#!/bin/bash

# moibash.sh - Giao diện Chat Client
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

# Lấy thư mục chứa script (để hỗ trợ symlink)
SCRIPT_DIR="$(cd "$(dirname "$(readlink -f "${BASH_SOURCE[0]}" 2>/dev/null || realpath "${BASH_SOURCE[0]}" 2>/dev/null || echo "${BASH_SOURCE[0]}")")" && pwd)"

# Đường dẫn đến agent
ROUTER_SCRIPT="$SCRIPT_DIR/router.sh"

# Đường dẫn đến .env file
ENV_FILE="$SCRIPT_DIR/.env"

# Hàm kiểm tra và setup API key
check_and_setup_api_key() {
    local api_key=""
    
    # Kiểm tra .env file có tồn tại không
    if [ ! -f "$ENV_FILE" ]; then
        echo -e "${YELLOW}⚠️  File .env không tồn tại!${RESET}"
        echo -e "${BLUE}Tạo file .env mới...${RESET}"
        touch "$ENV_FILE"
    fi
    
    # Đọc API key từ .env
    if [ -f "$ENV_FILE" ]; then
        api_key=$(grep "^GEMINI_API_KEY=" "$ENV_FILE" 2>/dev/null | cut -d= -f2 | tr -d "'" | tr -d '"' | tr -d ' ')
    fi
    
    # Kiểm tra API key có hợp lệ không
    if [ -z "$api_key" ] || [ "$api_key" = "" ]; then
        echo -e "${RED}${BOLD}❌ GEMINI API KEY chưa được thiết lập!${RESET}"
        echo ""
        echo -e "${YELLOW}Moibash cần Gemini API Key để hoạt động.${RESET}"
        echo -e "${CYAN}Lấy API key miễn phí tại: ${MAGENTA}https://makersuite.google.com/app/apikey${RESET}"
        echo ""
        echo -e "${GREEN}Vui lòng nhập GEMINI API KEY của bạn:${RESET}"
        echo -ne "${BLUE}${BOLD}➜${RESET} "
        read -r user_api_key
        
        if [ -z "$user_api_key" ]; then
            echo -e "${RED}❌ API Key không được để trống!${RESET}"
            echo -e "${YELLOW}Thoát chương trình.${RESET}"
            exit 1
        fi
        
        # Lưu API key vào .env
        echo "GEMINI_API_KEY='$user_api_key'" > "$ENV_FILE"
        echo ""
        echo -e "${GREEN}✅ Đã lưu API Key vào $ENV_FILE${RESET}"
        echo -e "${BLUE}Bạn có thể thay đổi API key bất kỳ lúc nào bằng cách chỉnh sửa file này.${RESET}"
        echo ""
        
        # Delay một chút để user đọc message
        sleep 1
    fi
}

# File lưu lịch sử chat (tạm thời trong session)
CHAT_HISTORY="$SCRIPT_DIR/chat_history_$$.txt"

# Version
VERSION="1.1.0"

# Auto-update check (only once per day)
AUTO_UPDATE_CHECK_FILE="$SCRIPT_DIR/.last_update_check"
check_for_updates() {
    # Skip if not in git repo or if checked today
    if [ ! -d "$SCRIPT_DIR/.git" ]; then
        return
    fi
    
    # Check if we already checked today
    if [ -f "$AUTO_UPDATE_CHECK_FILE" ]; then
        LAST_CHECK=$(cat "$AUTO_UPDATE_CHECK_FILE")
        TODAY=$(date +%Y-%m-%d)
        if [ "$LAST_CHECK" = "$TODAY" ]; then
            return
        fi
    fi
    
    # Check for updates silently
    cd "$SCRIPT_DIR" 2>/dev/null || return
    git fetch origin main 2>/dev/null || return
    
    LOCAL=$(git rev-parse HEAD 2>/dev/null)
    REMOTE=$(git rev-parse origin/main 2>/dev/null)
    
    if [ "$LOCAL" != "$REMOTE" ]; then
        echo -e "${YELLOW}⚠️  New version available! Run ${CYAN}moibash --update${YELLOW} to update.${RESET}"
        echo ""
    fi
    
    # Save check timestamp
    date +%Y-%m-%d > "$AUTO_UPDATE_CHECK_FILE"
}

# Function to perform update
perform_update() {
    echo -e "${CYAN}${BOLD}🔄 Updating moibash...${RESET}"
    
    if [ ! -d "$SCRIPT_DIR/.git" ]; then
        echo -e "${RED}❌ Not a git repository. Cannot auto-update.${RESET}"
        echo -e "${YELLOW}Please reinstall: ${CYAN}curl -fsSL https://raw.githubusercontent.com/minhqnd/moibash/main/install.sh | bash${RESET}"
        exit 1
    fi
    
    cd "$SCRIPT_DIR"
    
    # Stash any local changes
    git stash push -m "Auto-stash before update" 2>/dev/null
    
    # Pull latest changes
    echo -e "${BLUE}Pulling latest changes...${RESET}"
    if git pull origin main; then
        echo -e "${GREEN}✅ Updated successfully!${RESET}"
        echo -e "${BLUE}Restarting moibash...${RESET}"
        echo ""
        # Restart moibash
        exec "$SCRIPT_DIR/moibash.sh"
    else
        echo -e "${RED}❌ Update failed!${RESET}"
        echo -e "${YELLOW}Try manual update: cd $SCRIPT_DIR && git pull${RESET}"
        exit 1
    fi
}

# Hàm parse markdown để hiển thị đầy đủ markdown
parse_markdown() {
    local text="$1"
    local in_code_block=false
    
    # Process line by line
    while IFS= read -r line || [[ -n "$line" ]]; do
        # Code block markers (```)
        if [[ "$line" =~ ^\`\`\` ]]; then
            if [ "$in_code_block" = false ]; then
                in_code_block=true
                lang="${line#\`\`\`}"
                if [ -n "$lang" ]; then
                    echo -e "${CYAN}${BOLD}┌─ Code: $lang${RESET}"
                else
                    echo -e "${CYAN}${BOLD}┌─ Code${RESET}"
                fi
            else
                in_code_block=false
                echo -e "${CYAN}${BOLD}└─${RESET}"
            fi
            continue
        fi
        
        # Inside code block
        if [ "$in_code_block" = true ]; then
            echo -e "${CYAN}│${RESET} ${GRAY}${line}${RESET}"
            continue
        fi
        
        # Headings
        if [[ "$line" =~ ^###[[:space:]](.+)$ ]]; then
            echo -e "${YELLOW}${BOLD}${BASH_REMATCH[1]}${RESET}"
            continue
        elif [[ "$line" =~ ^##[[:space:]](.+)$ ]]; then
            echo -e "${CYAN}${BOLD}${BASH_REMATCH[1]}${RESET}"
            continue
        elif [[ "$line" =~ ^#[[:space:]](.+)$ ]]; then
            echo -e "${BLUE}${BOLD}${BASH_REMATCH[1]}${RESET}"
            continue
        fi
        
        # Bullet lists (- item)
        if [[ "$line" =~ ^([[:space:]]*)[-\*][[:space:]](.+)$ ]]; then
            indent="${BASH_REMATCH[1]}"
            item="${BASH_REMATCH[2]}"
            # Process inline formatting in item (use perl for better escape handling)
            item=$(echo "$item" | perl -pe 's/`([^`]*)`/\033[0;90m$1\033[0m/g')
            item=$(echo "$item" | perl -pe 's/\*\*([^*]+)\*\*/\033[1m$1\033[0m/g')
            item=$(echo "$item" | perl -pe 's/(?<!\*)\*([^*]+)\*(?!\*)/\033[3m$1\033[0m/g')
            echo -e "${indent}${GREEN}●${RESET} ${item}"
            continue
        fi
        
        # Numbered lists (1. item)
        if [[ "$line" =~ ^([[:space:]]*)([0-9]+)\.[[:space:]](.+)$ ]]; then
            indent="${BASH_REMATCH[1]}"
            number="${BASH_REMATCH[2]}"
            item="${BASH_REMATCH[3]}"
            # Process inline formatting
            item=$(echo "$item" | perl -pe 's/`([^`]*)`/\033[0;90m$1\033[0m/g')
            item=$(echo "$item" | perl -pe 's/\*\*([^*]+)\*\*/\033[1m$1\033[0m/g')
            item=$(echo "$item" | perl -pe 's/(?<!\*)\*([^*]+)\*(?!\*)/\033[3m$1\033[0m/g')
            echo -e "${indent}${CYAN}${number}.${RESET} ${item}"
            continue
        fi
        
        # Regular line with inline formatting
        # Bold (**text**) - must be processed before italic
        line=$(echo "$line" | perl -pe 's/\*\*([^*]+)\*\*/\033[1m$1\033[0m/g')
        # Italic (*text*) - use negative lookahead/lookbehind to avoid matching **
        line=$(echo "$line" | perl -pe 's/(?<!\*)\*([^*]+)\*(?!\*)/\033[3m$1\033[0m/g')
        # Inline code (`code`)
        line=$(echo "$line" | perl -pe 's/`([^`]*)`/\033[0;90m$1\033[0m/g')
        
        echo -e "$line"
    done <<< "$text"
}

# Hàm xóa màn hình
clear_screen() {
    clear
}

# Hàm hiển thị banner
show_banner() {
    echo -e "${CYAN}${BOLD}"
    echo -e "
██╗  ███╗   ███╗ ██████╗ ██╗██████╗  █████╗ ███████╗██╗  ██╗
╚██╗ ████╗ ████║██╔═══██╗██║██╔══██╗██╔══██╗██╔════╝██║  ██║
 ╚██╗██╔████╔██║██║   ██║██║██████╔╝███████║███████╗███████║
 ██╔╝██║╚██╔╝██║██║   ██║██║██╔══██╗██╔══██║╚════██║██╔══██║
██╔╝ ██║ ╚═╝ ██║╚██████╔╝██║██████╔╝██║  ██║███████║██║  ██║
╚═╝  ╚═╝     ╚═╝ ╚═════╝ ╚═╝╚═════╝ ╚═╝  ╚═╝╚══════╝╚═╝  ╚═╝"
    echo -e "${RESET}"
    # echo -e "version: ${YELLOW}${VERSION}${RESET}"
    echo -e "
Mẹo để bắt đầu:
1. Hỏi câu hỏi, sửa file hoặc chạy lệnh.
2. Cụ thể để có kết quả tốt nhất.
3. Tạo file MOIBASH.md để tùy chỉnh tương tác của bạn với MOIBASH.
4. ${GREEN}${BOLD}/help${RESET} để xem danh sách lệnh
5. ${GREEN}${BOLD}!<lệnh>${RESET} để chạy lệnh shell trực tiếp (ví dụ: ${GRAY}!ls -la${RESET})
6. Thoát bằng ${GREEN}${BOLD}/exit${RESET} hoặc ${GREEN}${BOLD}/quit${RESET}"
    echo ""
}

# Hàm hiển thị help
show_help() {
    echo -e "\n${YELLOW}${BOLD}📚 DANH SÁCH LỆNH:${RESET}"
    echo -e "${CYAN}  /help${RESET}   - Hiển thị danh sách lệnh"
    echo -e "${CYAN}  /clear${RESET}  - Xóa màn hình và lịch sử chat"
    echo -e "${CYAN}  /exit, /quit${RESET}   - Thoát chương trình"
    echo ""
    echo -e "${YELLOW}${BOLD}💡 TÍNH NĂNG:${RESET}"
    echo -e "${CYAN}  !<lệnh>${RESET} - Thực thi lệnh shell trực tiếp (ví dụ: ${GRAY}!ls -la${RESET})"
    echo ""
}

# Hàm hiển thị version
show_version() {
    echo -e "${CYAN}${BOLD}moibash${RESET} version ${YELLOW}${VERSION}${RESET}"
    echo -e "Repository: ${BLUE}https://github.com/minhqnd/moibash${RESET}"
}

# Hàm hiển thị usage
show_usage() {
    echo -e "${CYAN}${BOLD}Moibash${RESET} - AI Chat Agent với Function Calling"
    echo ""
    echo -e "${YELLOW}${BOLD}Usage:${RESET}"
    echo "  moibash               Khởi động chat interface"
    echo "  moibash --help        Hiển thị hướng dẫn sử dụng"
    echo "  moibash --version     Hiển thị phiên bản"
    echo "  moibash --update      Cập nhật từ GitHub"
    echo ""
    echo -e "${YELLOW}${BOLD}Trong chat:${RESET}"
    echo "  /help                 Danh sách lệnh"
    echo "  /clear                Xóa màn hình"
    echo "  /exit, /quit          Thoát"
    echo ""
    echo -e "${YELLOW}${BOLD}Examples:${RESET}"
    echo "  moibash                           # Bắt đầu chat"
    echo "  moibash --update                  # Cập nhật phiên bản mới"
    echo ""
    echo -e "${BLUE}Repository:${RESET} https://github.com/minhqnd/moibash"
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
    echo -ne "${MAGENTA}${BOLD}moiBash:${RESET} "
    parse_markdown "$message"
    # Lưu vào lịch sử
    echo "[$timestamp] moiBash: $message" >> "$CHAT_HISTORY"
}

# Hàm hiển thị lỗi
display_error() {
    local message="$1"
    echo -e "${RED}${BOLD}❌ Lỗi:${RESET} $message"
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
    
    # Kiểm tra nếu bắt đầu bằng ! thì chạy lệnh shell trực tiếp
    if [[ "$user_input" =~ ^! ]]; then
        # Lấy lệnh (bỏ dấu ! ở đầu)
        local shell_command="${user_input#!}"
        
        # Loại bỏ khoảng trắng đầu sau dấu !
        shell_command=$(echo "$shell_command" | sed 's/^[[:space:]]*//')
        
        if [ -z "$shell_command" ]; then
            display_error "Lệnh shell không được để trống!"
            return 1
        fi
        
        echo -e "${CYAN}${BOLD}$ ${shell_command}${RESET}"
        echo ""
        
        # Thực thi lệnh shell
        eval "$shell_command"
        local exit_code=$?
        
        echo ""
        if [ $exit_code -ne 0 ]; then
            echo -e "${RED}✗ Lệnh thực thi thất bại (Exit code: $exit_code)${RESET}"
        fi
        
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
    display_agent_message "Xin chào! Tôi là **moiBash**, rất *vui* được hỗ trợ bạn! 👋"
    echo ""
}

# Hàm main loop
main_loop() {
    # Hiển thị path cho input đầu tiên (dùng PWD thay vì SCRIPT_DIR)
    local display_path="${PWD/#$HOME/~}"
    echo -e "${GRAY}╭─ $display_path${RESET}"
    
    while true; do
        # Hiển thị prompt
        echo -ne "${GRAY}╰─${RESET} ${BLUE}${BOLD}➜${RESET} "
        
        # Đọc input từ user
        read -r user_input
        
        # Di chuyển lên 2 dòng, xóa dòng ╭─, xuống 1 dòng, xóa dòng ╰─
        echo -en "\033[1A\033[2K\r"  # Lên 1 dòng (đến ╰─), xóa dòng, về đầu dòng
        echo -en "\033[1A\033[2K\r"  # Lên 1 dòng nữa (đến ╭─), xóa dòng, về đầu dòng
        
        # Hiển thị lại prompt với input của user
        echo -e "${BLUE}${BOLD}➜${RESET} $user_input"
        # Thêm dòng trống sau câu hỏi user
        echo ""
        
        # Xử lý input
        process_input "$user_input"
        
        # Sau khi xử lý xong, hiển thị path cho input tiếp theo (dùng PWD)
        local display_path="${PWD/#$HOME/~}"
        echo -e "\n${GRAY}╭─ $display_path${RESET}"
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

# Xử lý command line arguments
case "${1:-}" in
    --help|-h)
        show_usage
        exit 0
        ;;
    --version|-v)
        show_version
        exit 0
        ;;
    --update|-u)
        perform_update
        ;;
    "")
        # Không có arguments, check for updates first
        check_for_updates
        # Check and setup API key if needed
        check_and_setup_api_key
        ;;
    *)
        echo -e "${RED}❌ Lỗi: Tham số không hợp lệ: $1${RESET}"
        echo -e "${YELLOW}Chạy 'moibash --help' để xem hướng dẫn${RESET}"
        exit 1
        ;;
esac

# Kiểm tra router.sh có tồn tại không
if [ ! -f "$ROUTER_SCRIPT" ]; then
    echo -e "${RED}${BOLD}❌ LỖI:${RESET} Không tìm thấy file router.sh!"
    echo -e "${YELLOW}Vui lòng đảm bảo router.sh nằm trong: $SCRIPT_DIR${RESET}"
    exit 1
fi

# Khởi động chat
init_chat

# Chạy main loop
main_loop
