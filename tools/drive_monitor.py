#!/usr/bin/env python3
"""走行中モニタ(JetPack 7.2): CSIエラーと電源・温度を同時に記録する

カメラには触らないので、11_record_camera / 17_run で走行させながら別ターミナルで
動かせる。走行後にCtrl-Cで止めると、CSIエラーが出た瞬間の電源電圧・電流を
平常時と比較して表示する(電圧低下・大電流ノイズが原因かの切り分け用)。

使い方:
    python ~/jetracer/tools/drive_monitor.py          # Ctrl-Cで終了
    python ~/jetracer/tools/drive_monitor.py --duration 300
記録: ~/jetracer/logs/drive_YYYYmmdd_HHMMSS.csv (+ _events.txt)
"""

import argparse
import csv
import glob
import os
import signal
import subprocess
import threading
import time

ERROR_KEYS = ('PD_CRC_ERR', 'PH_ECC', 'PH_CRC', 'Error 15 Received', 'Sending critical error')
WINDOW = 0.5  # エラー時刻の前後この秒数を「エラー時」とみなす


def find_power_channels():
    """INA3221の (ラベル, 電圧ファイル, 電流ファイル) を返す"""
    channels = []
    for hwmon in sorted(glob.glob('/sys/bus/i2c/drivers/ina3221/*/hwmon/hwmon*')):
        for i in (1, 2, 3):
            label_file = os.path.join(hwmon, 'in%d_label' % i)
            if os.path.exists(label_file):
                label = open(label_file).read().strip()
                channels.append((label, os.path.join(hwmon, 'in%d_input' % i),
                                 os.path.join(hwmon, 'curr%d_input' % i)))
    return channels


def find_temp_zones():
    zones = []
    for zone in sorted(glob.glob('/sys/class/thermal/thermal_zone*')):
        try:
            name = open(os.path.join(zone, 'type')).read().strip()
        except OSError:
            continue
        if name in ('cpu-thermal', 'gpu-thermal', 'tj-thermal', 'soc0-thermal'):
            zones.append((name, os.path.join(zone, 'temp')))
    return zones


def read_int(path):
    try:
        with open(path) as f:
            return int(f.read().strip())
    except (OSError, ValueError):
        return None


class JournalWatcher(object):
    def __init__(self, events_file):
        self.events = []  # (unix時刻, 内容)
        self._events_file = events_file
        self._proc = subprocess.Popen(
            ['journalctl', '-u', 'nvargus-daemon', '-f', '-n', '0', '-o', 'cat'],
            stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, text=True)
        threading.Thread(target=self._run, daemon=True).start()

    def _run(self):
        for line in self._proc.stdout:
            key = next((k for k in ERROR_KEYS if k in line), None)
            if key:
                now = time.time()
                self.events.append((now, key))
                with open(self._events_file, 'a') as f:
                    f.write('%s\t%s\t%s\n' % (time.strftime('%H:%M:%S', time.localtime(now)), key, line.strip()))
                print('  !! %s CSIエラー検出: %s' % (time.strftime('%H:%M:%S'), key), flush=True)

    def stop(self):
        self._proc.terminate()


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('--duration', type=float, default=0, help='記録秒数(0=Ctrl-Cまで)')
    parser.add_argument('--interval', type=float, default=0.02, help='電源サンプリング間隔[秒]')
    args = parser.parse_args()

    log_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'logs')
    os.makedirs(log_dir, exist_ok=True)
    stamp = time.strftime('%Y%m%d_%H%M%S')
    csv_path = os.path.join(log_dir, 'drive_%s.csv' % stamp)
    events_path = os.path.join(log_dir, 'drive_%s_events.txt' % stamp)

    power = find_power_channels()
    temps = find_temp_zones()
    if not power:
        print('WARNING: INA3221電源モニタが見つかりません(電圧は記録されません)')
    print('記録先:', os.path.abspath(csv_path))
    print('電源:', ', '.join(p[0] for p in power) or 'なし', '/ 温度:', ', '.join(t[0] for t in temps) or 'なし')
    print('走行を開始してください。終了はCtrl-C\n')

    watcher = JournalWatcher(events_path)
    stop = {'flag': False}
    signal.signal(signal.SIGINT, lambda *_: stop.__setitem__('flag', True))
    signal.signal(signal.SIGTERM, lambda *_: stop.__setitem__('flag', True))

    samples = []  # (t, {label: (mV, mA)})
    t_start = time.time()
    next_temp = 0
    temp_values = {}
    next_status = t_start + 10
    with open(csv_path, 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(['time', 'elapsed_s'] + ['%s_mV' % p[0] for p in power] + ['%s_mA' % p[0] for p in power]
                        + ['%s_mC' % t[0] for t in temps])
        while not stop['flag'] and (args.duration <= 0 or time.time() - t_start < args.duration):
            now = time.time()
            volts = [read_int(p[1]) for p in power]
            amps = [read_int(p[2]) for p in power]
            if now >= next_temp:
                temp_values = {t[0]: read_int(t[1]) for t in temps}
                next_temp = now + 1.0
            writer.writerow(['%.3f' % now, '%.3f' % (now - t_start)] + volts + amps
                            + [temp_values.get(t[0]) for t in temps])
            samples.append((now, volts, amps))
            if now >= next_status:
                v_in = [s[1][0] for s in samples[-500:] if s[1] and s[1][0]]
                print('  %4.0fs  VDD_IN最小=%smV  CSIエラー累計=%d' % (
                    now - t_start, min(v_in) if v_in else '-', len(watcher.events)), flush=True)
                next_status += 10
            time.sleep(args.interval)
    watcher.stop()

    # ---- 集計: エラー時刻の前後WINDOW秒と、それ以外を比較 ----
    print('\n' + '=' * 64)
    print('記録時間 %.0f秒 / CSIエラー %d件' % (time.time() - t_start, len(watcher.events)))
    if power and samples:
        err_times = [e[0] for e in watcher.events]
        for idx, (label, _, _) in enumerate(power):
            is_near = [any(abs(s[0] - t) <= WINDOW for t in err_times) for s in samples]
            near = [s for s, n in zip(samples, is_near) if n]
            far = [s for s, n in zip(samples, is_near) if not n]

            def stats(rows):
                v = [r[1][idx] for r in rows if r[1][idx] is not None]
                a = [r[2][idx] for r in rows if r[2][idx] is not None]
                if not v:
                    return '-'
                return '電圧 最小%5dmV 平均%5dmV / 電流 最大%5dmA 平均%5dmA' % (
                    min(v), sum(v) // len(v), max(a) if a else 0, sum(a) // len(a) if a else 0)
            print('[%s]' % label)
            print('  平常時  : %s' % stats(far))
            if err_times:
                print('  エラー時: %s' % stats(near))
    print('\nCSV: %s' % os.path.abspath(csv_path))
    if watcher.events:
        print('エラー詳細: %s' % os.path.abspath(events_path))


if __name__ == '__main__':
    main()
