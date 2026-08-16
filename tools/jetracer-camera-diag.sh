#!/bin/bash
# JetRacer JP7.2: カメラ関連のクロック/GPIO状態を読み取り専用でダンプ
echo "=== clk (extperiph/cam) ==="
grep -iE "extperiph|cam" /sys/kernel/debug/clk/clk_summary 2>/dev/null
echo "=== gpio (cam) ==="
grep -iE "cam" /sys/kernel/debug/gpio 2>/dev/null
echo "=== regulator summary (cam lines) ==="
grep -iE "cam|avdd|dvdd|iovdd" /sys/kernel/debug/regulator/regulator_summary 2>/dev/null
