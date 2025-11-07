#!/bin/bash

# uninstall.sh - Script gỡ cài đặt Moibash
# Xóa symlink khỏi /usr/local/bin

set -e

# Màu sắc
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
BLUE='\033[0;34m'
RESET='\033[0m'
BOLD='\033[1m'

BIN_DIR="/usr/local/bin"
SYMLINK_NAME="moibash"
SYMLINK_PATH="$BIN_DIR/$SYMLINK_NAME"

echo -e "${RED}${BOLD}╔════════════════════════════════════════╗${RESET}"
echo -e "${RED}${BOLD}║    MOIBASH UNINSTALLATION SCRIPT      ║${RESET}"
echo -e "${RED}${BOLD}╚════════════════════════════════════════╝${RESET}"
echo ""

# Kiểm tra symlink có tồn tại không
if [ ! -L "$SYMLINK_PATH" ] && [ ! -f "$SYMLINK_PATH" ]; then
    echo -e "${YELLOW}⚠️  Không tìm thấy moibash trong $BIN_DIR${RESET}"
    echo -e "${BLUE}Moibash chưa được cài đặt hoặc đã được gỡ cài đặt.${RESET}"
    exit 0
fi

# Kiểm tra quyền sudo nếu cần
if [ ! -w "$BIN_DIR" ]; then
    echo -e "${YELLOW}⚠️  Cần quyền sudo để xóa symlink từ $BIN_DIR${RESET}"
    echo -e "${BLUE}Nhập mật khẩu sudo:${RESET}"
    SUDO="sudo"
else
    SUDO=""
fi

# Xác nhận gỡ cài đặt
echo -e "${YELLOW}Bạn có chắc chắn muốn gỡ cài đặt moibash? (y/N)${RESET}"
read -r response

if [[ ! "$response" =~ ^[Yy]$ ]]; then
    echo -e "${BLUE}Đã hủy gỡ cài đặt.${RESET}"
    exit 0
fi

# Xóa symlink
echo -e "${BLUE}🗑️  Đang xóa symlink: $SYMLINK_PATH${RESET}"
$SUDO rm -f "$SYMLINK_PATH"

# Kiểm tra đã xóa thành công chưa
if [ ! -e "$SYMLINK_PATH" ]; then
    echo -e "${GREEN}${BOLD}✅ Đã gỡ cài đặt thành công!${RESET}"
    echo ""
    echo -e "${BLUE}📝 Lưu ý:${RESET}"
    echo -e "  - Thư mục moibash vẫn còn tại vị trí cài đặt"
    echo -e "  - Để cài đặt lại: ${CYAN}cd <moibash-dir> && ./install.sh${RESET}"
    echo ""
else
    echo -e "${RED}❌ Lỗi: Không thể xóa symlink!${RESET}"
    exit 1
fi
