#!/usr/bin/env python3
"""CSIカメラ リンク品質テスト(JetPack 7.2 / IMX219)

カメラをストリーミングしながら、CSIのエラーとフレームの途切れを計測する。

使い方(JupyterLabのターミナル等で、カメラを使うノートブックを全て停止してから):
    python ~/jetracer/tools/csi_link_test.py --drive 120   # 実走行テスト(推奨)
    python ~/jetracer/tools/csi_link_test.py               # 台上3フェーズ(静止/振動/モーター)
    python ~/jetracer/tools/csi_link_test.py --backend argus --drive 120   # 従来方式で比較

--drive: プロポで普段どおり走らせ、壁に軽くぶつける・段差を越えるなど衝撃を与える。
         V4L2方式では壊れたフレームを1枚捨てて続行するので、「最大フレーム間隔」が
         70ms以下(=欠けても1フレーム)なら30fpsの制御周期を守れている。
"""

import argparse
import os
import subprocess
import sys
import threading
import time

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'notebooks'))

BENCH_PHASES = [
    ('静止', '何もしないでください(基準値の測定)'),
    ('振動', 'モーターOFFのまま、カメラケーブル・両端のコネクタ・カメラ基板を指で軽く叩く/揺すってください'),
    ('モーター', '車輪を浮かせてモーターを回してください(ケーブルには触れない)'),
]
ERROR_KEYS = ('PD_CRC_ERR', 'PH_ECC', 'PH_CRC', 'corr_err', 'uncorr_err', 'discarding frame')


class JournalWatcher(object):
    """カーネルとnvargus-daemonのログを追跡し、CSIエラー件数を数える"""

    def __init__(self):
        self.count = 0
        self._proc = subprocess.Popen(
            ['journalctl', '-f', '-n', '0', '-o', 'cat',
             '_TRANSPORT=kernel', '+', '_SYSTEMD_UNIT=nvargus-daemon.service'],
            stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, text=True)
        threading.Thread(target=self._run, daemon=True).start()

    def _run(self):
        for line in self._proc.stdout:
            if any(k in line for k in ERROR_KEYS):
                self.count += 1

    def stop(self):
        self._proc.terminate()


def open_camera(backend, fps):
    if backend == 'v4l2':
        from v4l2_camera import V4L2Camera
        return V4L2Camera(width=224, height=224, capture_fps=fps)
    from csi_camera import CSICamera
    return CSICamera(width=224, height=224, capture_fps=fps)


def measure(camera, backend, fps, seconds, watcher):
    """seconds秒ストリーミングし (camera, 結果dict) を返す"""
    err_start = watcher.count
    drop_start = camera.stats['dropped'] if backend == 'v4l2' else 0
    restart_start = camera.stats['restarts'] if backend == 'v4l2' else 0
    frames = reopens = 0
    max_gap = 0.0
    t_start = last = time.monotonic()
    next_report = t_start + 5
    while time.monotonic() - t_start < seconds:
        try:
            camera.read()
            frames += 1
            now = time.monotonic()
            max_gap = max(max_gap, now - last)
            last = now
        except Exception as e:
            reopens += 1
            print('  !! カメラ停止を検知: %s → 開き直します' % e, flush=True)
            camera.release()
            camera = open_camera(backend, fps)
            drop_start = camera.stats['dropped'] if backend == 'v4l2' else 0
            restart_start = camera.stats['restarts'] if backend == 'v4l2' else 0
        if time.monotonic() >= next_report:
            dropped = camera.stats['dropped'] - drop_start if backend == 'v4l2' else '-'
            print('  %4.0fs  frames=%5d  CSIエラー=%3d  捨てたフレーム=%s  開き直し=%d  最大間隔=%.0fms' % (
                time.monotonic() - t_start, frames, watcher.count - err_start, dropped, reopens, max_gap * 1000),
                flush=True)
            next_report += 5
    time.sleep(0.5)  # 末尾のログ取り込み待ち
    return camera, {
        'frames': frames, 'errors': watcher.count - err_start, 'reopens': reopens, 'max_gap': max_gap,
        'dropped': camera.stats['dropped'] - drop_start if backend == 'v4l2' else None,
        'restarts': camera.stats['restarts'] - restart_start if backend == 'v4l2' else None,
    }


def countdown(seconds=5):
    for i in range(seconds, 0, -1):
        print('  %d秒後に計測開始...' % i, end='\r', flush=True)
        time.sleep(1)
    print(' ' * 30, end='\r')


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('--backend', choices=('v4l2', 'argus'), default='v4l2', help='カメラの取得方式')
    parser.add_argument('--drive', type=int, default=0, metavar='秒', help='実走行テストの秒数(0=台上3フェーズ)')
    parser.add_argument('--phase', type=int, default=45, help='台上テストの各フェーズの秒数')
    parser.add_argument('--fps', type=int, default=30, help='カメラFPS(録画/走行ノートブックと同じ30を推奨)')
    args = parser.parse_args()

    watcher = JournalWatcher()
    time.sleep(1.0)
    camera = open_camera(args.backend, args.fps)
    print('カメラ方式: %s' % args.backend)
    phases = [('走行', 'プロポで走らせ、壁に軽くぶつける・段差を越えるなど衝撃を与えてください')] \
        if args.drive > 0 else BENCH_PHASES
    seconds = args.drive if args.drive > 0 else args.phase
    results = []
    try:
        for name, instruction in phases:
            print('\n' + '=' * 72)
            print('【%s】%s' % (name, instruction))
            countdown()
            camera, r = measure(camera, args.backend, args.fps, seconds, watcher)
            results.append((name, r))
            print('  → %s: CSIエラー %d件 / 開き直し %d回 / 最大フレーム間隔 %.0fms' % (
                name, r['errors'], r['reopens'], r['max_gap'] * 1000))
    finally:
        camera.release()
        watcher.stop()

    print('\n' + '=' * 72)
    for name, r in results:
        extra = '' if r['dropped'] is None else '  捨てたフレーム=%d  ストリーム再起動=%d' % (r['dropped'], r['restarts'])
        print('%s: フレーム=%d  CSIエラー=%d  開き直し=%d  最大間隔=%.0fms%s' % (
            name, r['frames'], r['errors'], r['reopens'], r['max_gap'] * 1000, extra))
    print('\n判定:')
    worst_gap = max(r['max_gap'] for _, r in results) * 1000
    total_errors = sum(r['errors'] for _, r in results)
    if total_errors == 0:
        print('  CSIエラーは発生しませんでした(衝撃が足りない可能性があります)')
    elif worst_gap <= 70:
        print('  CSIエラー%d件が発生しましたが、最大フレーム間隔%.0fms(欠けても1フレーム)で' % (total_errors, worst_gap))
        print('  30fpsの制御周期を守れています。')
    else:
        print('  CSIエラー%d件で、最大%.0fmsフレームが途切れました。' % (total_errors, worst_gap))
        print('  カメラ・ケーブルの固定(衝撃対策)を見直してください。')


if __name__ == '__main__':
    main()
