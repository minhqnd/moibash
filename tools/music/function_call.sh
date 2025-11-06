#!/bin/bash

# function_call.sh - Music Agent Function Calling (Gemini)
# Input: câu hỏi tự nhiên ("phát bài Em của ngày hôm qua")
# Output: Gọi music.sh để lấy thông tin và phát preview

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
if [ -f "$SCRIPT_DIR/../../.env" ]; then
    source "$SCRIPT_DIR/../../.env"
fi

USER_MESSAGE="$1"
if [ -z "$USER_MESSAGE" ]; then
    echo "❌ Lỗi: Vui lòng nhập yêu cầu bài hát!"
    exit 1
fi

if [ -z "$GEMINI_API_KEY" ]; then
    echo "❌ Lỗi: Chưa thiết lập GEMINI_API_KEY!"
    exit 1
fi

# Escape ký tự đặc biệt
escaped_message=$(echo "$USER_MESSAGE" | sed 's/\\/\\\\/g; s/"/\\"/g')

# Gọi Gemini API
response=$(curl -s -X POST \
  "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent?key=$GEMINI_API_KEY" \
  -H "Content-Type: application/json" \
  -d "{
    \"systemInstruction\": {
      \"role\": \"system\",
      \"parts\": [{
        \"text\": \"Bạn là Music Name Extractor. 
Hãy đọc yêu cầu người dùng và chỉ trả về TÊN BÀI HÁT (string). 
Ví dụ: 
'Phát bài Em của ngày hôm qua' -> Em của ngày hôm qua
'Nghe nhạc Shape of You' -> Shape of You
'Thông tin bài Perfect' -> Perfect
Không trả JSON, không giải thích.\"
      }]
    },
    \"contents\": [{
      \"role\": \"user\",
      \"parts\": [{\"text\": \"$escaped_message\"}]
    }],
    \"generationConfig\": {\"temperature\": 0.1, \"maxOutputTokens\": 20}
  }")

# Parse Gemini output
track_name=$(echo "$response" | python3 -c "
import sys, json
try:
    data = json.load(sys.stdin)
    print(data['candidates'][0]['content']['parts'][0]['text'].strip())
except:
    print('')
")

if [ -z "$track_name" ]; then
    echo "❌ Không thể xác định bài hát từ yêu cầu của bạn."
    echo "💡 Thử lại: 'phát bài Em của ngày hôm qua' hoặc 'thông tin bài Perfect'"
    exit 1
fi

# Gọi music.sh
"$SCRIPT_DIR/music.sh" "$track_name"