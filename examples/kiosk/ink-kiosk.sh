#!/usr/bin/env bash
# 墨卷 · 展厅开机脚本（Linux / macOS）
#   bash examples/kiosk/ink-kiosk.sh            # 起中继 + 全屏 Chromium；浏览器崩了自动重开
#   INK_TOKEN=secret DMX_HOST=192.168.1.50 bash examples/kiosk/ink-kiosk.sh
set -u
ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
PORT="${INK_PORT:-8888}"
URL="${INK_URL:-http://127.0.0.1:$PORT/?preset=kiosk&grid=0}"
CHROME="${CHROME:-$(command -v chromium || command -v chromium-browser || command -v google-chrome || echo '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome')}"

cd "$ROOT"
python3 tools/vendor_mediapipe.py --check >/dev/null 2>&1 || echo "[kiosk] 提示：先跑 python3 tools/vendor_mediapipe.py，断网才有手势/面庞"
python3 server.py "$PORT" > /tmp/ink-server.log 2>&1 &
SRV=$!
trap 'kill $SRV 2>/dev/null' EXIT
sleep 1.5

# 浏览器守护：退出 / 崩溃就重开；Ctrl-C 结束整套
while true; do
  "$CHROME" --kiosk --incognito --noerrdialogs --disable-session-crashed-bubble --disable-infobars \
    --autoplay-policy=no-user-gesture-required --use-fake-ui-for-media-stream \
    --overscroll-history-navigation=0 --disable-pinch --app="$URL" >/dev/null 2>&1
  echo "[kiosk] browser exited $(date +%T), restarting in 3s"; sleep 3
done
