#!/bin/bash

# update.sh - Script cập nhật Moibash từ GitHub
# Pull code mới nhất và cài đặt lại symlink

set -e

# Màu sắc
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
RESET='\033[0m'
BOLD='\033[1m'

# Lấy đường dẫn của script
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

echo -e "${CYAN}${BOLD}╔════════════════════════════════════════╗${RESET}"
echo -e "${CYAN}${BOLD}║       MOIBASH UPDATE SCRIPT            ║${RESET}"
echo -e "${CYAN}${BOLD}╚════════════════════════════════════════╝${RESET}"
echo ""

# Kiểm tra git có cài đặt không
if ! command -v git &> /dev/null; then
    echo -e "${RED}❌ Lỗi: Git chưa được cài đặt!${RESET}"
    echo -e "${YELLOW}Vui lòng cài đặt git trước:${RESET}"
    echo -e "  macOS: ${CYAN}brew install git${RESET}"
    echo -e "  Linux: ${CYAN}sudo apt install git${RESET}"
    exit 1
fi

# Di chuyển đến thư mục moibash
cd "$SCRIPT_DIR"

# Kiểm tra có phải git repository không
if [ ! -d ".git" ]; then
    echo -e "${RED}❌ Lỗi: Đây không phải là git repository!${RESET}"
    echo -e "${YELLOW}Vui lòng clone từ GitHub:${RESET}"
    echo -e "  ${CYAN}git clone https://github.com/minhqnd/moibash.git${RESET}"
    exit 1
fi

echo -e "${BLUE}📁 Thư mục hiện tại: ${YELLOW}$SCRIPT_DIR${RESET}"
echo ""

# Lưu lại các thay đổi local (nếu có)
if ! git diff-index --quiet HEAD --; then
    echo -e "${YELLOW}⚠️  Phát hiện có thay đổi chưa commit${RESET}"
    echo -e "${BLUE}Đang stash các thay đổi...${RESET}"
    git stash push -m "Auto-stash before update on $(date)"
    STASHED=true
else
    STASHED=false
fi

# Lấy branch hiện tại
CURRENT_BRANCH=$(git branch --show-current)
echo -e "${BLUE}🌿 Branch hiện tại: ${YELLOW}$CURRENT_BRANCH${RESET}"

# Fetch updates từ remote
echo -e "${BLUE}🔄 Đang kiểm tra cập nhật từ GitHub...${RESET}"
git fetch origin

# Kiểm tra có updates không
LOCAL=$(git rev-parse @)
REMOTE=$(git rev-parse @{u} 2>/dev/null || echo "")

if [ -z "$REMOTE" ]; then
    echo -e "${YELLOW}⚠️  Không thể kết nối đến remote repository${RESET}"
    exit 1
fi

if [ "$LOCAL" = "$REMOTE" ]; then
    echo -e "${GREEN}✅ Moibash đã ở phiên bản mới nhất!${RESET}"
    
    if [ "$STASHED" = true ]; then
        echo -e "${BLUE}Đang khôi phục các thay đổi local...${RESET}"
        git stash pop
    fi
    
    exit 0
fi

# Có updates, pull về
echo -e "${CYAN}${BOLD}📥 Đang tải cập nhật...${RESET}"
echo ""

# Show commits sẽ được update
echo -e "${BLUE}Các thay đổi mới:${RESET}"
git log --oneline --decorate --graph HEAD..@{u} | head -10

echo ""
echo -e "${YELLOW}Tiếp tục cập nhật? (y/N)${RESET}"
read -r response

if [[ ! "$response" =~ ^[Yy]$ ]]; then
    echo -e "${BLUE}Đã hủy cập nhật.${RESET}"
    
    if [ "$STASHED" = true ]; then
        echo -e "${BLUE}Đang khôi phục các thay đổi local...${RESET}"
        git stash pop
    fi
    
    exit 0
fi

# Pull updates
echo -e "${BLUE}🔄 Đang pull code mới...${RESET}"
git pull origin "$CURRENT_BRANCH"

# Khôi phục các thay đổi local (nếu có)
if [ "$STASHED" = true ]; then
    echo -e "${BLUE}Đang khôi phục các thay đổi local...${RESET}"
    if git stash pop; then
        echo -e "${GREEN}✅ Đã khôi phục thay đổi local${RESET}"
    else
        echo -e "${YELLOW}⚠️  Có conflict khi khôi phục thay đổi local${RESET}"
        echo -e "${BLUE}Vui lòng resolve conflicts thủ công${RESET}"
    fi
fi

# Cấp quyền thực thi cho các scripts
echo -e "${BLUE}📝 Cập nhật quyền thực thi...${RESET}"
chmod +x main.sh router.sh 2>/dev/null || true
chmod +x install.sh uninstall.sh update.sh 2>/dev/null || true
chmod +x tools/*.sh 2>/dev/null || true
chmod +x tools/*/*.sh 2>/dev/null || true
chmod +x tools/*/*.py 2>/dev/null || true

# Reinstall symlink (đảm bảo symlink trỏ đúng vị trí)
if [ -L "/usr/local/bin/moibash" ]; then
    echo -e "${BLUE}🔗 Đang cập nhật symlink...${RESET}"
    ./install.sh
fi

echo ""
echo -e "${GREEN}${BOLD}✅ Cập nhật thành công!${RESET}"
echo ""
echo -e "${BLUE}📊 Thông tin phiên bản:${RESET}"
echo -e "  Branch: ${YELLOW}$CURRENT_BRANCH${RESET}"
echo -e "  Commit: ${YELLOW}$(git rev-parse --short HEAD)${RESET}"
echo -e "  Date: ${YELLOW}$(git log -1 --format=%cd --date=short)${RESET}"
echo ""
echo -e "${CYAN}🚀 Sẵn sàng sử dụng moibash!${RESET}"
echo ""
