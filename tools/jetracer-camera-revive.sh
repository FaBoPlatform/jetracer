#!/bin/bash
# JetRacer JP7.2: IMX219センサの電源再投入(ドライバ再バインド)+ argusデーモン再起動
# JP7.2ではセッション終了後のセンサ電源再投入が失敗することがあり(I2C NACK)、
# 再バインドでプローブ時の電源シーケンスを再実行して復活させる。
set -e
echo 9-0010 > /sys/bus/i2c/drivers/imx219/unbind 2>/dev/null || true
sleep 0.5
echo 9-0010 > /sys/bus/i2c/drivers/imx219/bind
systemctl restart nvargus-daemon
