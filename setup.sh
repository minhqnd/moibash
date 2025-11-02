#!/bin/bash

# setup.sh - Script thiết lập Gemini API Key
# Môn: Hệ Điều Hành

# Màu sắc
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
BOLD='\033[1m'
RESET='\033[0m'

echo -e "${CYAN}${BOLD}"
echo "╔════════════════════════════════════════════════╗"
echo "║                                                ║"
echo "║     🔧  THIẾT LẬP GEMINI API KEY  🔧          ║"
echo "║                                                ║"
echo "╚════════════════════════════════════════════════╝"
echo -e "${RESET}\n"

# Kiểm tra xem đã có API key chưa
if [ ! -z "$GEMINI_API_KEY" ]; then
    echo -e "${GREEN}✅ Đã có GEMINI_API_KEY trong môi trường!${RESET}"
    echo -e "${YELLOW}Key hiện tại: ${GEMINI_API_KEY:0:20}...${RESET}\n"
    
    read -p "Bạn có muốn thay đổi không? (y/N): " change
    if [[ ! "$change" =~ ^[Yy]$ ]]; then
        echo -e "\n${BLUE}Giữ nguyên API key hiện tại.${RESET}"
        exit 0
    fi
fi

echo -e "${YELLOW}📌 Hướng dẫn lấy API key:${RESET}"
echo "1. Truy cập: https://aistudio.google.com/app/apikey"
echo "2. Đăng nhập với tài khoản Google"
echo "3. Nhấn 'Create API Key'"
echo "4. Copy API key"
echo ""

# Nhập API key
read -p "Nhập Gemini API Key của bạn: " api_key

if [ -z "$api_key" ]; then
    echo -e "\n${RED}❌ API key không được để trống!${RESET}"
    exit 1
fi

# Xác định shell config file
shell_config=""
if [ -f "$HOME/.zshrc" ]; then
    shell_config="$HOME/.zshrc"
elif [ -f "$HOME/.bashrc" ]; then
    shell_config="$HOME/.bashrc"
else
    echo -e "\n${RED}❌ Không tìm thấy file config shell (.zshrc hoặc .bashrc)${RESET}"
    exit 1
fi

echo -e "\n${BLUE}Shell config file: $shell_config${RESET}"

# Kiểm tra xem đã có dòng export chưa
if grep -q "GEMINI_API_KEY" "$shell_config"; then
    echo -e "${YELLOW}⚠️  Đã tồn tại GEMINI_API_KEY trong file config!${RESET}"
    read -p "Bạn có muốn cập nhật không? (y/N): " update
    
    if [[ "$update" =~ ^[Yy]$ ]]; then
        # Backup file cũ
        cp "$shell_config" "${shell_config}.backup"
        echo -e "${GREEN}✅ Đã backup file config: ${shell_config}.backup${RESET}"
        
        # Xóa dòng cũ và thêm dòng mới
        sed -i.tmp '/GEMINI_API_KEY/d' "$shell_config"
        rm -f "${shell_config}.tmp"
        echo "export GEMINI_API_KEY='$api_key'" >> "$shell_config"
        echo -e "${GREEN}✅ Đã cập nhật API key!${RESET}"
    else
        echo -e "${YELLOW}Hủy bỏ cập nhật.${RESET}"
        exit 0
    fi
else
    # Thêm dòng mới
    echo "" >> "$shell_config"
    echo "# Gemini API Key for Chat Agent" >> "$shell_config"
    echo "export GEMINI_API_KEY='$api_key'" >> "$shell_config"
    echo -e "${GREEN}✅ Đã thêm API key vào $shell_config!${RESET}"
fi

# Export cho session hiện tại
export GEMINI_API_KEY="$api_key"

echo -e "\n${GREEN}${BOLD}🎉 Thiết lập thành công!${RESET}\n"
echo -e "${YELLOW}📝 Lưu ý:${RESET}"
echo "1. API key đã được lưu vào: $shell_config"
echo "2. Đã export cho terminal hiện tại"
echo "3. Với terminal mới, chạy: source $shell_config"
echo ""
echo -e "${CYAN}${BOLD}Bây giờ bạn có thể chạy:${RESET}"
echo -e "${GREEN}./main.sh${RESET}"
echo ""

# Test API key
read -p "Bạn có muốn test API key ngay không? (Y/n): " test_api
if [[ ! "$test_api" =~ ^[Nn]$ ]]; then
    echo -e "\n${BLUE}Đang test API key...${RESET}"
    response=$(./agent.sh "Xin chào, bạn có hoạt động không?")
    
    if [ $? -eq 0 ]; then
        echo -e "\n${GREEN}${BOLD}✅ Test thành công!${RESET}"
        echo -e "${CYAN}Response từ Gemini:${RESET}"
        echo "$response"
    else
        echo -e "\n${RED}❌ Test thất bại!${RESET}"
        echo "Response: $response"
    fi
fi

echo ""
