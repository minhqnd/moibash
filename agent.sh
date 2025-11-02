#!/bin/bash

# agent.sh - Xử lý tin nhắn với Gemini API
# Môn: Hệ Điều Hành

# Load API key từ .env file nếu tồn tại
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
if [ -f "$SCRIPT_DIR/.env" ]; then
    # Load .env file và set variables
    set -a
    source "$SCRIPT_DIR/.env"
    set +a
fi

# Cấu hình Gemini API
GEMINI_API_URL="https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash-exp:generateContent"
GEMINI_MODEL="gemini-2.0-flash-exp"

# Nhận tin nhắn từ tham số
USER_MESSAGE="$1"

# Hàm kiểm tra API key
check_api_key() {
    if [ -z "$GEMINI_API_KEY" ]; then
        echo "❌ Lỗi: Chưa thiết lập GEMINI_API_KEY!"
        echo ""
        echo "📌 Hướng dẫn thiết lập:"
        echo "1. Lấy API key tại: https://aistudio.google.com/app/apikey"
        echo "2. Thêm vào file ~/.zshrc hoặc ~/.bashrc:"
        echo "   export GEMINI_API_KEY='your-api-key-here'"
        echo "3. Reload shell: source ~/.zshrc"
        echo ""
        echo "Hoặc chạy tạm thời:"
        echo "export GEMINI_API_KEY='your-api-key-here'"
        return 1
    fi
    return 0
}

# Hàm escape JSON string
json_escape() {
    local string="$1"
    # Escape các ký tự đặc biệt cho JSON
    echo "$string" | sed 's/\\/\\\\/g' | sed 's/"/\\"/g' | sed 's/$/\\n/' | tr -d '\n' | sed 's/\\n$//'
}

# Hàm gọi Gemini API
call_gemini_api() {
    local user_message="$1"
    
    # Escape message cho JSON
    local escaped_message=$(json_escape "$user_message")
    
    # Tạo request JSON với system instruction
    local request_json=$(cat <<EOF
{
  "contents": [
    {
      "parts": [
        {
          "text": "$escaped_message"
        }
      ]
    }
  ],
  "systemInstruction": {
    "parts": [
      {
        "text": "Bạn là một trợ lý AI thân thiện và hữu ích. Hãy trả lời bằng tiếng Việt một cách tự nhiên, ngắn gọn và dễ hiểu. Sử dụng emoji phù hợp để làm câu trả lời sinh động hơn. Bạn đang được tích hợp vào một chương trình bash script chat client cho môn Hệ Điều Hành."
      }
    ]
  },
  "generationConfig": {
    "temperature": 0.9,
    "topK": 40,
    "topP": 0.95,
    "maxOutputTokens": 1024
  }
}
EOF
)
    
    # Gọi API với curl
    local response=$(curl -s -X POST "$GEMINI_API_URL?key=$GEMINI_API_KEY" \
        -H 'Content-Type: application/json' \
        -d "$request_json" 2>&1)
    
    # Kiểm tra lỗi curl
    if [ $? -ne 0 ]; then
        echo "❌ Lỗi kết nối API: $response"
        return 1
    fi
    
    # Kiểm tra lỗi API
    if echo "$response" | grep -q '"error"'; then
        local error_message=$(echo "$response" | grep -o '"message":"[^"]*"' | head -1 | sed 's/"message":"//;s/"//')
        if [ -z "$error_message" ]; then
            error_message="Không thể kết nối đến Gemini API"
        fi
        echo "❌ API Error: $error_message"
        return 1
    fi
    
    # Parse response để lấy text
    # Sử dụng python nếu có để parse JSON chính xác hơn
    if command -v python3 &> /dev/null; then
        local ai_response=$(echo "$response" | python3 -c "
import sys, json
try:
    data = json.load(sys.stdin)
    text = data['candidates'][0]['content']['parts'][0]['text']
    print(text, end='')
except:
    sys.exit(1)
")
        if [ $? -eq 0 ] && [ ! -z "$ai_response" ]; then
            echo "$ai_response"
            return 0
        fi
    fi
    
    # Fallback: Parse với sed/grep
    local ai_response=$(echo "$response" | grep -o '"text"[[:space:]]*:[[:space:]]*"[^"]*"' | head -1 | sed 's/"text"[[:space:]]*:[[:space:]]*"//;s/"$//')
    
    if [ -z "$ai_response" ]; then
        echo "❌ Không nhận được phản hồi hợp lệ từ API"
        return 1
    fi
    
    # Decode escaped characters
    ai_response=$(echo "$ai_response" | sed 's/\\n/\n/g' | sed 's/\\"/"/g' | sed 's/\\\\/\\/g')
    
    # Trả về response
    echo "$ai_response"
    return 0
}

# Hàm xử lý fallback khi API không khả dụng
fallback_response() {
    local message="$1"
    local lower_message=$(echo "$message" | tr '[:upper:]' '[:lower:]')
    
    # Một số response đơn giản
    if [[ "$lower_message" =~ ^(xin chào|chào|hello|hi|hey)$ ]]; then
        echo "Xin chào! Rất tiếc, hiện tại không thể kết nối đến Gemini API. Vui lòng kiểm tra lại cấu hình! �"
    elif [[ "$lower_message" =~ (tên|name) ]]; then
        echo "Mình là Chat Agent được hỗ trợ bởi Gemini API! � (Hiện đang ở chế độ offline)"
    else
        echo "⚠️ Chế độ offline: Không thể kết nối đến Gemini API. Vui lòng kiểm tra GEMINI_API_KEY và kết nối internet."
    fi
}

# Main: Xử lý và trả về response
if [ -z "$USER_MESSAGE" ]; then
    echo "❌ Lỗi: Không nhận được tin nhắn!"
    exit 1
fi

# Kiểm tra API key
if ! check_api_key; then
    exit 1
fi

# Gọi Gemini API
response=$(call_gemini_api "$USER_MESSAGE")

if [ $? -eq 0 ]; then
    echo "$response"
else
    fallback_response "$USER_MESSAGE"
fi