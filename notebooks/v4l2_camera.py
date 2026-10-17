"""V4L2直接キャプチャによるCSIカメラ(JetPack 7.2 / IMX219)

Argus(nvarguscamerasrc)は、走行中の衝突・振動でCSIにCRCエラーが1回出るだけで
キャプチャセッションを止めてしまい、30fpsの制御周期を守れない(NVIDIAの既知の制約)。
本クラスはArgusを使わずV4L2で直接RAW画像を受け取り、エラーフラグ付きの壊れた
フレームは1枚だけ捨てて続行する(JetPack 6系でのArgusの振る舞いに相当)。

RAW(RG10)→BGRの変換(簡易ISP: デモザイク・黒レベル・ホワイトバランス・ガンマ・
自動露出)を自前で行うため、Argus経由の画像とは色味が異なる。学習データの録画と
走行(推論)は必ず同じカメラクラスで行うこと。

使い方は CSICamera と同じ:
    from v4l2_camera import V4L2Camera
    camera = V4L2Camera(width=224, height=224)
    image = camera.read()          # BGR uint8 (224, 224, 3)
    camera.cap.release()           # または camera.release()
"""

import ctypes
import errno
import fcntl
import mmap
import os
import select
import threading
import time

import cv2
import numpy as np
import traitlets
from jetcam.camera import Camera

# ---------------------------------------------------------------- V4L2 ABI (aarch64)
_IOC_WRITE, _IOC_READ = 1, 2


def _IOC(direction, nr, size):
    return (direction << 30) | (size << 16) | (ord('V') << 8) | nr


class _v4l2_pix_format(ctypes.Structure):
    _fields_ = [('width', ctypes.c_uint32), ('height', ctypes.c_uint32),
                ('pixelformat', ctypes.c_uint32), ('field', ctypes.c_uint32),
                ('bytesperline', ctypes.c_uint32), ('sizeimage', ctypes.c_uint32),
                ('colorspace', ctypes.c_uint32), ('priv', ctypes.c_uint32),
                ('flags', ctypes.c_uint32), ('ycbcr_enc', ctypes.c_uint32),
                ('quantization', ctypes.c_uint32), ('xfer_func', ctypes.c_uint32)]


class _v4l2_format_union(ctypes.Union):
    _fields_ = [('pix', _v4l2_pix_format), ('raw_data', ctypes.c_uint8 * 200),
                ('_align', ctypes.c_void_p)]


class _v4l2_format(ctypes.Structure):
    _fields_ = [('type', ctypes.c_uint32), ('fmt', _v4l2_format_union)]


class _v4l2_requestbuffers(ctypes.Structure):
    _fields_ = [('count', ctypes.c_uint32), ('type', ctypes.c_uint32),
                ('memory', ctypes.c_uint32), ('capabilities', ctypes.c_uint32),
                ('flags', ctypes.c_uint8), ('reserved', ctypes.c_uint8 * 3)]


class _timeval(ctypes.Structure):
    _fields_ = [('tv_sec', ctypes.c_long), ('tv_usec', ctypes.c_long)]


class _v4l2_timecode(ctypes.Structure):
    _fields_ = [('type', ctypes.c_uint32), ('flags', ctypes.c_uint32),
                ('frames', ctypes.c_uint8), ('seconds', ctypes.c_uint8),
                ('minutes', ctypes.c_uint8), ('hours', ctypes.c_uint8),
                ('userbits', ctypes.c_uint8 * 4)]


class _v4l2_buffer_m(ctypes.Union):
    _fields_ = [('offset', ctypes.c_uint32), ('userptr', ctypes.c_ulong),
                ('planes', ctypes.c_void_p), ('fd', ctypes.c_int32)]


class _v4l2_buffer(ctypes.Structure):
    _fields_ = [('index', ctypes.c_uint32), ('type', ctypes.c_uint32),
                ('bytesused', ctypes.c_uint32), ('flags', ctypes.c_uint32),
                ('field', ctypes.c_uint32), ('timestamp', _timeval),
                ('timecode', _v4l2_timecode), ('sequence', ctypes.c_uint32),
                ('memory', ctypes.c_uint32), ('m', _v4l2_buffer_m),
                ('length', ctypes.c_uint32), ('reserved2', ctypes.c_uint32),
                ('request_fd', ctypes.c_int32)]


class _v4l2_ext_control(ctypes.Structure):
    _pack_ = 1
    _fields_ = [('id', ctypes.c_uint32), ('size', ctypes.c_uint32),
                ('reserved2', ctypes.c_uint32), ('value64', ctypes.c_int64)]


class _v4l2_ext_controls(ctypes.Structure):
    _fields_ = [('which', ctypes.c_uint32), ('count', ctypes.c_uint32),
                ('error_idx', ctypes.c_uint32), ('request_fd', ctypes.c_int32),
                ('reserved', ctypes.c_uint32), ('controls', ctypes.POINTER(_v4l2_ext_control))]


assert ctypes.sizeof(_v4l2_format) == 208 and ctypes.sizeof(_v4l2_buffer) == 88
assert ctypes.sizeof(_v4l2_ext_control) == 20 and ctypes.sizeof(_v4l2_ext_controls) == 32

_VIDIOC_S_FMT = _IOC(_IOC_READ | _IOC_WRITE, 5, ctypes.sizeof(_v4l2_format))
_VIDIOC_REQBUFS = _IOC(_IOC_READ | _IOC_WRITE, 8, ctypes.sizeof(_v4l2_requestbuffers))
_VIDIOC_QUERYBUF = _IOC(_IOC_READ | _IOC_WRITE, 9, ctypes.sizeof(_v4l2_buffer))
_VIDIOC_QBUF = _IOC(_IOC_READ | _IOC_WRITE, 15, ctypes.sizeof(_v4l2_buffer))
_VIDIOC_DQBUF = _IOC(_IOC_READ | _IOC_WRITE, 17, ctypes.sizeof(_v4l2_buffer))
_VIDIOC_STREAMON = _IOC(_IOC_WRITE, 18, ctypes.sizeof(ctypes.c_int))
_VIDIOC_STREAMOFF = _IOC(_IOC_WRITE, 19, ctypes.sizeof(ctypes.c_int))
_VIDIOC_S_EXT_CTRLS = _IOC(_IOC_READ | _IOC_WRITE, 72, ctypes.sizeof(_v4l2_ext_controls))

_BUF_TYPE_VIDEO_CAPTURE = 1
_MEMORY_MMAP = 1
_BUF_FLAG_ERROR = 0x40
_FIELD_NONE = 1
_PIX_FMT_RG10 = ord('R') | (ord('G') << 8) | (ord('1') << 16) | (ord('0') << 24)

# tegracam (nv_imx219) のカメラコントロール
_CID_SENSOR_MODE = 0x009a2008
_CID_GAIN = 0x009a2009
_CID_EXPOSURE = 0x009a200a
_CID_FRAME_RATE = 0x009a200b
_CID_BYPASS_MODE = 0x009a2064
_CID_LOW_LATENCY = 0x009a206d

# IMX219 センサーモード(nvarguscamerasrcの番号と同じ)。2 = 1920x1080@30 (録画・走行の既定)
SENSOR_MODES = {2: (1920, 1080, 30), 3: (1640, 1232, 30), 4: (1280, 720, 60)}

GAIN_MIN, GAIN_MAX = 16, 170            # 16 = 1.0倍
BLACK_LEVEL_10BIT = 64


class CameraTimeoutError(RuntimeError):
    """一定時間フレームが届かない"""


class _CapHandle(object):
    """既存ノートブックの camera.cap.read() / camera.cap.release() 互換"""

    def __init__(self, camera):
        self._camera = camera

    def read(self):
        try:
            return True, self._camera.read()
        except RuntimeError:
            return False, None

    def release(self):
        self._camera.release()

    def isOpened(self):
        return not self._camera.released


class V4L2Camera(Camera):

    capture_device = traitlets.Integer(default_value=0)
    capture_fps = traitlets.Integer(default_value=30)
    sensor_mode = traitlets.Integer(default_value=2)
    # read()がこの秒数フレームを受け取れなければCameraTimeoutError
    read_timeout = traitlets.Float(default_value=0.5)
    # 自動露出: 目標の明るさ(ガンマ後の平均輝度 0-255)。auto_exposure=Falseなら固定値を使う
    auto_exposure = traitlets.Bool(default_value=True)
    target_brightness = traitlets.Float(default_value=110.0)
    exposure_us = traitlets.Integer(default_value=15000)
    gain = traitlets.Integer(default_value=32)
    # ホワイトバランス: None=自動(グレーワールド)、(r, b) 指定で固定
    wb_gains = traitlets.Any(default_value=None, allow_none=True)
    gamma = traitlets.Float(default_value=2.2)

    def __init__(self, *args, **kwargs):
        super(V4L2Camera, self).__init__(*args, **kwargs)
        if self.sensor_mode not in SENSOR_MODES:
            raise ValueError('sensor_mode は %s のいずれか' % sorted(SENSOR_MODES))
        self.sensor_w, self.sensor_h, max_fps = SENSOR_MODES[self.sensor_mode]
        self.capture_fps = min(self.capture_fps, max_fps)
        self.released = False
        self.stats = {'frames': 0, 'dropped': 0, 'restarts': 0, 'max_gap_ms': 0.0}
        self._cond = threading.Condition()
        self._frame = None
        self._seq = 0
        self._returned_seq = 0
        self._stop = False
        self._fatal = None
        self._fd = -1
        self._buffers = []
        self._streaming = False
        self._wb = np.array(self.wb_gains if self.wb_gains else (1.5, 1.5), dtype=np.float32)
        self._exposure = int(self.exposure_us)
        self._gain = int(self.gain)
        self._max_exposure = int(1e6 / self.capture_fps) - 1000
        self._lut = self._make_lut()
        try:
            self._open()
            self._thread = threading.Thread(target=self._reader, daemon=True)
            self._thread.start()
            self.read(timeout=5.0)
        except Exception as e:
            self.release()
            raise RuntimeError('Could not initialize camera (V4L2): %s' % e)
        self.cap = _CapHandle(self)

    # ------------------------------------------------------------ V4L2 setup
    def _ioctl(self, request, arg):
        fcntl.ioctl(self._fd, request, arg)

    def _set_controls(self, values):
        ctrls = (_v4l2_ext_control * len(values))()
        for i, (cid, value) in enumerate(values):
            ctrls[i].id = cid
            ctrls[i].value64 = int(value)
        req = _v4l2_ext_controls(which=0, count=len(values), controls=ctrls)
        self._ioctl(_VIDIOC_S_EXT_CTRLS, req)

    def _open(self):
        self._fd = os.open('/dev/video%d' % self.capture_device, os.O_RDWR | os.O_NONBLOCK)
        fmt = _v4l2_format()
        fmt.type = _BUF_TYPE_VIDEO_CAPTURE
        fmt.fmt.pix.width = self.sensor_w
        fmt.fmt.pix.height = self.sensor_h
        fmt.fmt.pix.pixelformat = _PIX_FMT_RG10
        fmt.fmt.pix.field = _FIELD_NONE
        self._ioctl(_VIDIOC_S_FMT, fmt)
        self._bytesperline = fmt.fmt.pix.bytesperline or self.sensor_w * 2
        self._set_controls([(_CID_BYPASS_MODE, 0), (_CID_SENSOR_MODE, self.sensor_mode)])
        self._set_controls([(_CID_FRAME_RATE, self.capture_fps * 1000000),
                            (_CID_EXPOSURE, self._exposure), (_CID_GAIN, self._gain)])

        req = _v4l2_requestbuffers(count=4, type=_BUF_TYPE_VIDEO_CAPTURE, memory=_MEMORY_MMAP)
        self._ioctl(_VIDIOC_REQBUFS, req)
        for i in range(req.count):
            buf = _v4l2_buffer(index=i, type=_BUF_TYPE_VIDEO_CAPTURE, memory=_MEMORY_MMAP)
            self._ioctl(_VIDIOC_QUERYBUF, buf)
            self._buffers.append(mmap.mmap(self._fd, buf.length, mmap.MAP_SHARED,
                                           mmap.PROT_READ | mmap.PROT_WRITE, offset=buf.m.offset))
        self._start_stream()

    def _start_stream(self):
        for i in range(len(self._buffers)):
            self._ioctl(_VIDIOC_QBUF, _v4l2_buffer(index=i, type=_BUF_TYPE_VIDEO_CAPTURE, memory=_MEMORY_MMAP))
        self._ioctl(_VIDIOC_STREAMON, ctypes.c_int(_BUF_TYPE_VIDEO_CAPTURE))
        self._streaming = True

    def _stop_stream(self):
        if self._streaming:
            try:
                self._ioctl(_VIDIOC_STREAMOFF, ctypes.c_int(_BUF_TYPE_VIDEO_CAPTURE))
            except OSError:
                pass
            self._streaming = False

    def _restart_stream(self):
        """ドライバ側でストリームが止まった場合の再起動(Argus不要・数百ms)"""
        self.stats['restarts'] += 1
        self._stop_stream()
        self._start_stream()

    # ------------------------------------------------------------ capture thread
    def _reader(self):
        last_frame = time.monotonic()
        try:
            while not self._stop:
                ready, _, _ = select.select([self._fd], [], [], 0.1)
                now = time.monotonic()
                if not ready:
                    # 0.5秒以上まったくフレームが来ない → ストリームを張り直す
                    if now - last_frame > 0.5:
                        self._restart_stream()
                        last_frame = now
                    continue
                buf = _v4l2_buffer(type=_BUF_TYPE_VIDEO_CAPTURE, memory=_MEMORY_MMAP)
                try:
                    self._ioctl(_VIDIOC_DQBUF, buf)
                except OSError as e:
                    if e.errno == errno.EAGAIN:
                        continue
                    if e.errno == errno.EIO:  # ドライバがチャネルのエラー回復中
                        self.stats['dropped'] += 1
                        continue
                    raise
                try:
                    if buf.flags & _BUF_FLAG_ERROR:
                        # CRCエラー等で壊れたフレーム: 1枚だけ捨てて続行する
                        self.stats['dropped'] += 1
                        continue
                    raw = np.frombuffer(self._buffers[buf.index], dtype='<u2',
                                        count=self.sensor_h * self._bytesperline // 2)
                    raw = raw.reshape(self.sensor_h, self._bytesperline // 2)[:, :self.sensor_w]
                    image = self._process(raw)
                finally:
                    self._ioctl(_VIDIOC_QBUF, buf)
                gap = (now - last_frame) * 1000
                last_frame = now
                with self._cond:
                    self._frame = image
                    self._seq += 1
                    self.stats['frames'] += 1
                    if self.stats['frames'] > 1:
                        self.stats['max_gap_ms'] = max(self.stats['max_gap_ms'], gap)
                    self._cond.notify_all()
        except Exception as e:
            with self._cond:
                self._fatal = e
                self._cond.notify_all()

    # ------------------------------------------------------------ simple ISP
    def _make_lut(self):
        # 16bitフルスケール入力 → ガンマ補正済み8bit
        x = np.arange(65536, dtype=np.float32) / 65535.0
        return np.clip(255.0 * np.power(x, 1.0 / self.gamma) + 0.5, 0, 255).astype(np.uint8)

    def _process(self, raw):
        # RG10は10bitを[15:6]に左詰め(下位6bitは上位のコピー)。RGGB配列。
        # V4L2のバッファはキャッシュの効かないDMAメモリで、飛び飛びに読むと非常に遅い
        # (1色8ms)。1行おきのBayer行ペアだけを連続コピーしてから処理する。
        rows = np.ascontiguousarray(raw.reshape(self.sensor_h // 2, 2, self.sensor_w)[::2])
        q = rows.reshape(rows.shape[0], 2, self.sensor_w // 2, 2)
        g = (q[:, 0, :, 1] >> 1) + (q[:, 1, :, 0] >> 1)
        bgr = np.dstack((q[:, 1, :, 1], g, q[:, 0, :, 0]))
        # 横1/4は整数倍のエリア縮小(OpenCVの高速経路)、残りは線形補間で出力サイズへ
        bgr = cv2.resize(bgr, (self.sensor_w // 8, rows.shape[0]), interpolation=cv2.INTER_AREA)
        bgr = cv2.resize(bgr, (self.width, self.height), interpolation=cv2.INTER_LINEAR)
        black = BLACK_LEVEL_10BIT << 6
        bgr = cv2.subtract(bgr, (black, black, black, 0))

        if self.wb_gains is None:
            # グレーワールド法(ゆっくり追従させてチラつきを防ぐ)
            mean_b, mean_g, mean_r = cv2.mean(bgr)[:3]
            target = np.clip([mean_g / (mean_r + 1.0), mean_g / (mean_b + 1.0)], 0.5, 4.0)
            self._wb = 0.9 * self._wb + 0.1 * np.asarray(target, dtype=np.float32)  # (r, b)
            wb_r, wb_b = float(self._wb[0]), float(self._wb[1])
        else:
            wb_r, wb_b = self.wb_gains
        scale = 65535.0 / ((1023 - BLACK_LEVEL_10BIT) << 6)
        bgr = cv2.multiply(bgr, (wb_b * scale, scale, wb_r * scale, 0), dtype=cv2.CV_16U)
        bgr = self._lut[bgr]

        if self.auto_exposure:
            self._update_exposure(cv2.mean(bgr)[1])
        return bgr

    def _update_exposure(self, brightness):
        # 比例制御: 露出時間を優先して上げ、上限に達したらゲインを上げる
        error = self.target_brightness / max(brightness, 1.0)
        if 0.9 < error < 1.1:
            return
        ratio = min(max(error ** 0.5, 0.7), 1.4)
        total = self._exposure * self._gain * ratio
        exposure = int(min(max(total / GAIN_MIN, 100), self._max_exposure))
        gain = int(min(max(total / exposure, GAIN_MIN), GAIN_MAX))
        if exposure != self._exposure or gain != self._gain:
            try:
                self._set_controls([(_CID_EXPOSURE, exposure), (_CID_GAIN, gain)])
                self._exposure, self._gain = exposure, gain
            except OSError:
                pass

    # ------------------------------------------------------------ public API
    def _read(self):
        return self.read()

    def read(self, timeout=None):
        """次の新しいフレーム(BGR uint8)を返す。timeout秒届かなければCameraTimeoutError"""
        if timeout is None:
            timeout = self.read_timeout
        deadline = time.monotonic() + timeout
        with self._cond:
            while self._seq == self._returned_seq:
                if self._fatal is not None:
                    raise RuntimeError('Could not read image from camera: %s' % self._fatal)
                if self.released:
                    raise RuntimeError('Camera is released')
                remaining = deadline - time.monotonic()
                if remaining <= 0:
                    raise CameraTimeoutError('カメラから%.1f秒間フレームが届きません' % timeout)
                self._cond.wait(remaining)
            self._returned_seq = self._seq
            self.value = self._frame
            return self._frame

    def release(self):
        if self.released:
            return True
        self._stop = True
        thread = getattr(self, '_thread', None)
        if thread is not None and thread.is_alive():
            thread.join(2.0)  # select()のタイムアウトが0.1秒なので必ず抜ける
        with self._cond:
            self.released = True
            self._cond.notify_all()
        self._stop_stream()
        for buf in self._buffers:
            try:
                buf.close()
            except Exception:
                pass
        self._buffers = []
        if self._fd >= 0:
            if self._buffers == []:
                try:
                    self._ioctl(_VIDIOC_REQBUFS, _v4l2_requestbuffers(
                        count=0, type=_BUF_TYPE_VIDEO_CAPTURE, memory=_MEMORY_MMAP))
                except OSError:
                    pass
            os.close(self._fd)
            self._fd = -1
        return True
