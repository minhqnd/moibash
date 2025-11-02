#!/bin/bash

# chat.sh - Chat thông thường với Gemini
# Tool: Chat

# Load .env
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
if [ -f "$SCRIPT_DIR/../.env" ]; then
    set -a
    source "$SCRIPT_DIR/../.env"
    set +a
fi

USER_MESSAGE="$1"

if [ -z "$USER_MESSAGE" ]; then
    echo "❌ Không có tin nhắn"
    exit 1
fi

# Escape message
escaped_message=$(echo "$USER_MESSAGE" | sed 's/\\/\\\\/g' | sed 's/"/\\"/g')

# System instruction
SYSTEM_INSTRUCTION="Bạn là một trợ lý AI thân thiện và hữu ích. Hãy trả lời bằng tiếng Việt một cách tự nhiên, ngắn gọn và dễ hiểu. Sử dụng emoji phù hợp để làm câu trả lời sinh động hơn."

# Gọi API
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
        \"temperature\": 0.9,
        \"topK\": 40,
        \"topP\": 0.95,
        \"maxOutputTokens\": 1024
      }
    }")

# Parse response bằng python
if command -v python3 &> /dev/null; then
    ai_response=$(echo "$response" | python3 -c "
import sys, json
try:
    data = json.load(sys.stdin)
    text = data['candidates'][0]['content']['parts'][0]['text']
    print(text, end='')
except:
    print('❌ Lỗi parse response')
    sys.exit(1)
" 2>/dev/null)
    
    if [ $? -eq 0 ] && [ ! -z "$ai_response" ]; then
        echo "$ai_response"
        exit 0
    fi
fi

# Fallback
echo "❌ Không nhận được phản hồi"
exit 1
