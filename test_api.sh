#!/bin/bash

# test_api.sh - Test Gemini API connection
# Kiểm tra kết nối và API key

# Màu sắc
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
BOLD='\033[1m'
RESET='\033[0m'

echo -e "${CYAN}${BOLD}"
echo "╔═══════════════════════════════════════╗"
echo "║                                       ║"
echo "║     🧪  TEST GEMINI API  🧪          ║"
echo "║                                       ║"
echo "╚═══════════════════════════════════════╝"
echo -e "${RESET}\n"

# Kiểm tra API key
echo -e "${BLUE}[1/4] Kiểm tra API Key...${RESET}"
if [ -z "$GEMINI_API_KEY" ]; then
    echo -e "${RED}❌ GEMINI_API_KEY chưa được thiết lập!${RESET}"
    echo -e "${YELLOW}Chạy: ./setup.sh để thiết lập${RESET}\n"
    exit 1
else
    echo -e "${GREEN}✅ API Key đã được thiết lập${RESET}"
    echo -e "${YELLOW}   Key: ${GEMINI_API_KEY:0:20}...${RESET}\n"
fi

# Kiểm tra curl
echo -e "${BLUE}[2/4] Kiểm tra curl command...${RESET}"
if ! command -v curl &> /dev/null; then
    echo -e "${RED}❌ curl không được cài đặt!${RESET}\n"
    exit 1
else
    echo -e "${GREEN}✅ curl đã sẵn sàng${RESET}\n"
fi

# Kiểm tra agent.sh
echo -e "${BLUE}[3/4] Kiểm tra agent.sh...${RESET}"
if [ ! -f "./agent.sh" ]; then
    echo -e "${RED}❌ Không tìm thấy agent.sh!${RESET}\n"
    exit 1
elif [ ! -x "./agent.sh" ]; then
    echo -e "${YELLOW}⚠️  agent.sh chưa có quyền thực thi${RESET}"
    chmod +x ./agent.sh
    echo -e "${GREEN}✅ Đã cấp quyền thực thi${RESET}\n"
else
    echo -e "${GREEN}✅ agent.sh sẵn sàng${RESET}\n"
fi

# Test API call
echo -e "${BLUE}[4/4] Test API call...${RESET}"
echo -e "${CYAN}Gửi tin nhắn: \"Xin chào, bạn có hoạt động không?\"${RESET}\n"

response=$(./agent.sh "Xin chào, bạn có hoạt động không?")
exit_code=$?

if [ $exit_code -eq 0 ]; then
    echo -e "${GREEN}${BOLD}✅ Test thành công!${RESET}\n"
    echo -e "${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${RESET}"
    echo -e "${BOLD}Response từ Gemini AI:${RESET}"
    echo "$response"
    echo -e "${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${RESET}\n"
    
    echo -e "${GREEN}${BOLD}🎉 Tất cả kiểm tra đều thành công!${RESET}"
    echo -e "${CYAN}Bạn có thể chạy chat client:${RESET} ${GREEN}./main.sh${RESET}\n"
else
    echo -e "${RED}${BOLD}❌ Test thất bại!${RESET}\n"
    echo -e "${YELLOW}Response:${RESET}"
    echo "$response"
    echo ""
    echo -e "${YELLOW}💡 Gợi ý:${RESET}"
    echo "1. Kiểm tra API key có đúng không"
    echo "2. Kiểm tra kết nối internet"
    echo "3. Thử chạy lại: ./setup.sh"
    echo ""
    exit 1
fi
