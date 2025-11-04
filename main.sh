#!/bin/bash

# main.sh - Giao diện Chat Client
# Môn: Hệ Điều Hành
# Chat Agent Terminal Interface

# Màu sắc ANSI
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
BLUE='\033[0;34m'
MAGENTA='\033[0;35m'
CYAN='\033[0;36m'
WHITE='\033[1;37m'
GRAY='\033[0;90m'
RESET='\033[0m'
BOLD='\033[1m'

# Đường dẫn đến agent
ROUTER_SCRIPT="./router.sh"

# File lưu lịch sử chat (tạm thời trong session)
CHAT_HISTORY="./chat_history_$$.txt"

# Hàm parse markdown để hiển thị in đậm và in nghiêng
parse_markdown() {
    local text="$1"
    # Chuyển đổi **bold** thành ANSI bold
    text=$(echo "$text" | sed 's/\*\*\([^*]*\)\*\*/\\033[1m\1\\033[0m/g')
    # Chuyển đổi *italic* thành ANSI italic (nếu terminal hỗ trợ)
    text=$(echo "$text" | sed 's/\*\([^*]*\)\*/\\033[3m\1\\033[0m/g')
    echo "$text"
}

# Hàm xóa màn hình
clear_screen() {
    clear
}

# Hàm hiển thị banner
show_banner() {
    echo -e "${CYAN}${BOLD}"
    echo -e "             _ ______             _     "
    echo -e "            (_|____  \           | |    "
    echo -e " ____   ___  _ ____)  ) ____  ___| | _  "
    echo -e "|    \ / _ \| |  __  ( / _  |/___) || \ "
    echo -e "| | | | |_| | | |__)  | ( | |___ | | | |"
    echo -e "|_|_|_|\___/|_|______/ \_||_(___/|_| |_|"
    echo -e "                                        "
    echo -e "OSG Project"
    echo -e ""
    echo -e "${RESET}"
    echo -e "${GRAY}Gõ /help để xem danh sách lệnh${RESET}"
    echo ""
}

# Hàm hiển thị help
show_help() {
    echo -e "\n${YELLOW}${BOLD}📚 DANH SÁCH LỆNH:${RESET}"
    echo -e "${CYAN}  /help${RESET}   - Hiển thị danh sách lệnh"
    echo -e "${CYAN}  /clear${RESET}  - Xóa màn hình và lịch sử chat"
    echo -e "${CYAN}  /exit, /quit${RESET}   - Thoát chương trình"
    echo ""
}

# Hàm lấy thời gian hiện tại
get_timestamp() {
    date '+%H:%M:%S'
}

# Hàm hiển thị tin nhắn của user
display_user_message() {
    local message="$1"
    local timestamp=$(get_timestamp)
    echo -e "${GREEN}${BOLD}Bạn:${RESET} $message"
    # Lưu vào lịch sử
    echo "[$timestamp] USER: $message" >> "$CHAT_HISTORY"
}

# Hàm hiển thị tin nhắn của agent
display_agent_message() {
    local message="$1"
    local timestamp=$(get_timestamp)
    local formatted_message=$(parse_markdown "$message")
    echo -e "${MAGENTA}${BOLD}Agent:${RESET} $formatted_message"
    # Lưu vào lịch sử
    echo "[$timestamp] AGENT: $message" >> "$CHAT_HISTORY"
    echo ""
}

# Hàm hiển thị lỗi
display_error() {
    local message="$1"
    echo -e "${RED}${BOLD}❌ Lỗi:${RESET} $message"
    echo ""
}

# Hàm hiển thị thông tin
display_info() {
    local message="$1"
    echo -e "${BLUE}ℹ️  $message${RESET}"
    echo ""
}

# Hàm gọi agent và nhận response
call_agent() {
    local user_input="$1"
    
    # Kiểm tra agent script có tồn tại không
    if [ ! -f "$ROUTER_SCRIPT" ]; then
        display_error "Không tìm thấy agent.sh! Vui lòng đảm bảo file tồn tại."
        return 1
    fi
    
    # Kiểm tra agent script có quyền thực thi không
    if [ ! -x "$ROUTER_SCRIPT" ]; then
        chmod +x "$ROUTER_SCRIPT"
    fi
    
    # Gọi agent và nhận response
    local response=$("$ROUTER_SCRIPT" "$user_input")
    
    if [ $? -eq 0 ]; then
        echo "$response"
        return 0
    else
        return 1
    fi
}

# Hàm xử lý lệnh đặc biệt
handle_command() {
    local input="$1"
    
    case "$input" in
        /help)
            show_help
            return 0
            ;;
        /clear)
            clear_screen
            show_banner
            # Xóa lịch sử chat
            > "$CHAT_HISTORY"
            display_info "Đã xóa màn hình và lịch sử chat!"
            return 0
            ;;
        /exit|/quit)
            echo -e "\n${CYAN}${BOLD}👋 Tạm biệt! Hẹn gặp lại bạn!${RESET}\n"
            # Xóa file lịch sử tạm
            rm -f "$CHAT_HISTORY"
            exit 0
            ;;
        /*)
            display_error "Lệnh không hợp lệ! Gõ /help để xem danh sách lệnh."
            return 1
            ;;
        *)
            return 1
            ;;
    esac
}

# Hàm xử lý input từ user
process_input() {
    local user_input="$1"
    
    # Loại bỏ khoảng trắng đầu/cuối
    user_input=$(echo "$user_input" | sed 's/^[[:space:]]*//;s/[[:space:]]*$//')
    
    # Kiểm tra input rỗng
    if [ -z "$user_input" ]; then
        display_error "Tin nhắn không được để trống!"
        return 1
    fi
    
    # Hiển thị tin nhắn của user
    # display_user_message "$user_input"
    
    # Kiểm tra xem có phải lệnh đặc biệt không
    if handle_command "$user_input"; then
        return 0
    fi
    
    # Gọi agent để xử lý
    local agent_response=$(call_agent "$user_input")
    
    if [ $? -eq 0 ]; then
        display_agent_message "$agent_response"
    else
        display_error "Không thể nhận phản hồi từ agent!"
    fi
}

# Hàm khởi tạo chat
init_chat() {
    # Tạo file lịch sử tạm
    touch "$CHAT_HISTORY"
    
    # Xóa màn hình và hiển thị banner
    clear_screen
    show_banner
    
    # Tin nhắn chào mừng từ agent
    display_agent_message "Xin chào! Tôi là **Chat Agent** rất *vui* được trò chuyện với bạn! 👋"
}

# Hàm main loop
main_loop() {
    while true; do
        # Hiển thị prompt
        echo -ne "${BLUE}${BOLD}➜${RESET} "
        
        # Đọc input từ user
        read -r user_input
        
        # Xử lý input
        process_input "$user_input"
    done
}

# Hàm dọn dẹp khi thoát (Ctrl+C)
cleanup() {
    echo -e "\n\n${YELLOW}Đang dọn dẹp...${RESET}"
    rm -f "$CHAT_HISTORY"
    echo -e "${CYAN}${BOLD}👋 Tạm biệt! Hẹn gặp lại bạn!${RESET}\n"
    exit 0
}

# Bắt signal Ctrl+C
trap cleanup SIGINT SIGTERM

# ============================================
# MAIN PROGRAM
# ============================================

# Kiểm tra agent.sh có tồn tại không
if [ ! -f "$ROUTER_SCRIPT" ]; then
    echo -e "${RED}${BOLD}❌ LỖI:${RESET} Không tìm thấy file agent.sh!"
    echo -e "${YELLOW}Vui lòng đảm bảo agent.sh nằm cùng thư mục với main.sh${RESET}"
    exit 1
fi

# Khởi động chat
init_chat

# Chạy main loop
main_loop
