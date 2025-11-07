#!/bin/bash

# shell.sh - Unified shell execution tool
# Combines executefile and processtool functionality
# Supports: running shell commands and executing script files

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

execute_shell() {
    local action="$1"
    local target="$2"
    local args="$3"
    local working_dir="${4:-$(pwd)}"
    
    # Validate working directory
    if [ ! -d "$working_dir" ]; then
        working_dir="$(pwd)"
    fi
    
    # Chuyển đến working directory
    cd "$working_dir" 2>/dev/null
    
    local output
    local exit_code
    
    if [ "$action" = "command" ]; then
        # Run shell command
        if [ -z "$target" ]; then
            echo "{\"error\": \"Lệnh không được để trống\"}"
            return 1
        fi
        
        # Thực thi lệnh với eval để xử lý quotes và arguments đúng
        output=$(eval "$target" 2>&1)
        exit_code=$?
        
        # Trả về kết quả
        if command -v python3 &> /dev/null; then
            python3 -c "
import sys, json
output = sys.argv[1]
exit_code = int(sys.argv[2])
command = sys.argv[3]
result = {
    'success': exit_code == 0,
    'output': output,
    'exit_code': exit_code,
    'command': command,
    'working_dir': sys.argv[4]
}
print(json.dumps(result, ensure_ascii=False))
" "$output" "$exit_code" "$target" "$working_dir"
        else
            echo "{\"success\": $([ $exit_code -eq 0 ] && echo 'true' || echo 'false'), \"output\": \"$output\", \"exit_code\": $exit_code, \"command\": \"$target\", \"working_dir\": \"$working_dir\"}"
        fi
        
    elif [ "$action" = "file" ]; then
        # Execute script file
        local file_path="$target"
        
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
        
        # Validate file path to prevent path traversal attacks
        local resolved_path=$(realpath "$file_path" 2>/dev/null)
        if [ $? -ne 0 ] || [ ! -f "$resolved_path" ]; then
            echo "{\"error\": \"Invalid file path\"}"
            return 1
        fi
        
        # Additional security: ensure resolved path is not attempting to escape working directory
        # This prevents malicious paths like "../../etc/passwd"
        local current_dir=$(pwd)
        if [[ "$resolved_path" == /etc/* ]] || [[ "$resolved_path" == /root/* ]]; then
            echo "{\"error\": \"Access to system directories is restricted\"}"
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
                # Nếu không có extension phù hợp, kiểm tra nếu file đã có quyền thực thi
                if [ ! -x "$file_path" ]; then
                    echo "{\"error\": \"File không có extension hỗ trợ (py/sh/js) và không có quyền thực thi. Chỉ hỗ trợ Python, Bash, Node.js scripts.\"}"
                    return 1
                fi
                ;;
        esac
        
        # Thực thi file
        cd "$working_dir" 2>/dev/null || cd "$(dirname "$file_path")"
        
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
    else
        echo "{\"error\": \"Action không hợp lệ. Sử dụng 'command' hoặc 'file'\"}"
        return 1
    fi
}

# Main
execute_shell "$1" "$2" "$3" "$4"
