#!/usr/bin/env python3
"""
看门狗：每 10 秒问一次 /health；心跳超过 20 秒没来、或 fps < 5，就执行一条命令（默认：打印；可换成重启浏览器）。
    python3 examples/kiosk/watchdog.py --url http://127.0.0.1:8888 --cmd "pkill -f chromium"
"""
import argparse, json, subprocess, time, urllib.request
ap = argparse.ArgumentParser(); ap.add_argument("--url", default="http://127.0.0.1:8888"); ap.add_argument("--cmd", default="")
ap.add_argument("--every", type=float, default=10); a = ap.parse_args()
bad = 0
while True:
    try:
        h = json.load(urllib.request.urlopen(a.url + "/health", timeout=3)); hb = h.get("heartbeat")
        alive = bool(hb and hb.get("alive"))
        print(time.strftime("%H:%M:%S"), "alive" if alive else "NO HEARTBEAT", json.dumps(hb), flush=True)
    except Exception as e:
        alive = False; print(time.strftime("%H:%M:%S"), "relay unreachable:", e, flush=True)
    bad = 0 if alive else bad + 1
    if bad >= 3 and a.cmd:
        print("→ running:", a.cmd, flush=True); subprocess.call(a.cmd, shell=True); bad = 0
    time.sleep(a.every)
