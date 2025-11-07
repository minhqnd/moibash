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

# Danh sách câu chờ theo intent
SPINNER_CHAT=(
    "🤖 Đang khởi động agent thông minh nhất thế giới"
    "💭 Đang truy cập thông tin từ thời Tam Quốc"
    "🚀 Đang kết nối với trạm ISS lấy kết quả"
    "🧠 Đang hỏi ý kiến hội đồng cố vấn AI"
    "🔒 Đang lục tung kho dữ liệu tối mật"
    "⏰ Đang gọi điện cho người trong tương lai"
    "⚛️ Đang phân tích câu hỏi bằng lượng tử"
    "😴 Đang đánh thức mô hình sau giấc ngủ đông"
    "☁️ Đang vi vu trên đám mây tìm đáp án"
)

SPINNER_SEARCH=(
    "🔍 Đang lục tung Google tìm kiếm thông tin"
    "🔍 Đang đào sâu vào kho dữ liệu web"
    "🤖 Đang hỏi ý kiến các công cụ tìm kiếm"
    "📡 Đang truy cập mạng lưới thông tin toàn cầu"
    "📊 Đang phân tích kết quả tìm kiếm"
)

SPINNER_IMAGE=(
    "🎨 Đang vẽ tranh cho bạn nè"
    "🖼️ Đang tạo ảnh đẹp mắt từ trí tưởng tượng"
    "🤖 Đang nhờ họa sĩ AI vẽ tranh"
    "🎨 Đang pha màu và vẽ nét"
    "✨ Đang hoàn thiện bức ảnh"
)

SPINNER_CALENDAR=(
    "📅 Đang nhờ trợ lý kiểm tra lịch cho bạn"
    "📓 Đang lục tung sổ tay ghi chú"
    "🤖 Đang hỏi ý kiến trợ lý lịch"
    "📅 Đang kiểm tra các sự kiện sắp tới"
    "📋 Đang sắp xếp lịch trình"
)

SPINNER_WEATHER=(
    "🌤️ Đang ra ngoài trời nhìn mây"
    "📺 Đang xem dự báo thời tiết trên TV"
    "☀️ Đang hỏi ý kiến ông trời"
    "🌡️ Đang kiểm tra nhiệt độ và gió"
    "🗺️ Đang phân tích bản đồ thời tiết"
)

SPINNER_FILESYSTEM=(
    "📁 Đang lục tung ổ cứng tìm file"
    "💾 Đang thao tác với hệ thống file"
    "🔧 Đang chuẩn bị công cụ xử lý file"
    "📝 Đang kiểm tra quyền truy cập file"
    "⚙️ Đang thực thi thao tác file"
)

get_random_message_for_intent() {
    local intent="$1"
    local messages=()
    
    case "$intent" in
        chat)
            messages=("${SPINNER_CHAT[@]}")
            ;;
        google_search)
            messages=("${SPINNER_SEARCH[@]}")
            ;;
        image_create)
            messages=("${SPINNER_IMAGE[@]}")
            ;;
        calendar)
            messages=("${SPINNER_CALENDAR[@]}")
            ;;
        weather)
            messages=("${SPINNER_WEATHER[@]}")
            ;;
        filesystem)
            messages=("${SPINNER_FILESYSTEM[@]}")
            ;;
        *)
            messages=("${SPINNER_CHAT[@]}")  # Default to chat
            ;;
    esac
    
    local n=${#messages[@]}
    if [ "$n" -eq 0 ]; then
        echo "Đang xử lý yêu cầu"
        return
    fi
    local idx=$(( RANDOM % n ))
    echo "${messages[$idx]}"
}

start_spinner() {
    local intent="$1"
    local msg
    msg=$(get_random_message_for_intent "$intent")
    # Chỉ hiển thị nếu đầu ra là terminal
    if [ -t 2 ]; then
        SPINNER_ACTIVE=1
        {
            local frames="|/-\\"
            local i=0
            local elapsed=0
            local count=0
            while [ "$SPINNER_ACTIVE" -eq 1 ]; do
                i=$(( (i + 1) % 4 ))
                count=$((count + 1))
                if [ $count -eq 10 ]; then
                    elapsed=$((elapsed + 1))
                    count=0
                fi
                printf "\r%s (%ds) %s" "$msg" "$elapsed" "${frames:$i:1}" >&2
                sleep 0.1
            done
        } &
        SPINNER_PID=$!
        disown "$SPINNER_PID" 2>/dev/null
    fi
}

stop_spinner() {
    if [ -n "$SPINNER_PID" ] && [ "$SPINNER_ACTIVE" -eq 1 ]; then
        SPINNER_ACTIVE=0
        # Kết thúc tiến trình spinner nếu còn chạy
        if kill -0 "$SPINNER_PID" 2>/dev/null; then
            kill "$SPINNER_PID" 2>/dev/null
            wait "$SPINNER_PID" 2>/dev/null
        fi
        SPINNER_PID=""
        # Xoá dòng spinner
        printf "\r\033[K" >&2
    fi
}

# Cleanup function to be called on exit
cleanup() {
    stop_spinner
    # Remove trap to avoid recursive calls
    trap - EXIT INT TERM
}

# Đảm bảo spinner được tắt khi script kết thúc hoặc bị ngắt
trap 'cleanup' EXIT INT TERM

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
            # Ưu tiên dùng Python version nếu có
            if [ -f "$TOOLS_DIR/calendar/function_call.py" ]; then
                "$TOOLS_DIR/calendar/function_call.py" "$message"
            else
                "$TOOLS_DIR/calendar/function_call.sh" "$message"
            fi
            ;;
        filesystem)
            # Gọi filesystem agent với Python function calling
            # Pass user's current directory và chat history để agent biết context
            if [ -f "$TOOLS_DIR/filesystem/function_call.py" ]; then
                # Export PWD để Python script có thể đọc
                export MOIBASH_USER_PWD="$PWD"
                # Export chat history file path (sử dụng PID từ main process)
                export MOIBASH_CHAT_HISTORY="$SCRIPT_DIR/chat_history_${MOIBASH_PID:-$$}.txt"
                "$TOOLS_DIR/filesystem/function_call.py" "$message"
            else
                echo "❌ Filesystem agent chưa được cài đặt"
                return 1
            fi
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

# Bắt đầu spinner với intent cụ thể
start_spinner "$intent"

# Debug: Hiển thị intent (có thể tắt sau)
# echo "[Intent: $intent]" >&2

# Export spinner PID để tool có thể tắt nó
export MOIBASH_SPINNER_PID="$SPINNER_PID"
export MOIBASH_SPINNER_ACTIVE="$SPINNER_ACTIVE"

# Thực thi tool tương ứng (tool sẽ tự dừng spinner khi cần)
execute_tool "$intent" "$USER_MESSAGE"
exit_code=$?

# Dừng spinner trước khi thoát
stop_spinner

exit $exit_code
