#!/usr/bin/env python3
"""
Jetson Orin Nano / JetPack 6.2 — OLED ネットワークモニタ
========================================================
128×32 SSD1306 OLED に 1 秒毎に次を表示します：
  • USB ガジェット (l4tbr0, usb*) の IP
  • 有線 NIC (eth*, en*, eno*) の IP
  • Wi‑Fi (wl*, wlan*) の IP

ラベル **wifi / eth / usb** は常に表示され、IP が取得できない場合は "N/A" を表示します。

依存ライブラリ
---------------
  sudo apt update && sudo apt install -y python3-pip i2c-tools
  pip3 install adafruit-circuitpython-ssd1306 Pillow Jetson.GPIO

実行
----
  sudo python3 oled_stats_jetpack62.py
"""
from __future__ import annotations

import os
import subprocess
import time
from typing import Iterable, List

import Adafruit_SSD1306
import Jetson.GPIO as GPIO
from PIL import Image, ImageDraw, ImageFont

# -----------------------------------------------------------------------------
# ネットワークユーティリティ
# -----------------------------------------------------------------------------

def iface_state(name: str) -> str:
    """Return operstate ('up', 'down', 'unknown', or 'absent')."""
    path = f"/sys/class/net/{name}/operstate"
    if not os.path.exists(path):
        return "absent"
    try:
        return open(path).read().strip()
    except IOError:
        return "down"


def ip_of(name: str) -> str:
    """IPv4 アドレスを返す。IF が up で IP 有ならそれを、無ければ 'N/A'。"""
    if iface_state(name) != "up":
        return "N/A"
    try:
        out = subprocess.check_output(
            f"ip -4 addr show {name} | grep -oP '(?<=inet\\s)\\d+(?:\\.\\d+){{3}}'",
            shell=True,
            stderr=subprocess.DEVNULL,
        )
        ip = out.decode().strip()
        return ip if ip else "N/A"
    except subprocess.CalledProcessError:
        return "N/A"


# -----------------------------------------------------------------------------
# インタフェース候補生成
# -----------------------------------------------------------------------------

USB_PREFIXES = ("l4tbr", "usb")        # USB gadget / Ethernet
ETH_PREFIXES = ("en", "eth", "eno")     # 有線 NIC
WIFI_PREFIXES = ("wl", "wlan")          # Wi‑Fi


def scan_ifaces(prefixes: Iterable[str]) -> List[str]:
    """Return list of interface names starting with any of prefixes."""
    try:
        return [n for n in os.listdir("/sys/class/net") if any(n.startswith(p) for p in prefixes)]
    except FileNotFoundError:
        return []


def first_ip(prefixes: Iterable[str]) -> str:
    """Return first non‑N/A IP among interfaces matching prefixes, else 'N/A'."""
    for iface in scan_ifaces(prefixes):
        ip = ip_of(iface)
        if ip != "N/A":
            return ip
    return "N/A"


# -----------------------------------------------------------------------------
# OLED / GPIO
# -----------------------------------------------------------------------------

def detect_i2c_bus() -> int:
    board = GPIO.gpio_pin_data.get_data()[0]
    if board in ("JETSON_ORIN_NANO", "JETSON_NANO"):
        return 7  # I2C1 on 40‑pin header
    if board in ("JETSON_XAVIER", "JETSON_NX"):
        return 8
    return 1  # fallback


# -----------------------------------------------------------------------------
# メインループ
# -----------------------------------------------------------------------------

def main() -> None:
    disp = Adafruit_SSD1306.SSD1306_128_32(rst=None, i2c_bus=detect_i2c_bus(), gpio=1)
    disp.begin()
    disp.clear()
    disp.display()

    width, height = disp.width, disp.height
    image = Image.new("1", (width, height))
    draw = ImageDraw.Draw(image)
    font = ImageFont.load_default()

    while True:
        # IP アドレスを取得 (毎秒更新)
        usb_ip  = first_ip(USB_PREFIXES)
        eth_ip  = first_ip(ETH_PREFIXES)
        wifi_ip = first_ip(WIFI_PREFIXES)

        # 画面クリア
        draw.rectangle((0, 0, width, height), outline=0, fill=0)

        # ラベルは常に表示
        draw.text((0, 0),  f"wifi:{wifi_ip}", font=font, fill=255)
        draw.text((0, 8),  f"eth: {eth_ip}",  font=font, fill=255)
        draw.text((0, 16), f"usb: {usb_ip}",  font=font, fill=255)

        disp.image(image)
        disp.display()
        time.sleep(1)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        pass
