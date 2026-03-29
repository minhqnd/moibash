#!/bin/bash

# google_search.sh - Tìm kiếm Google với Gemini
# Tool: Google Search

# Load .env
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
if [ -f "$SCRIPT_DIR/../.env" ]; then
    set -a
    source "$SCRIPT_DIR/../.env"
    set +a
fi

USER_MESSAGE="$1"

if [ -z "$USER_MESSAGE" ]; then
    echo "❌ Không có câu hỏi"
    exit 1
fi

echo "🔍 Đang tìm kiếm..."

# Escape message
escaped_message=$(echo "$USER_MESSAGE" | sed 's/\\/\\\\/g' | sed 's/"/\\"/g')

# Gọi API với Google Search tool
response=$(curl -s -X POST \
    "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash-lite:generateContent?key=$GEMINI_API_KEY" \
    -H 'Content-Type: application/json' \
    -d "{
      \"contents\": [{
        \"parts\": [{\"text\": \"$escaped_message\"}]
      }],
      \"tools\": [{
        \"google_search\": {}
      }],
      \"generationConfig\": {
        \"temperature\": 0.7,
        \"maxOutputTokens\": 1024
      }
    }")

# Parse response bằng python
if command -v python3 &> /dev/null; then
    result=$(echo "$response" | python3 -c "
import sys, json
try:
    data = json.load(sys.stdin)
    
    # Lấy text response
    for candidate in data.get('candidates', []):
        for part in candidate.get('content', {}).get('parts', []):
            if 'text' in part:
                print(part['text'])
                sys.exit(0)
    
    # Nếu không có text, có thể có search results
    print('✅ Đã tìm kiếm, nhưng không có kết quả text')
    sys.exit(0)
except Exception as e:
    print(f'❌ Lỗi parse: {e}')
    sys.exit(1)
" 2>/dev/null)
    
    if [ $? -eq 0 ]; then
        echo ""
        echo "$result"
        exit 0
    fi
fi

# Fallback
text=$(echo "$response" | grep -o '"text"[[:space:]]*:[[:space:]]*"[^"]*"' | head -1 | sed 's/.*"text"[[:space:]]*:[[:space:]]*"//;s/".*//')

if [ ! -z "$text" ]; then
    echo ""
    echo "$text"
    exit 0
fi

echo "❌ Không tìm thấy kết quả"
exit 1
