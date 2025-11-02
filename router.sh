#!/bin/bash

# agent.sh - Agent Router với Intent Classification
# Môn: Hệ Điều Hành
# Flow: User message → Intent Classification → Tool Execution

# Load API key từ .env file
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
if [ -f "$SCRIPT_DIR/.env" ]; then
    set -a
    source "$SCRIPT_DIR/.env"
    set +a
fi

# Nhận tin nhắn từ tham số
USER_MESSAGE="$1"

# Thư mục tools
TOOLS_DIR="$SCRIPT_DIR/tools"

# Hàm kiểm tra API key
check_api_key() {
    if [ -z "$GEMINI_API_KEY" ]; then
        echo "❌ Lỗi: Chưa thiết lập GEMINI_API_KEY!"
        echo ""
        echo "📌 Tạo file .env với nội dung:"
        echo "   GEMINI_API_KEY='your-api-key-here'"
        return 1
    fi
    return 0
}

# Hàm phân loại intent
classify_intent() {
    local message="$1"
    
    # Gọi intent classifier
    local intent=$("$TOOLS_DIR/intent.sh" "$message" 2>/dev/null)
    
    if [ $? -eq 0 ] && [ ! -z "$intent" ]; then
        echo "$intent"
        return 0
    fi
    
    # Default: chat
    echo "chat"
    return 0
}

# Hàm thực thi tool theo intent
execute_tool() {
    local intent="$1"
    local message="$2"
    
    case "$intent" in
        chat)
            "$TOOLS_DIR/chat.sh" "$message"
            ;;
        image_create)
            "$TOOLS_DIR/image_create.sh" "$message"
            ;;
        google_search)
            "$TOOLS_DIR/google_search.sh" "$message"
            ;;
        *)
            echo "❌ Intent không hợp lệ: $intent"
            return 1
            ;;
    esac
    
    return $?
}

# Main: Xử lý tin nhắn
if [ -z "$USER_MESSAGE" ]; then
    echo "❌ Lỗi: Không nhận được tin nhắn!"
    exit 1
fi

# Kiểm tra API key
if ! check_api_key; then
    exit 1
fi

# Phân loại intent
intent=$(classify_intent "$USER_MESSAGE")

# Debug: Hiển thị intent (có thể tắt sau)
# echo "[Intent: $intent]" >&2

# Thực thi tool tương ứng
execute_tool "$intent" "$USER_MESSAGE"

exit $?
