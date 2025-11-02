#!/bin/bash

# filesystem.sh - Thao tác với file hệ thống
# Hỗ trợ: read, create, update, delete, execute, list, search

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

# Hàm đọc file
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

# Hàm tạo file
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

# Hàm cập nhật file (ghi đè hoặc append)
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

# Hàm xóa file
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

# Hàm đổi tên file/folder
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

# Hàm thực thi file
execute_file() {
    local file_path="$1"
    local args="$2"
    local working_dir="${3:-$(pwd)}"
    
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
    
    # Xác định interpreter dựa trên extension
    local ext="${file_path##*.}"
    local interpreter=""
    
    case "$ext" in
        py)
            interpreter="python3"
            ;;
        sh)
            interpreter="bash"
            ;;
        js)
            interpreter="node"
            ;;
        *)
            # Nếu không có extension phù hợp, thử chmod +x và chạy trực tiếp
            if [ ! -x "$file_path" ]; then
                chmod +x "$file_path" 2>/dev/null
                if [ $? -ne 0 ]; then
                    echo "{\"error\": \"File không có quyền thực thi và không xác định được interpreter\"}"
                    return 1
                fi
            fi
            ;;
    esac
    
    # Thực thi file
    cd "$working_dir" 2>/dev/null || cd "$(dirname "$file_path")"
    
    local output
    local exit_code
    
    if [ ! -z "$interpreter" ]; then
        output=$($interpreter "$file_path" $args 2>&1)
        exit_code=$?
    else
        output=$("$file_path" $args 2>&1)
        exit_code=$?
    fi
    
    # Trả về kết quả
    if command -v python3 &> /dev/null; then
        python3 -c "
import sys, json
output = sys.argv[1]
exit_code = int(sys.argv[2])
result = {
    'success': exit_code == 0,
    'output': output,
    'exit_code': exit_code,
    'path': sys.argv[3]
}
print(json.dumps(result, ensure_ascii=False))
" "$output" "$exit_code" "$file_path"
    else
        echo "{\"success\": $([ $exit_code -eq 0 ] && echo 'true' || echo 'false'), \"output\": \"$output\", \"exit_code\": $exit_code, \"path\": \"$file_path\"}"
    fi
}

# Hàm list files trong thư mục
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

# Hàm search files
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

# Main command handler
case "${1:-help}" in
    read)
        # ./filesystem.sh read "/path/to/file"
        read_file "$2"
        ;;
        
    create)
        # ./filesystem.sh create "/path/to/file" "content"
        create_file "$2" "$3"
        ;;
        
    update)
        # ./filesystem.sh update "/path/to/file" "content" "mode"
        update_file "$2" "$3" "$4"
        ;;
        
    delete)
        # ./filesystem.sh delete "/path/to/file"
        delete_file "$2"
        ;;
        
    rename)
        # ./filesystem.sh rename "/old/path" "/new/path"
        rename_file "$2" "$3"
        ;;
        
    execute)
        # ./filesystem.sh execute "/path/to/file" "args" "working_dir"
        execute_file "$2" "$3" "$4"
        ;;
        
    list)
        # ./filesystem.sh list "/path/to/dir" "pattern" "recursive"
        list_files "$2" "$3" "$4"
        ;;
        
    search)
        # ./filesystem.sh search "/path/to/dir" "pattern" "recursive"
        search_files "$2" "$3" "$4"
        ;;
        
    help|*)
        cat << 'EOF'
📁 Filesystem Tool

Cách sử dụng:

1. Read file:
   ./filesystem.sh read "/path/to/file"

2. Create file:
   ./filesystem.sh create "/path/to/file" "content"

3. Update file:
   ./filesystem.sh update "/path/to/file" "content" "overwrite|append"

4. Delete file/folder:
   ./filesystem.sh delete "/path/to/file"

5. Rename file/folder:
   ./filesystem.sh rename "/old/path" "/new/path"

6. Execute file:
   ./filesystem.sh execute "/path/to/file" "args" "working_dir"

7. List files:
   ./filesystem.sh list "/path/to/dir" "pattern" "recursive"

8. Search files:
   ./filesystem.sh search "/path/to/dir" "pattern" "recursive"

EOF
        ;;
esac
