#!/usr/bin/env python3
import os
# -----------------------------------------------------------------------------
# Jetson.GPIO が Systemd 下で model を見失う場合の対策
# -----------------------------------------------------------------------------
os.environ.setdefault("JETSON_MODEL_NAME", "JETSON_ORIN_NANO")

import subprocess
import time
from typing import Optional

import Adafruit_SSD1306
from PIL import Image, ImageDraw, ImageFont
import Jetson.GPIO as GPIO

# -----------------------------------------------------------------------------
# ヘルパ関数
# -----------------------------------------------------------------------------

def iface_state(name: str) -> str:
    """Return operstate text or 'absent'."""
    path = f"/sys/class/net/{name}/operstate"
    if not os.path.exists(path):
        return "absent"
    try:
        return open(path).read().strip()
    except IOError:
        return "down"


def get_ip(name: str) -> str:
    """IPv4 アドレスを返す。up 以外 / 取得失敗時は 'N/A'."""
    if iface_state(name) != "up":
        return "N/A"
    try:
        out = subprocess.check_output(
            f"ip -4 addr show {name} | grep -oP '(?<=inet\\s)\\d+(?:\\.\\d+){{3}}'",
            shell=True,
            stderr=subprocess.DEVNULL,
        )
        return (out.decode().strip() or "N/A")
    except subprocess.CalledProcessError:
        return "N/A"


def detect_bus() -> int:
    """Jetson model -> I2C バス番号"""
    board = GPIO.gpio_pin_data.get_data()[0]
    return {"JETSON_ORIN_NANO": 7, "JETSON_NANO": 7, "JETSON_XAVIER": 8, "JETSON_NX": 8}.get(board, 1)


def find_iface(prefixes) -> Optional[str]:
    """/sys/class/net を走査して最初に一致した dev 名を返す"""
    for dev in os.listdir("/sys/class/net"):
        if any(dev.startswith(p) for p in prefixes):
            return dev
    return None

# -----------------------------------------------------------------------------
# メインループ
# -----------------------------------------------------------------------------

def main():
    disp = Adafruit_SSD1306.SSD1306_128_32(rst=None, i2c_bus=detect_bus(), gpio=1)
    disp.begin()
    disp.clear()
    disp.display()

    width, height = disp.width, disp.height
    image = Image.new("1", (width, height))
    draw = ImageDraw.Draw(image)
    font = ImageFont.load_default()

    while True:
        draw.rectangle((0, 0, width, height), outline=0, fill=0)

        usb_if  = find_iface(["l4tbr0", "usb"])
        eth_if  = find_iface(["eth", "en", "eno"])
        wifi_if = find_iface(["wl", "wlan"])

        draw.text((0, 0), f"wifi: {get_ip(wifi_if) if wifi_if else 'N/A'}", font=font, fill=255)
        draw.text((0, 8), f"eth:  {get_ip(eth_if)  if eth_if  else 'N/A'}", font=font, fill=255)
        draw.text((0,16), f"usb:  {get_ip(usb_if) if usb_if else 'N/A'}", font=font, fill=255)

        disp.image(image)
        disp.display()
        time.sleep(1)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        pass
