#!/bin/bash

# install.sh - Script cài đặt Moibash
# Tạo symlink để gọi moibash từ bất kỳ đâu

set -e  # Exit on error

# Màu sắc
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
BLUE='\033[0;34m'
RESET='\033[0m'
BOLD='\033[1m'

# Lấy đường dẫn tuyệt đối của thư mục hiện tại
INSTALL_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
MAIN_SCRIPT="$INSTALL_DIR/moibash.sh"
BIN_DIR="/usr/local/bin"
SYMLINK_NAME="moibash"
SYMLINK_PATH="$BIN_DIR/$SYMLINK_NAME"

echo -e "${BLUE}${BOLD}╔════════════════════════════════════════╗${RESET}"
echo -e "${BLUE}${BOLD}║     MOIBASH INSTALLATION SCRIPT        ║${RESET}"
echo -e "${BLUE}${BOLD}╚════════════════════════════════════════╝${RESET}"
echo ""

# Kiểm tra main.sh có tồn tại không
if [ ! -f "$MAIN_SCRIPT" ]; then
    echo -e "${RED}❌ Lỗi: Không tìm thấy moibash.sh!${RESET}"
    echo -e "${YELLOW}Vui lòng chạy script này từ thư mục gốc của moibash${RESET}"
    exit 1
fi

# Kiểm tra quyền sudo nếu cần
if [ ! -w "$BIN_DIR" ]; then
    echo -e "${YELLOW}⚠️  Cần quyền sudo để tạo symlink trong $BIN_DIR${RESET}"
    echo -e "${BLUE}Nhập mật khẩu sudo:${RESET}"
    SUDO="sudo"
else
    SUDO=""
fi

# Cấp quyền thực thi cho main.sh
echo -e "${BLUE}📝 Cấp quyền thực thi cho moibash.sh...${RESET}"
chmod +x "$MAIN_SCRIPT"

# Cấp quyền cho các script khác
echo -e "${BLUE}📝 Cấp quyền thực thi cho các scripts...${RESET}"
chmod +x "$INSTALL_DIR/router.sh" 2>/dev/null || true
chmod +x "$INSTALL_DIR"/tools/*.sh 2>/dev/null || true
chmod +x "$INSTALL_DIR"/tools/*/*.sh 2>/dev/null || true
chmod +x "$INSTALL_DIR"/tools/*/*.py 2>/dev/null || true

# Xóa symlink cũ nếu tồn tại
if [ -L "$SYMLINK_PATH" ] || [ -f "$SYMLINK_PATH" ]; then
    echo -e "${YELLOW}⚠️  Phát hiện symlink/file cũ tại $SYMLINK_PATH${RESET}"
    echo -e "${BLUE}Đang xóa...${RESET}"
    $SUDO rm -f "$SYMLINK_PATH"
fi

# Tạo symlink mới
echo -e "${BLUE}🔗 Tạo symlink: $SYMLINK_PATH → $MAIN_SCRIPT${RESET}"
$SUDO ln -sf "$MAIN_SCRIPT" "$SYMLINK_PATH"

# Kiểm tra symlink đã tạo thành công chưa
if [ -L "$SYMLINK_PATH" ]; then
    echo -e "${GREEN}${BOLD}✅ Cài đặt thành công!${RESET}"
    echo ""
    echo -e "${GREEN}Bây giờ bạn có thể gọi moibash từ bất kỳ đâu:${RESET}"
    echo -e "${CYAN}  $ moibash${RESET}"
    echo ""
    echo -e "${BLUE}📁 Thư mục cài đặt: ${YELLOW}$INSTALL_DIR${RESET}"
    echo -e "${BLUE}🔗 Symlink: ${YELLOW}$SYMLINK_PATH${RESET}"
    echo ""
    echo -e "${YELLOW}💡 Tips:${RESET}"
    echo -e "  - Để cập nhật: ${CYAN}moibash --update${RESET}"
    echo -e "  - Để gỡ cài đặt: ${CYAN}cd $INSTALL_DIR && ./uninstall.sh${RESET}"
    echo ""
else
    echo -e "${RED}❌ Lỗi: Không thể tạo symlink!${RESET}"
    exit 1
fi
