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

# Spinner hiển thị khi đợi agent phản hồi
SPINNER_PID=""
SPINNER_ACTIVE=0

# Danh sách câu chờ hài hước (có thể tuỳ biến)
SPINNER_MESSAGES=(
    "Đang khởi động agent thông minh nhất thế giới"
    "Đang truy cập thông tin từ thời Tam Quốc"
    "Đang kết nối với trạm ISS lấy kết quả"
    "Đang hỏi ý kiến hội đồng cố vấn AI"
    "Đang lục tung kho dữ liệu tối mật"
    "Đang gọi điện cho người trong tương lai"
    "Đang phân tích câu hỏi bằng lượng tử"
    "Đang đánh thức mô hình sau giấc ngủ đông"
    "Đang vi vu trên đám mây tìm đáp án"
)

random_spinner_message() {
    local n=${#SPINNER_MESSAGES[@]}
    if [ "$n" -eq 0 ]; then
        echo "Đang xử lý yêu cầu"
        return
    fi
    local idx=$(( RANDOM % n ))
    echo "${SPINNER_MESSAGES[$idx]}"
}

start_spinner() {
    local msg
    msg=${1:-"$(random_spinner_message)"}
    # Chỉ hiển thị nếu đầu ra là terminal
    if [ -t 2 ]; then
        SPINNER_ACTIVE=1
        {
            local frames="|/-\\"
            local i=0
            while [ "$SPINNER_ACTIVE" -eq 1 ]; do
                i=$(( (i + 1) % 4 ))
                printf "\r%s %s" "$msg" "${frames:$i:1}" >&2
                sleep 0.1
            done
        } &
        SPINNER_PID=$!
        disown "$SPINNER_PID" 2>/dev/null
    fi
}

stop_spinner() {
    if [ -n "$SPINNER_PID" ]; then
        SPINNER_ACTIVE=0
        # Kết thúc tiến trình spinner nếu còn chạy
        kill "$SPINNER_PID" 2>/dev/null
        wait "$SPINNER_PID" 2>/dev/null
        SPINNER_PID=""
        # Xoá dòng spinner
        printf "\r\033[K" >&2
    fi
}

# Đảm bảo spinner được tắt khi script kết thúc hoặc bị ngắt
trap 'stop_spinner' EXIT INT TERM

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
        weather)
            "$TOOLS_DIR/weather/function_call.sh" "$message"
            ;;
        calendar)
            "$TOOLS_DIR/calendar/function_call.sh" "$message"
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
start_spinner
intent=$(classify_intent "$USER_MESSAGE")

# Debug: Hiển thị intent (có thể tắt sau)
# echo "[Intent: $intent]" >&2

# Thực thi tool tương ứng
execute_tool "$intent" "$USER_MESSAGE"
exit_code=$?

# Dừng spinner khi đã có phản hồi
stop_spinner

exit $exit_code
