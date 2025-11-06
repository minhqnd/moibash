#!/bin/bash
# play.sh - Phát nhạc preview (tương thích Git Bash / Windows)

URL="$1"

if [ -z "$URL" ]; then
  echo "❌ Không có URL để phát."
  exit 1
fi

# Ưu tiên mpv nếu có
if command -v mpv >/dev/null 2>&1; then
  echo "▶️ Đang phát bản xem trước bằng mpv..."
  # Git Bash cần 'setsid' hoặc '& disown' để tránh bị treo terminal
  setsid mpv --no-video --force-window=no "$URL" >/dev/null 2>&1 &
  disown
  exit 0
fi

# Nếu không có mpv, fallback mở trình duyệt (Windows style)
if command -v explorer.exe >/dev/null 2>&1; then
  echo "🎵 Mở bản preview trên trình duyệt..."
  explorer.exe "$URL"
  exit 0
fi

# Nếu cả hai đều không có
echo "⚠️ Không thể phát nhạc (không tìm thấy mpv hoặc explorer.exe)"
echo "🔗 Link preview: $URL"