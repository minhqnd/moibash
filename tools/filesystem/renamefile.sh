#!/bin/bash

# renamefile.sh - Đổi tên file/folder

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

rename_file() {
    local old_path="$1"
    local new_path="$2"
    
    if [ -z "$old_path" ] || [ -z "$new_path" ]; then
        echo "{\"error\": \"Cần cung cấp đường dẫn cũ và mới\"}"
        return 1
    fi
    
    # Chuyển đổi sang absolute path nếu là relative path
    if [[ "$old_path" != /* ]]; then
        old_path="$(pwd)/$old_path"
    fi
    if [[ "$new_path" != /* ]]; then
        new_path="$(pwd)/$new_path"
    fi
    
    if [ ! -e "$old_path" ]; then
        echo "{\"error\": \"File/folder không tồn tại: $old_path\"}"
        return 1
    fi
    
    if [ -e "$new_path" ]; then
        echo "{\"error\": \"File/folder đích đã tồn tại: $new_path\"}"
        return 1
    fi
    
    # Đổi tên
    mv "$old_path" "$new_path" 2>/dev/null
    
    if [ $? -eq 0 ]; then
        echo "{\"success\": true, \"old_path\": \"$old_path\", \"new_path\": \"$new_path\", \"message\": \"Đã đổi tên thành công\"}"
    else
        echo "{\"error\": \"Không thể đổi tên từ $old_path sang $new_path\"}"
        return 1
    fi
}

# Main
rename_file "$1" "$2"