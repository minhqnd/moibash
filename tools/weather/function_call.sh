#!/bin/bash

# function_call.sh - Sử dụng Gemini Function Calling để lấy thông tin thời tiết

# Load .env
if [ -f "../../.env" ]; then
    source "../../.env"
fi

USER_MESSAGE="$1"

if [ -z "$USER_MESSAGE" ]; then
    echo "❌ Lỗi: Vui lòng cung cấp câu hỏi về thời tiết!"
    exit 1
fi

if [ -z "$GEMINI_API_KEY" ]; then
    echo "❌ Lỗi: Chưa thiết lập GEMINI_API_KEY!"
    exit 1
fi

# Escape message for JSON
escaped_message=$(echo "$USER_MESSAGE" | sed 's/\\/\\\\/g; s/"/\\"/g')

# Gọi Gemini với Function Calling
response=$(curl -s -X POST \
    "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash-lite:generateContent?key=$GEMINI_API_KEY" \
    -H 'Content-Type: application/json' \
    -d "{
      \"contents\": [{
        \"role\": \"user\",
        \"parts\": [{\"text\": \"$escaped_message\"}]
      }],
      \"tools\": [{
        \"functionDeclarations\": [{
          \"name\": \"get_current_weather\",
          \"description\": \"Lấy thông tin thời tiết hiện tại cho một địa điểm\",
          \"parameters\": {
            \"type\": \"object\",
            \"properties\": {
              \"location\": {
                \"type\": \"string\",
                \"description\": \"Tên địa điểm. Bỏ dấu tiếng Việt, giữ khoảng trắng. Ví dụ: 'Hà Nội' → 'Ha Noi', 'Đà Nẵng' → 'Da Nang'\"
              }
            },
            \"required\": [\"location\"]
          }
        }]
      }]
    }")

# Parse location từ response
location=$(echo "$response" | python3 -c "
import sys, json
try:
    data = json.load(sys.stdin)
    candidates = data.get('candidates', [])
    if candidates:
        content = candidates[0].get('content', {})
        parts = content.get('parts', [])
        for part in parts:
            if 'functionCall' in part:
                func_call = part['functionCall']
                if func_call.get('name') == 'get_current_weather':
                    args = func_call.get('args', {})
                    print(args.get('location', ''))
                    exit(0)
    print('')
except:
    print('')
")

if [ -z "$location" ]; then
    echo "❌ Không thể xác định địa điểm từ câu hỏi của bạn."
    echo "💡 Vui lòng đặt câu hỏi rõ ràng hơn, ví dụ: 'Thời tiết ở Hà Nội thế nào?'"
    exit 1
fi

# Gọi weather.sh để lấy thông tin thời tiết
SCRIPT_DIR="$(dirname "$0")"
weather_data=$("$SCRIPT_DIR/weather.sh" "$location")

# Kiểm tra lỗi
if echo "$weather_data" | grep -q '"error"'; then
    echo "$weather_data"
    exit 1
fi

# Gửi kết quả lại cho Gemini để tạo response tự nhiên
escaped_weather=$(echo "$weather_data" | sed 's/\\/\\\\/g; s/"/\\"/g')

# Tạo prompt chi tiết cho Gemini
instruction="Bạn là trợ lý thời tiết thân thiện. Dựa trên dữ liệu thời tiết sau: $escaped_weather

Hãy trả lời CHI TIẾT và THÂN THIỆN bằng tiếng Việt:
- Mô tả thời tiết hiện tại tại địa điểm này
- Đánh giá nhiệt độ (nóng/mát/lạnh/thích hợp)
- Tình trạng mưa
- Gợi ý trang phục phù hợp
- Lời khuyên cho hoạt động ngoài trời

Viết tự nhiên như đang trò chuyện với bạn bè, nhưng ngắn gọn nhát có thể!"

final_response=$(curl -s -X POST \
    "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash-lite:generateContent?key=$GEMINI_API_KEY" \
    -H 'Content-Type: application/json' \
    -d "{
      \"contents\": [{
        \"role\": \"user\",
        \"parts\": [{\"text\": \"$instruction\"}]
      }]
    }")

# Parse response cuối cùng
natural_response=$(echo "$final_response" | python3 -c "
import sys, json
try:
    data = json.load(sys.stdin)
    text = data['candidates'][0]['content']['parts'][0].get('text', '')
    print(text)
except:
    print('')
")

if [ ! -z "$natural_response" ]; then
    echo "$natural_response"
else
    # Fallback: hiển thị thông tin cơ bản
    echo "$weather_data" | python3 -c "
import sys, json
try:
    data = json.load(sys.stdin)
    print(f'🌤️ Thời tiết tại {data.get(\"location\", \"N/A\")}, {data.get(\"country\", \"N/A\")}')
    print(f'🌡️ Nhiệt độ: {data.get(\"temperature\", \"N/A\")}°C')
    print(f'💧 Lượng mưa: {data.get(\"rain\", 0)} mm')
except:
    print('Lỗi hiển thị dữ liệu thời tiết')
"
fi
