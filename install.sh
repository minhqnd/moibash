#!/bin/bash

# install.sh - Universal Installation Script for Moibash
# Usage 1 (Remote): curl -fsSL https://raw.githubusercontent.com/minhqnd/moibash/main/install.sh | bash
# Usage 2 (Local):  ./install.sh
# Usage 3 (Uninstall): ./install.sh --uninstall

set -e  # Exit on error

# Màu sắc
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
MAGENTA='\033[0;35m'
RESET='\033[0m'
BOLD='\033[1m'

# Handle uninstall
if [ "$1" = "--uninstall" ] || [ "$1" = "-u" ]; then
    echo -e "${RED}${BOLD}"
    echo '╔═══════════════════════════════════════════════════╗'
    echo '║         MOIBASH UNINSTALLATION                    ║'
    echo '╚═══════════════════════════════════════════════════╝'
    echo -e "${RESET}"
    
    INSTALL_DIR="$HOME/.moibash"
    SYMLINK_PATH="/usr/local/bin/moibash"
    
    echo -e "${YELLOW}This will remove:${RESET}"
    echo -e "  • Installation directory: ${CYAN}$INSTALL_DIR${RESET}"
    echo -e "  • Symlink: ${CYAN}$SYMLINK_PATH${RESET}"
    echo ""
    echo -ne "${RED}Are you sure? (y/N): ${RESET}"
    read -r response
    
    if [[ ! "$response" =~ ^[Yy]$ ]]; then
        echo -e "${BLUE}Uninstallation cancelled.${RESET}"
        exit 0
    fi
    
    # Remove installation directory
    if [ -d "$INSTALL_DIR" ]; then
        echo -e "${BLUE}Removing $INSTALL_DIR...${RESET}"
        rm -rf "$INSTALL_DIR"
        echo -e "${GREEN}✅ Removed${RESET}"
    fi
    
    # Remove symlink
    if [ -L "$SYMLINK_PATH" ] || [ -f "$SYMLINK_PATH" ]; then
        echo -e "${BLUE}Removing symlink...${RESET}"
        if [ -w "/usr/local/bin" ]; then
            rm -f "$SYMLINK_PATH"
        else
            sudo rm -f "$SYMLINK_PATH"
        fi
        echo -e "${GREEN}✅ Removed${RESET}"
    fi
    
    echo ""
    echo -e "${GREEN}${BOLD}✅ Moibash uninstalled successfully!${RESET}"
    echo -e "${BLUE}Thanks for using moibash! 👋${RESET}"
    echo ""
    exit 0
fi

# Handle help
if [ "$1" = "--help" ] || [ "$1" = "-h" ]; then
    echo -e "${CYAN}${BOLD}Moibash Installation Script${RESET}"
    echo ""
    echo -e "${YELLOW}${BOLD}Usage:${RESET}"
    echo "  ./install.sh                    Install moibash locally"
    echo "  curl ... install.sh | bash      Install moibash remotely"
    echo "  ./install.sh --uninstall        Uninstall moibash"
    echo "  ./install.sh --help             Show this help"
    echo ""
    echo -e "${YELLOW}${BOLD}Description:${RESET}"
    echo "  This script installs moibash with all dependencies."
    echo "  It will check system requirements and guide you through setup."
    echo ""
    echo -e "${YELLOW}${BOLD}Requirements:${RESET}"
    echo "  • Python 3.6+"
    echo "  • pip3"
    echo "  • curl"
    echo "  • git"
    echo ""
    echo -e "${BLUE}Repository: ${MAGENTA}https://github.com/minhqnd/moibash${RESET}"
    echo ""
    exit 0
fi

# Detect if running as remote install or local install
if [ -f "$(dirname "$0")/moibash.sh" ]; then
    # Local install - already in moibash directory
    IS_LOCAL=true
    INSTALL_DIR="$(cd "$(dirname "$0")" && pwd)"
else
    # Remote install - need to clone
    IS_LOCAL=false
    INSTALL_DIR="$HOME/.moibash"
fi

# Configuration
REPO_URL="https://github.com/minhqnd/moibash.git"
BIN_DIR="/usr/local/bin"
SYMLINK_NAME="moibash"
SYMLINK_PATH="$BIN_DIR/$SYMLINK_NAME"

echo -e "${BLUE}${BOLD}"
echo '
██╗  ███╗   ███╗ ██████╗ ██╗██████╗  █████╗ ███████╗██╗  ██╗
╚██╗ ████╗ ████║██╔═══██╗██║██╔══██╗██╔══██╗██╔════╝██║  ██║
 ╚██╗██╔████╔██║██║   ██║██║██████╔╝███████║███████╗███████║
 ██╔╝██║╚██╔╝██║██║   ██║██║██╔══██╗██╔══██║╚════██║██╔══██║
██╔╝ ██║ ╚═╝ ██║╚██████╔╝██║██████╔╝██║  ██║███████║██║  ██║
╚═╝  ╚═╝     ╚═╝ ╚═════╝ ╚═╝╚═════╝ ╚═╝  ╚═╝╚══════╝╚═╝  ╚═╝
'
echo -e "${RESET}"
echo -e "${CYAN}${BOLD}╔════════════════════════════════════════════════════╗${RESET}"
echo -e "${CYAN}${BOLD}║     MOIBASH REMOTE INSTALLATION SCRIPT             ║${RESET}"
echo -e "${CYAN}${BOLD}╚════════════════════════════════════════════════════╝${RESET}"
echo ""

# Function to check if command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Check prerequisites
echo -e "${BLUE}📋 Checking prerequisites...${RESET}"

# Check Git
if ! command_exists git; then
    echo -e "${RED}❌ Git is not installed!${RESET}"
    echo -e "${YELLOW}Please install git first:${RESET}"
    echo -e "  macOS:   ${CYAN}brew install git${RESET}"
    echo -e "  Ubuntu:  ${CYAN}sudo apt-get install git${RESET}"
    echo -e "  CentOS:  ${CYAN}sudo yum install git${RESET}"
    exit 1
fi
echo -e "${GREEN}✅ Git found${RESET}"

# Check curl
if ! command_exists curl; then
    echo -e "${RED}❌ curl is not installed!${RESET}"
    echo -e "${YELLOW}Please install curl first:${RESET}"
    echo -e "  macOS:   ${CYAN}brew install curl${RESET}"
    echo -e "  Ubuntu:  ${CYAN}sudo apt-get install curl${RESET}"
    echo -e "  CentOS:  ${CYAN}sudo yum install curl${RESET}"
    exit 1
fi
echo -e "${GREEN}✅ curl found${RESET}"

# Check Python 3
if ! command_exists python3; then
    echo -e "${RED}❌ Python 3 is not installed!${RESET}"
    echo -e "${YELLOW}Moibash requires Python 3 to run some agents.${RESET}"
    echo -e "${YELLOW}Please install Python 3 first:${RESET}"
    echo -e "  macOS:   ${CYAN}brew install python3${RESET}"
    echo -e "  Ubuntu:  ${CYAN}sudo apt-get install python3 python3-pip${RESET}"
    echo -e "  CentOS:  ${CYAN}sudo yum install python3 python3-pip${RESET}"
    echo ""
    echo -e "${BLUE}Or download from: ${MAGENTA}https://www.python.org/downloads/${RESET}"
    exit 1
fi

# Check Python version
PYTHON_VERSION=$(python3 --version 2>&1 | grep -oE '[0-9]+\.[0-9]+' | head -1)
PYTHON_MAJOR=$(echo "$PYTHON_VERSION" | cut -d. -f1)
PYTHON_MINOR=$(echo "$PYTHON_VERSION" | cut -d. -f2)

if [ "$PYTHON_MAJOR" -lt 3 ] || ([ "$PYTHON_MAJOR" -eq 3 ] && [ "$PYTHON_MINOR" -lt 6 ]); then
    echo -e "${RED}❌ Python version $PYTHON_VERSION is too old!${RESET}"
    echo -e "${YELLOW}Moibash requires Python 3.6 or higher.${RESET}"
    echo -e "${YELLOW}Please upgrade Python.${RESET}"
    exit 1
fi
echo -e "${GREEN}✅ Python $PYTHON_VERSION found${RESET}"

# Check pip3
if ! command_exists pip3; then
    echo -e "${YELLOW}⚠️  pip3 is not installed!${RESET}"
    echo -e "${BLUE}Installing pip3...${RESET}"
    if command_exists apt-get; then
        sudo apt-get install -y python3-pip
    elif command_exists yum; then
        sudo yum install -y python3-pip
    elif command_exists brew; then
        brew install python3
    else
        echo -e "${RED}❌ Could not install pip3 automatically.${RESET}"
        echo -e "${YELLOW}Please install pip3 manually.${RESET}"
        exit 1
    fi
fi
echo -e "${GREEN}✅ pip3 found${RESET}"

echo ""
echo -e "${GREEN}${BOLD}✅ All prerequisites met!${RESET}"
echo ""

# Clone repository (only for remote install)
if [ "$IS_LOCAL" = false ]; then
    # Check if moibash is already installed
    if [ -d "$INSTALL_DIR" ]; then
        echo -e "${YELLOW}⚠️  Moibash is already installed at $INSTALL_DIR${RESET}"
        echo -e "${BLUE}Do you want to reinstall? (y/n): ${RESET}"
        read -r response
        if [[ "$response" =~ ^[Yy]$ ]]; then
            echo -e "${BLUE}🗑️  Removing old installation...${RESET}"
            rm -rf "$INSTALL_DIR"
            echo -e "${GREEN}✅ Removed${RESET}"
        else
            echo -e "${YELLOW}Installation cancelled.${RESET}"
            exit 0
        fi
    fi

    echo -e "${BLUE}📥 Downloading moibash from GitHub...${RESET}"
    git clone --depth 1 "$REPO_URL" "$INSTALL_DIR" 2>&1 | grep -E "(Cloning|done)" || true

    if [ ! -d "$INSTALL_DIR" ]; then
        echo -e "${RED}❌ Failed to clone repository!${RESET}"
        exit 1
    fi

    echo -e "${GREEN}✅ Downloaded successfully${RESET}"
    echo ""
else
    echo -e "${GREEN}✅ Using local directory: $INSTALL_DIR${RESET}"
    echo ""
fi

# Check if moibash.sh exists
if [ ! -f "$INSTALL_DIR/moibash.sh" ]; then
    echo -e "${RED}❌ Error: moibash.sh not found in $INSTALL_DIR${RESET}"
    exit 1
fi

# Set permissions
echo -e "${BLUE}📝 Setting up permissions...${RESET}"
chmod +x "$INSTALL_DIR/moibash.sh"
chmod +x "$INSTALL_DIR/router.sh" 2>/dev/null || true
chmod +x "$INSTALL_DIR"/tools/*.sh 2>/dev/null || true
chmod +x "$INSTALL_DIR"/tools/*/*.sh 2>/dev/null || true
chmod +x "$INSTALL_DIR"/tools/*/*.py 2>/dev/null || true
echo -e "${GREEN}✅ Permissions set${RESET}"
echo ""

# Create empty .env file if not exists
ENV_FILE="$INSTALL_DIR/.env"
if [ ! -f "$ENV_FILE" ]; then
    echo -e "${BLUE}📝 Creating .env file...${RESET}"
    touch "$ENV_FILE"
    echo -e "${GREEN}✅ Created${RESET}"
    echo ""
fi

# Create symlink
SUDO=""
if [ ! -w "$BIN_DIR" ]; then
    echo -e "${YELLOW}⚠️  Need sudo privileges to create symlink in $BIN_DIR${RESET}"
    echo -e "${BLUE}Please enter your password:${RESET}"
    SUDO="sudo"
fi

# Remove old symlink if exists
if [ -L "$SYMLINK_PATH" ] || [ -f "$SYMLINK_PATH" ]; then
    echo -e "${YELLOW}⚠️  Found existing symlink at $SYMLINK_PATH${RESET}"
    echo -e "${BLUE}Removing...${RESET}"
    $SUDO rm -f "$SYMLINK_PATH"
fi

# Create new symlink
echo -e "${BLUE}🔗 Creating symlink: $SYMLINK_PATH → $INSTALL_DIR/moibash.sh${RESET}"
$SUDO ln -sf "$INSTALL_DIR/moibash.sh" "$SYMLINK_PATH"

# Verify installation
if [ -L "$SYMLINK_PATH" ] && [ -x "$INSTALL_DIR/moibash.sh" ]; then
    echo ""
    echo -e "${GREEN}${BOLD}╔═══════════════════════════════════════════════════╗${RESET}"
    echo -e "${GREEN}${BOLD}║     INSTALLATION SUCCESSFUL!                      ║${RESET}"
    echo -e "${GREEN}${BOLD}╚═══════════════════════════════════════════════════╝${RESET}"
    echo ""
    echo -e "${GREEN}You can now use moibash from anywhere:${RESET}"
    echo -e "${CYAN}  $ moibash${RESET}"
    echo ""
    echo -e "${BLUE}📁 Installation directory: ${YELLOW}$INSTALL_DIR${RESET}"
    echo -e "${BLUE}🔗 Symlink: ${YELLOW}$SYMLINK_PATH${RESET}"
    echo ""
    echo -e "${MAGENTA}${BOLD}💡 Quick Tips:${RESET}"
    echo -e "  • Start chatting: ${CYAN}moibash${RESET}"
    echo -e "  • Get help: ${CYAN}moibash --help${RESET}"
    echo -e "  • Update: ${CYAN}moibash --update${RESET} or ${CYAN}cd $INSTALL_DIR && git pull${RESET}"
    echo -e "  • Uninstall: ${CYAN}./install.sh --uninstall${RESET}"
    echo ""
    echo -e "${YELLOW}⚠️  First run:${RESET}"
    echo -e "  Moibash will ask for your GEMINI API KEY on first launch."
    echo -e "  Get your free key at: ${MAGENTA}https://makersuite.google.com/app/apikey${RESET}"
    echo ""
    echo -e "${GREEN}${BOLD}Happy chatting! 🚀${RESET}"
    echo ""
else
    echo -e "${RED}❌ Installation failed!${RESET}"
    echo -e "${YELLOW}Please check the error messages above.${RESET}"
    exit 1
fi
