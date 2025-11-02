#!/bin/bash

# intent.sh - Phân loại intent của user message
# Sử dụng Gemini để phân loại: chat, image_create, google_search

# Load .env
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
if [ -f "$SCRIPT_DIR/../.env" ]; then
    set -a
    source "$SCRIPT_DIR/../.env"
    set +a
fi

USER_MESSAGE="$1"

if [ -z "$USER_MESSAGE" ]; then
    echo "chat"
    exit 0
fi

# System instruction để phân loại intent
SYSTEM_INSTRUCTION="Bạn là một intent classifier. Phân loại câu hỏi của user vào 1 trong 5 loại:
- chat: Câu hỏi thông thường, trò chuyện, hỏi đáp kiến thức chung
- image_create: Yêu cầu tạo ảnh, vẽ ảnh, generate image
- google_search: Cần thông tin thời gian thực, tin tức, sự kiện mới, thông tin cập nhật
- weather: Hỏi về thời tiết, nhiệt độ, mưa nắng tại một địa điểm cụ thể
- calendar: Quản lý lịch, xem lịch trình, thêm/sửa/xóa sự kiện, họp, hẹn

CHỈ TRẢ VỀ MỘT TRONG NĂM TỪ: chat, image_create, google_search, weather, calendar
KHÔNG GIẢI THÍCH, CHỈ TRẢ VỀ TÊN INTENT"

# Escape message
escaped_message=$(echo "$USER_MESSAGE" | sed 's/\\/\\\\/g' | sed 's/"/\\"/g')

# Gọi API để classify
response=$(curl -s -X POST \
    "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash-exp:generateContent?key=$GEMINI_API_KEY" \
    -H 'Content-Type: application/json' \
    -d "{
      \"contents\": [{
        \"parts\": [{\"text\": \"$escaped_message\"}]
      }],
      \"systemInstruction\": {
        \"parts\": [{\"text\": \"$SYSTEM_INSTRUCTION\"}]
      },
      \"generationConfig\": {
        \"temperature\": 0.1,
        \"maxOutputTokens\": 10
      }
    }")

# Parse intent bằng python
if command -v python3 &> /dev/null; then
    intent=$(echo "$response" | python3 -c "
import sys, json, re
try:
    data = json.load(sys.stdin)
    text = data['candidates'][0]['content']['parts'][0]['text'].strip().lower()
    # Lấy intent từ text
    if 'image_create' in text or 'image' in text:
        print('image_create')
    elif 'google_search' in text or 'search' in text:
        print('google_search')
    elif 'weather' in text:
        print('weather')
    elif 'calendar' in text:
        print('calendar')
    else:
        print('chat')
except:
    print('chat')
" 2>/dev/null)
else
    # Fallback: parse bằng grep
    intent=$(echo "$response" | grep -o '"text"[[:space:]]*:[[:space:]]*"[^"]*"' | head -1 | sed 's/.*"text"[[:space:]]*:[[:space:]]*"//;s/".*//' | tr -d '\n' | tr '[:upper:]' '[:lower:]')
    
    if [[ "$intent" == *"image"* ]]; then
        intent="image_create"
    elif [[ "$intent" == *"search"* ]]; then
        intent="google_search"
    elif [[ "$intent" == *"weather"* ]]; then
        intent="weather"
    elif [[ "$intent" == *"calendar"* ]]; then
        intent="calendar"
    else
        intent="chat"
    fi
fi

# Đảm bảo intent hợp lệ
case "$intent" in
    image_create|google_search|weather|calendar|chat)
        echo "$intent"
        ;;
    *)
        echo "chat"
        ;;
esac
