#!/bin/bash

# createfile.sh - Tạo file mới

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

create_file() {
    local file_path="$1"
    local content="$2"
    
    if [ -z "$file_path" ]; then
        echo "{\"error\": \"Đường dẫn file là bắt buộc\"}"
        return 1
    fi
    
    # Chuyển đổi sang absolute path nếu là relative path
    if [[ "$file_path" != /* ]]; then
        file_path="$(pwd)/$file_path"
    fi
    
    if [ -f "$file_path" ]; then
        echo "{\"error\": \"File đã tồn tại: $file_path\"}"
        return 1
    fi
    
    # Tạo thư mục cha nếu chưa tồn tại
    local dir_path=$(dirname "$file_path")
    mkdir -p "$dir_path" 2>/dev/null
    
    # Tạo file với nội dung
    echo "$content" > "$file_path" 2>/dev/null
    
    if [ $? -eq 0 ]; then
        echo "{\"success\": true, \"path\": \"$file_path\", \"message\": \"Đã tạo file thành công\"}"
    else
        echo "{\"error\": \"Không thể tạo file: $file_path\"}"
        return 1
    fi
}

# Main
create_file "$1" "$2"