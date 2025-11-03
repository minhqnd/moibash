#!/bin/bash

# updatefile.sh - Cập nhật nội dung file

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

update_file() {
    local file_path="$1"
    local content="$2"
    local mode="${3:-overwrite}"  # overwrite hoặc append
    
    if [ -z "$file_path" ]; then
        echo "{\"error\": \"Đường dẫn file là bắt buộc\"}"
        return 1
    fi
    
    # Chuyển đổi sang absolute path nếu là relative path
    if [[ "$file_path" != /* ]]; then
        file_path="$(pwd)/$file_path"
    fi
    
    if [ ! -f "$file_path" ]; then
        echo "{\"error\": \"File không tồn tại: $file_path\"}"
        return 1
    fi
    
    if [ ! -w "$file_path" ]; then
        echo "{\"error\": \"Không có quyền ghi file: $file_path\"}"
        return 1
    fi
    
    # Cập nhật file
    if [ "$mode" == "append" ]; then
        echo "$content" >> "$file_path" 2>/dev/null
    else
        echo "$content" > "$file_path" 2>/dev/null
    fi
    
    if [ $? -eq 0 ]; then
        echo "{\"success\": true, \"path\": \"$file_path\", \"message\": \"Đã cập nhật file thành công\"}"
    else
        echo "{\"error\": \"Không thể cập nhật file: $file_path\"}"
        return 1
    fi
}

# Main
update_file "$1" "$2" "$3"