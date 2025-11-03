#!/bin/bash

# searchfiles.sh - Tìm kiếm files

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

search_files() {
    local dir_path="${1:-.}"
    local name_pattern="$2"
    local recursive="${3:-true}"
    
    # Chuyển đổi sang absolute path nếu là relative path
    if [[ "$dir_path" != /* ]]; then
        dir_path="$(pwd)/$dir_path"
    fi
    
    if [ ! -d "$dir_path" ]; then
        echo "{\"error\": \"Thư mục không tồn tại: $dir_path\"}"
        return 1
    fi
    
    # Search files
    local results
    if [ "$recursive" == "true" ]; then
        results=$(find "$dir_path" -type f -name "$name_pattern" 2>/dev/null)
    else
        results=$(find "$dir_path" -maxdepth 1 -type f -name "$name_pattern" 2>/dev/null)
    fi
    
    # Parse results
    if command -v python3 &> /dev/null; then
        echo "$results" | python3 -c "
import sys, json, os

files = []
for line in sys.stdin:
    line = line.strip()
    if line:
        size = os.path.getsize(line) if os.path.exists(line) else 0
        files.append({
            'path': line,
            'name': os.path.basename(line),
            'size': size
        })

result = {
    'files': files,
    'count': len(files),
    'pattern': sys.argv[1],
    'search_path': sys.argv[2]
}
print(json.dumps(result, ensure_ascii=False))
" "$name_pattern" "$dir_path"
    else
        echo "$results"
    fi
}

# Main
search_files "$1" "$2" "$3"