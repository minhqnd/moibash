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

When users ask about system capabilities or need help with specific features, provide accurate information about available tools and how to use them effectively."

# Gọi API
response=$(curl -s -X POST \
    "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent?key=$GEMINI_API_KEY" \
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
