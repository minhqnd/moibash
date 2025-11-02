#!/bin/bash

# function_call.sh - Sử dụng Gemini Function Calling để lấy thông tin thời tiết
# Flow: User message → Gemini Function Calling → Extract location → Call weather API

# Load .env
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
if [ -f "$SCRIPT_DIR/../../.env" ]; then
    set -a
    source "$SCRIPT_DIR/../../.env"
    set +a
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
escaped_message=$(echo "$USER_MESSAGE" | sed 's/\\/\\\\/g' | sed 's/"/\\"/g' | sed 's/$/\\n/' | tr -d '\n' | sed 's/\\n$//')

# Bước 1: Gọi Gemini với Function Calling để extract location
function_call_response=$(curl -s -X POST \
    "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent?key=$GEMINI_API_KEY" \
    -H 'Content-Type: application/json' \
    -d "{
      \"contents\": [
        {
          \"role\": \"user\",
          \"parts\": [
            {
              \"text\": \"$escaped_message\"
            }
          ]
        }
      ],
      \"tools\": [
        {
          \"functionDeclarations\": [
            {
              \"name\": \"get_current_weather\",
              \"description\": \"Lấy thông tin thời tiết hiện tại cho một địa điểm cụ thể. Hỗ trợ tên thành phố, quốc gia bằng tiếng Việt hoặc tiếng Anh.\",
              \"parameters\": {
                \"type\": \"object\",
                \"properties\": {
                  \"location\": {
                    \"type\": \"string\",
                    \"description\": \"Tên địa điểm (thành phố, quận, huyện, quốc gia). Ví dụ: 'Hà Nội', 'London', 'New York', 'Tokyo'\"
                  }
                },
                \"required\": [\"location\"]
              }
            }
          ]
        }
      ]
    }")

# Debug: Hiển thị response (có thể comment sau)
# echo "DEBUG Response: $function_call_response" >&2

# Bước 2: Parse function call để lấy location
if command -v python3 &> /dev/null; then
    parse_result=$(echo "$function_call_response" | python3 -c "
import sys, json
try:
    data = json.load(sys.stdin)
    candidates = data.get('candidates', [])
    
    if not candidates:
        print('NO_FUNCTION_CALL')
        sys.exit(0)
    
    content = candidates[0].get('content', {})
    parts = content.get('parts', [])
    
    for part in parts:
        if 'functionCall' in part:
            func_call = part['functionCall']
            if func_call.get('name') == 'get_current_weather':
                args = func_call.get('args', {})
                location = args.get('location', '')
                if location:
                    print(f'LOCATION|{location}')
                    sys.exit(0)
    
    # Nếu không có function call, có thể là câu trả lời thông thường
    for part in parts:
        if 'text' in part:
            print(f'TEXT|{part[\"text\"]}')
            sys.exit(0)
    
    print('NO_FUNCTION_CALL')
except Exception as e:
    print(f'ERROR|{str(e)}')
" 2>/dev/null)
else
    # Fallback parsing nếu không có python
    if echo "$function_call_response" | grep -q '"functionCall"'; then
        location=$(echo "$function_call_response" | grep -o '"location"[[:space:]]*:[[:space:]]*"[^"]*"' | head -1 | sed 's/.*"location"[[:space:]]*:[[:space:]]*"//;s/".*//')
        if [ ! -z "$location" ]; then
            parse_result="LOCATION|$location"
        else
            parse_result="NO_FUNCTION_CALL"
        fi
    else
        parse_result="NO_FUNCTION_CALL"
    fi
fi

# Xử lý kết quả parse
IFS='|' read -r result_type result_value <<< "$parse_result"

case "$result_type" in
    LOCATION)
        # Bước 3: Gọi weather.sh để lấy thông tin thời tiết
        weather_data=$("$SCRIPT_DIR/weather.sh" "$result_value")
        
        # Kiểm tra lỗi
        if echo "$weather_data" | grep -q '"error"'; then
            echo "$weather_data"
            exit 1
        fi
        
        # Bước 4: Format kết quả cho người dùng
        if command -v python3 &> /dev/null; then
            formatted_output=$(echo "$weather_data" | python3 -c "
import sys, json
try:
    data = json.load(sys.stdin)
    location = data.get('location', 'N/A')
    country = data.get('country', '')
    temp = data.get('temperature', 'N/A')
    rain = data.get('rain', 0)
    time = data.get('time', 'N/A')
    
    output = f'''🌤️ Thông tin thời tiết tại {location}'''
    if country:
        output += f', {country}'
    output += f'''

🌡️ Nhiệt độ: {temp}°C
☔ Lượng mưa: {rain} mm
🕐 Thời gian: {time}
📍 Tọa độ: {data.get('latitude', 'N/A')}, {data.get('longitude', 'N/A')}'''
    
    print(output)
except Exception as e:
    print(f'Lỗi định dạng: {str(e)}')
" 2>/dev/null)
        else
            # Fallback format
            formatted_output="$weather_data"
        fi
        
        echo "$formatted_output"
        
        # Bước 5: Gửi kết quả lại cho Gemini để tạo response tự nhiên
        escaped_weather=$(echo "$weather_data" | sed 's/\\/\\\\/g' | sed 's/"/\\"/g' | sed 's/$/\\n/' | tr -d '\n' | sed 's/\\n$//')
        
        final_response=$(curl -s -X POST \
            "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent?key=$GEMINI_API_KEY" \
            -H 'Content-Type: application/json' \
            -d "{
              \"contents\": [
                {
                  \"role\": \"user\",
                  \"parts\": [{\"text\": \"$escaped_message\"}]
                },
                {
                  \"role\": \"model\",
                  \"parts\": [{
                    \"functionCall\": {
                      \"name\": \"get_current_weather\",
                      \"args\": {\"location\": \"$result_value\"}
                    }
                  }]
                },
                {
                  \"role\": \"function\",
                  \"parts\": [{
                    \"functionResponse\": {
                      \"name\": \"get_current_weather\",
                      \"response\": {
                        \"content\": $weather_data
                      }
                    }
                  }]
                }
              ],
              \"tools\": [
                {
                  \"functionDeclarations\": [
                    {
                      \"name\": \"get_current_weather\",
                      \"description\": \"Lấy thông tin thời tiết hiện tại cho một địa điểm cụ thể.\",
                      \"parameters\": {
                        \"type\": \"object\",
                        \"properties\": {
                          \"location\": {
                            \"type\": \"string\",
                            \"description\": \"Tên địa điểm\"
                          }
                        },
                        \"required\": [\"location\"]
                      }
                    }
                  ]
                }
              ]
            }")
        
        # Parse response cuối cùng
        if command -v python3 &> /dev/null; then
            natural_response=$(echo "$final_response" | python3 -c "
import sys, json
try:
    data = json.load(sys.stdin)
    text = data['candidates'][0]['content']['parts'][0].get('text', '')
    if text:
        print(text)
    else:
        sys.exit(1)
except:
    sys.exit(1)
" 2>/dev/null)
            
            if [ $? -eq 0 ] && [ ! -z "$natural_response" ]; then
                echo ""
                echo "💬 Phân tích:"
                echo "$natural_response"
            fi
        fi
        ;;
        
    TEXT)
        # Gemini trả về text thông thường (không phải weather query)
        echo "$result_value"
        ;;
        
    NO_FUNCTION_CALL)
        echo "❌ Không thể xác định địa điểm từ câu hỏi của bạn."
        echo "💡 Vui lòng đặt câu hỏi rõ ràng hơn, ví dụ: 'Thời tiết ở Hà Nội thế nào?'"
        exit 1
        ;;
        
    ERROR)
        echo "❌ Lỗi khi xử lý: $result_value"
        exit 1
        ;;
        
    *)
        echo "❌ Lỗi không xác định"
        exit 1
        ;;
esac
