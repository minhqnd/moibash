#!/bin/bash

# processtool.sh - Thực thi các lệnh hệ thống
# Hỗ trợ: run_command - chạy lệnh shell bất kỳ

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

run_command() {
    local command="$1"
    local working_dir="${2:-$(pwd)}"
    
    if [ -z "$command" ]; then
        echo "{\"error\": \"Lệnh không được để trống\"}"
        return 1
    fi
    
    # Validate working directory
    if [ ! -d "$working_dir" ]; then
        working_dir="$(pwd)"
    fi
    
    # Chuyển đến working directory
    cd "$working_dir" 2>/dev/null
    
    # Thực thi lệnh
    local output
    local exit_code
    
    # Chạy lệnh và capture output
    output=$($command 2>&1)
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
" "$output" "$exit_code" "$command" "$working_dir"
    else
        echo "{\"success\": $([ $exit_code -eq 0 ] && echo 'true' || echo 'false'), \"output\": \"$output\", \"exit_code\": $exit_code, \"command\": \"$command\", \"working_dir\": \"$working_dir\"}"
    fi
}

# Main
run_command "$1" "$2"
