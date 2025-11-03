#!/bin/bash

# listfiles.sh - Liệt kê files trong thư mục

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

list_files() {
    local dir_path="${1:-.}"
    local pattern="${2:-*}"
    local recursive="${3:-false}"
    
    # Chuyển đổi sang absolute path nếu là relative path
    if [[ "$dir_path" != /* ]]; then
        dir_path="$(pwd)/$dir_path"
    fi
    
    if [ ! -d "$dir_path" ]; then
        echo "{\"error\": \"Thư mục không tồn tại: $dir_path\"}"
        return 1
    fi
    
    # List files
    if command -v python3 &> /dev/null; then
        python3 -c "
import os, json, sys, glob

dir_path = sys.argv[1]
pattern = sys.argv[2]
recursive = sys.argv[3] == 'true'

files = []
folders = []

try:
    if recursive:
        # Tìm kiếm đệ quy
        for root, dirs, filenames in os.walk(dir_path):
            for filename in filenames:
                if pattern == '*' or filename.endswith(pattern.replace('*', '')):
                    full_path = os.path.join(root, filename)
                    size = os.path.getsize(full_path)
                    files.append({'name': filename, 'path': full_path, 'size': size})
            for dirname in dirs:
                full_path = os.path.join(root, dirname)
                folders.append({'name': dirname, 'path': full_path})
    else:
        # Chỉ list thư mục hiện tại
        for item in os.listdir(dir_path):
            full_path = os.path.join(dir_path, item)
            if os.path.isfile(full_path):
                if pattern == '*' or item.endswith(pattern.replace('*', '')):
                    size = os.path.getsize(full_path)
                    files.append({'name': item, 'path': full_path, 'size': size})
            elif os.path.isdir(full_path):
                folders.append({'name': item, 'path': full_path})
    
    result = {
        'files': files,
        'folders': folders,
        'file_count': len(files),
        'folder_count': len(folders),
        'path': dir_path
    }
    print(json.dumps(result, ensure_ascii=False))
except Exception as e:
    print(json.dumps({'error': str(e)}, ensure_ascii=False))
" "$dir_path" "$pattern" "$recursive"
    else
        # Fallback
        echo "{\"error\": \"Cần python3 để list files\"}"
        return 1
    fi
}

# Main
list_files "$1" "$2" "$3"