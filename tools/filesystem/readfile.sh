#!/bin/bash

# readfile.sh - Đọc nội dung file

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

read_file() {
    local file_path="$1"
    
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
    
    if [ ! -r "$file_path" ]; then
        echo "{\"error\": \"Không có quyền đọc file: $file_path\"}"
        return 1
    fi
    
    # Đọc nội dung file
    local content=$(cat "$file_path" | python3 -c "
import sys, json
content = sys.stdin.read()
print(json.dumps({'content': content, 'path': sys.argv[1], 'size': len(content)}, ensure_ascii=False))
" "$file_path" 2>/dev/null)
    
    if [ $? -eq 0 ]; then
        echo "$content"
    else
        # Fallback
        echo "{\"content\": \"$(cat "$file_path")\", \"path\": \"$file_path\"}"
    fi
}

# Main
read_file "$1"