from jetcam.camera import Camera
import atexit
import ctypes
import cv2
import numpy as np
import subprocess
import threading
import time
import traitlets


# センサ再バインド+nvargus-daemon再起動(インストーラが配置・sudoers NOPASSWD登録済み)
REVIVE_COMMAND = ['sudo', '-n', '/usr/local/bin/jetracer-camera-revive']


class CameraTimeoutError(RuntimeError):
    """一定時間フレームが届かない(CSIストリームが無言で停止した)"""


# 解放できずに放棄したVideoCapture。参照を手放すとデストラクタがrelease()を呼び、
# argusデーモン再起動後だとセグメンテーション違反でプロセスごと落ちるため保持し続ける。
_abandoned_captures = []


def _argus_daemon_pid():
    try:
        out = subprocess.run(['systemctl', 'show', '-p', 'MainPID', '--value', 'nvargus-daemon'],
                             capture_output=True, text=True, timeout=5)
        return out.stdout.strip()
    except Exception:
        return None


def revive_camera(timeout=60):
    """カメラスタックを復旧する。成功時True。"""
    try:
        result = subprocess.run(REVIVE_COMMAND, timeout=timeout,
                                stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        return result.returncode == 0
    except Exception:
        return False


class _CapHandle(object):
    """後方互換用: 既存ノートブックの camera.cap.read() / camera.cap.release() を、
    リーダースレッドと競合しない CSICamera 側の実装へ委譲する。
    (OpenCVのVideoCaptureはスレッドセーフではないため、read中の別スレッドから
     release()を直接呼ぶとクラッシュやハングの原因になる)"""

    def __init__(self, camera):
        self._camera = camera

    def read(self):
        try:
            return True, self._camera._read()
        except RuntimeError:
            return False, None

    def release(self):
        self._camera.release()

    def isOpened(self):
        return not self._camera.released


class CSICamera(Camera):

    capture_device = traitlets.Integer(default_value=0)
    capture_fps = traitlets.Integer(default_value=30)
    capture_width = traitlets.Integer(default_value=640)
    capture_height = traitlets.Integer(default_value=480)
    # ウォッチドッグ: この秒数フレームが届かなければ CameraTimeoutError を送出する。
    # JP7.2ではCSIのCRCエラー(走行中の衝突・振動)が1回出るとArgusがストリームを
    # 止めてしまい、従来の cap.read() は例外も出さず永久に待ち続けていた。
    # 正常時のフレーム間隔は30fpsで最大40ms程度なので0.5秒で十分に判定できる。
    read_timeout = traitlets.Float(default_value=0.5)
    open_timeout = traitlets.Float(default_value=10.0)

    def __init__(self, *args, **kwargs):
        super(CSICamera, self).__init__(*args, **kwargs)
        self._cond = threading.Condition()
        self._frame = None
        self._seq = 0
        self._returned_seq = 0
        self._failed = False
        self._stop_reader = False
        self.released = False
        self._thread = None
        self._vc = None
        self._daemon_pid = _argus_daemon_pid()
        try:
            self._vc = cv2.VideoCapture(self._gst_str(), cv2.CAP_GSTREAMER)
            if not self._vc.isOpened():
                raise RuntimeError('Could not open camera pipeline.')

            # cap.read()は別スレッドで回し、本スレッドはタイムアウト付きで待つ
            self._thread = threading.Thread(target=self._reader, daemon=True)
            self._thread.start()
            self._read(timeout=self.open_timeout)
        except Exception:
            # 失敗した作りかけのパイプラインを残さない(JP7.2ではゴミが後続の取得を妨げる)
            try:
                self.release()
            except Exception:
                pass
            raise RuntimeError(
                'Could not initialize camera.  Please see error trace.')

        self.cap = _CapHandle(self)
        atexit.register(self.release)

    def _gst_str(self):
        return 'nvarguscamerasrc sensor-id=%d ! video/x-raw(memory:NVMM), width=%d, height=%d, format=(string)NV12, framerate=(fraction)%d/1 ! nvvidconv ! video/x-raw, width=(int)%d, height=(int)%d, format=(string)BGRx ! videoconvert ! appsink' % (
                self.capture_device, self.capture_width, self.capture_height, self.capture_fps, self.width, self.height)

    def _reader(self):
        while not self._stop_reader:
            ok, image = self._vc.read()
            with self._cond:
                if self._stop_reader:
                    break
                if not ok:
                    self._failed = True
                    self._cond.notify_all()
                    break
                self._frame = image
                self._seq += 1
                self._cond.notify_all()

    def _read(self, timeout=None):
        """次の新しいフレームを返す。timeout秒届かなければCameraTimeoutError。"""
        if timeout is None:
            timeout = self.read_timeout
        deadline = time.monotonic() + timeout
        with self._cond:
            while self._seq == self._returned_seq:
                if self._failed or self.released:
                    raise RuntimeError('Could not read image from camera')
                remaining = deadline - time.monotonic()
                if remaining <= 0:
                    raise CameraTimeoutError(
                        'カメラから%.1f秒間フレームが届きません(CSIストリーム停止)' % timeout)
                self._cond.wait(remaining)
            self._returned_seq = self._seq
            return self._frame

    def release(self, join_timeout=2.0):
        """パイプラインを解放する。ストリーム停止で固まっていても戻ってくる。"""
        if self.released:
            return True
        self._stop_reader = True
        thread = self._thread
        if thread is not None and thread.is_alive():
            thread.join(join_timeout)
        with self._cond:
            self.released = True
            self._cond.notify_all()
        if self._vc is None:
            return True
        if (thread is not None and thread.is_alive()) or _argus_daemon_pid() != self._daemon_pid:
            # 以下の場合はrelease()せずに放棄する(呼び出し側は開き直す/revive_camera()する):
            #  - リーダーがcap.read()の中で固まっている(並行してrelease()するとクラッシュの恐れ)
            #  - argusデーモンが再起動された(古いパイプラインをrelease()するとセグフォで落ちる)
            _abandoned_captures.append(self._vc)
            # Python終了時の後片付けでもデストラクタが走らないよう参照を1つ余分に持つ
            ctypes.pythonapi.Py_IncRef(ctypes.py_object(self._vc))
            self._vc = None
            return False
        self._vc.release()
        self._vc = None
        return True
