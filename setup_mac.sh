#!/bin/bash
# Mac での自動起動セットアップスクリプト

set -e

DIR="$(cd "$(dirname "$0")" && pwd)"
PYTHON="$(which python3)"
PLIST="$HOME/Library/LaunchAgents/com.supplytracker.plist"

echo "=== Supply Tracker セットアップ ==="
echo "インストール先: $DIR"
echo "Python:         $PYTHON"

# 依存関係インストール
echo ""
echo "▶ 依存関係をインストール中..."
pip3 install -r "$DIR/requirements.txt" -q
python3 -m playwright install chromium

# plist 生成
echo ""
echo "▶ 自動起動を設定中..."
mkdir -p "$HOME/Library/LaunchAgents"

cat > "$PLIST" <<EOF
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
  <key>Label</key>
  <string>com.supplytracker</string>
  <key>ProgramArguments</key>
  <array>
    <string>$PYTHON</string>
    <string>$DIR/scheduler.py</string>
  </array>
  <key>WorkingDirectory</key>
  <string>$DIR</string>
  <key>RunAtLoad</key>
  <true/>
  <key>KeepAlive</key>
  <true/>
  <key>StandardOutPath</key>
  <string>$DIR/data/scheduler.log</string>
  <key>StandardErrorPath</key>
  <string>$DIR/data/scheduler.log</string>
</dict>
</plist>
EOF

# 既存のジョブをアンロードしてから登録
launchctl unload "$PLIST" 2>/dev/null || true
launchctl load "$PLIST"

echo ""
echo "✅ 完了！"
echo ""
echo "  ダッシュボード → http://localhost:5001"
echo "  ログ          → $DIR/data/scheduler.log"
echo ""
echo "  停止する場合:   launchctl unload $PLIST"
echo "  再起動する場合: launchctl kickstart gui/$(id -u)/com.supplytracker"
