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

# Tìm file chat history (file mới nhất với pattern chat_history_*.txt)
CHAT_HISTORY_FILE=""
if [ -f "$SCRIPT_DIR/../chat_history_$$.txt" ]; then
    CHAT_HISTORY_FILE="$SCRIPT_DIR/../chat_history_$$.txt"
elif ls "$SCRIPT_DIR/../chat_history_"*.txt 1> /dev/null 2>&1; then
    # Lấy file mới nhất nếu không tìm thấy file với PID hiện tại
    CHAT_HISTORY_FILE=$(ls -t "$SCRIPT_DIR/../chat_history_"*.txt | head -1)
fi

# Escape message
escaped_message=$(echo "$USER_MESSAGE" | sed 's/\\/\\\\/g' | sed 's/"/\\"/g')

# Build chat history context cho API (không dùng Python)
HISTORY_CONTEXT=""
if [ -f "$CHAT_HISTORY_FILE" ]; then
    # Đọc lịch sử chat và build context
    # Lấy 20 dòng cuối cùng để tránh context quá dài
    HISTORY_LINES=""
    while IFS= read -r line; do
        # Parse format: [timestamp] ROLE: message
        if [[ "$line" =~ ^\[.*\][[:space:]]USER:[[:space:]](.+)$ ]]; then
            msg="${BASH_REMATCH[1]}"
            # Escape đúng cách cho JSON
            escaped_msg=$(echo "$msg" | sed 's/\\/\\\\/g; s/"/\\"/g')
            if [ -z "$HISTORY_LINES" ]; then
                HISTORY_LINES="USER: $escaped_msg"
            else
                HISTORY_LINES="$HISTORY_LINES | USER: $escaped_msg"
            fi
        elif [[ "$line" =~ ^\[.*\][[:space:]]moiBash:[[:space:]](.+)$ ]]; then
            msg="${BASH_REMATCH[1]}"
            escaped_msg=$(echo "$msg" | sed 's/\\/\\\\/g; s/"/\\"/g')
            if [ -z "$HISTORY_LINES" ]; then
                HISTORY_LINES="ASSISTANT: $escaped_msg"
            else
                HISTORY_LINES="$HISTORY_LINES | ASSISTANT: $escaped_msg"
            fi
        fi
    done < <(tail -20 "$CHAT_HISTORY_FILE")
    HISTORY_CONTEXT="$HISTORY_LINES"
fi

# Build context message với history
CONTEXT_MESSAGE="$escaped_message"
if [ -n "$HISTORY_CONTEXT" ]; then
    escaped_history=$(echo "$HISTORY_CONTEXT" | sed 's/\\/\\\\/g; s/"/\\"/g')
    CONTEXT_MESSAGE="[CHAT HISTORY]\\n$escaped_history\\n\\n[CURRENT MESSAGE]\\n$escaped_message"
fi

# System instruction
SYSTEM_INSTRUCTION="You are Moibash Agent, an intelligent AI assistant integrated into the Moibash system. Moibash is a comprehensive AI-powered terminal application that provides natural language interfaces for various productivity tasks.

Core Capabilities:
- Intelligent conversation and general assistance
- File system management (create, read, update, delete files and folders with safety confirmations)
- Google Calendar integration for scheduling and event management
- Weather information retrieval by location
- AI-powered image generation from text descriptions
- Web search functionality for real-time information

Response Guidelines:
- Respond in Vietnamese for Vietnamese queries, English for English queries
- Provide clear, concise, and helpful responses
- Maintain professional and friendly tone
- Focus on chat-related queries; for specific tools, guide users to use appropriate commands
- Explain complex concepts in simple terms when needed
- Ask clarifying questions when user intent is unclear
- Use markdown formatting for better readability
- **IMPORTANT**: When you see [CHAT HISTORY] at the beginning of the message, use it to understand the conversation context. The current user message will be under [CURRENT MESSAGE]. Refer to previous messages when relevant to provide contextual responses.

When users ask about system capabilities or need help with specific features, provide accurate information about available tools and how to use them effectively."

# Gọi API
response=$(curl -s -X POST \
    "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent?key=$GEMINI_API_KEY" \
    -H 'Content-Type: application/json' \
    -d "{
      \"contents\": [{
        \"parts\": [{\"text\": \"$CONTEXT_MESSAGE\"}]
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

# Kiểm tra error trong response
if echo "$response" | grep -q '"error"'; then
    error_msg=$(echo "$response" | python3 -c "
import sys, json
try:
    data = json.load(sys.stdin)
    print(data['error']['message'])
except:
    print('API Error')
" 2>/dev/null)
    echo "❌ API Error: $error_msg"
    exit 1
fi

# Parse response bằng python
if command -v python3 &> /dev/null; then
    ai_response=$(echo "$response" | python3 -c "
import sys, json
try:
    data = json.load(sys.stdin)
    text = data['candidates'][0]['content']['parts'][0]['text']
    print(text, end='')
except Exception as e:
    print(f'Parse error: {e}', file=sys.stderr)
    sys.exit(1)
" 2>&1)
    
    parse_exit=$?
    
    if [ $parse_exit -eq 0 ] && [ ! -z "$ai_response" ]; then
        echo "$ai_response"
        exit 0
    else
        echo "❌ Lỗi parse response: $ai_response"
        echo "Response gốc (100 ký tự đầu): ${response:0:100}"
        exit 1
    fi
fi

# Fallback
echo "❌ Python không khả dụng"
exit 1
