#!/bin/bash

# deletefile.sh - Xóa file hoặc folder

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

delete_file() {
    local file_path="$1"
    
    if [ -z "$file_path" ]; then
        echo "{\"error\": \"Đường dẫn file là bắt buộc\"}"
        return 1
    fi
    
    # Chuyển đổi sang absolute path nếu là relative path
    if [[ "$file_path" != /* ]]; then
        file_path="$(pwd)/$file_path"
    fi
    
    if [ ! -e "$file_path" ]; then
        echo "{\"error\": \"File/folder không tồn tại: $file_path\"}"
        return 1
    fi
    
    # Xóa file hoặc folder
    if [ -d "$file_path" ]; then
        rm -rf "$file_path" 2>/dev/null
    else
        rm -f "$file_path" 2>/dev/null
    fi
    
    if [ $? -eq 0 ]; then
        echo "{\"success\": true, \"path\": \"$file_path\", \"message\": \"Đã xóa thành công\"}"
    else
        echo "{\"error\": \"Không thể xóa: $file_path\"}"
        return 1
    fi
}

# Main
delete_file "$1"