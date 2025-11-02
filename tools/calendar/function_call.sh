#!/bin/bash

# function_call.sh - Sử dụng Gemini Function Calling để quản lý Google Calendar
# Flow: User message → Gemini Function Calling → Extract actions → Call calendar API

# Load .env
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
if [ -f "$SCRIPT_DIR/../../.env" ]; then
    set -a
    source "$SCRIPT_DIR/../../.env"
    set +a
fi

USER_MESSAGE="$1"

if [ -z "$USER_MESSAGE" ]; then
    echo "❌ Lỗi: Vui lòng cung cấp câu hỏi về lịch!"
    exit 1
fi

if [ -z "$GEMINI_API_KEY" ]; then
    echo "❌ Lỗi: Chưa thiết lập GEMINI_API_KEY!"
    exit 1
fi

# Kiểm tra xem đã đăng nhập chưa
if ! "$SCRIPT_DIR/auth.sh" status > /dev/null 2>&1; then
    echo "❌ Chưa đăng nhập Google Calendar"
    echo "💡 Vui lòng chạy: ./tools/calendar/auth.sh login"
    exit 1
fi

# Escape message for JSON
escape_json() {
    echo "$1" | python3 -c "import sys, json; print(json.dumps(sys.stdin.read().strip()))" 2>/dev/null | sed 's/^"//;s/"$//'
}

escaped_message=$(escape_json "$USER_MESSAGE")

# System instruction cho function calling
SYSTEM_INSTRUCTION="Bạn là trợ lý quản lý lịch thông minh.

KHI XỬ LÝ YÊU CẦU:
1. LUÔN KIỂM TRA LỊCH HIỆN TẠI TRƯỚC khi thêm/xóa/sửa
2. Với yêu cầu XÓA: list_events trước, tìm event phù hợp, sau đó delete_event
3. Với yêu cầu THÊM: list_events trước để kiểm tra conflict, sau đó add_event
4. Với yêu cầu SỬA: list_events để tìm event, sau đó update_event
5. Parse thời gian tự nhiên sang ISO 8601 format (timezone +07:00)
6. Nếu không có giờ cụ thể, mặc định dùng giờ hợp lý

THỜI GIAN:
- 'hôm nay', 'today' → ngày hiện tại
- 'ngày mai', 'tomorrow' → ngày tiếp theo
- 'tuần này', 'this week' → 7 ngày tới
- 'sáng' → 08:00-12:00
- 'chiều' → 13:00-17:00
- 'tối' → 18:00-22:00

VÍ DỤ XỬ LÝ:
User: 'lịch trình hôm nay'
→ Call: list_events với timeMin=hôm nay 00:00, timeMax=hôm nay 23:59

User: 'thêm lịch đi ăn tối lúc 7h'
→ Step 1: list_events kiểm tra 19:00-20:00
→ Step 2: add_event('Đi ăn tối', '19:00', '20:00')

User: 'xóa lịch họp sáng nay'
→ Step 1: list_events sáng nay (08:00-12:00)
→ Step 2: Tìm event có 'họp' trong title
→ Step 3: delete_event(event_id)

User: 'xoá các lịch họp sáng nay và thêm lịch đi chơi golf'
→ Step 1: list_events sáng nay
→ Step 2: delete_event cho các event 'họp'
→ Step 3: add_event('Đi chơi golf', thời gian sáng)

HÃY GỌI FUNCTION THEO THỨ TỰ HỢP LÝ!

QUAN TRỌNG - KHI TRẢ LỜI USER:
- LUÔN HIỂN thị TOÀN BỘ thông tin chi tiết của từng event
- Với mỗi event, hiển thị: Tiêu đề, Thời gian, Địa điểm (nếu có), Mô tả (nếu có)
- Định dạng dễ đọc và rõ ràng
- KHÔNG được chỉ nói 'có X lịch' mà phải liệt kê chi tiết tất cả

VÍ DỤ OUTPUT TỐT:
User: 'lịch trình ngày mai'
→ Response: 'Lịch trình ngày mai của bạn:

1. 📅 Họp team
   ⏰ 09:00 - 10:00
   📍 Phòng họp A
   📝 Review dự án tuần

2. 📅 Lunch với khách hàng  
   ⏰ 12:00 - 13:30
   📍 Nhà hàng ABC
   
Tổng cộng: 2 sự kiện'"

# Function declarations
FUNCTION_DECLARATIONS='[
    {
        "name": "list_events",
        "description": "Lấy danh sách events từ Google Calendar trong khoảng thời gian. LUÔN GỌI FUNCTION NÀY TRƯỚC KHI ADD/UPDATE/DELETE để kiểm tra lịch hiện tại.",
        "parameters": {
            "type": "object",
            "properties": {
                "time_min": {
                    "type": "string",
                    "description": "Thời gian bắt đầu (ISO 8601 format, ví dụ: 2024-01-15T00:00:00+07:00)"
                },
                "time_max": {
                    "type": "string",
                    "description": "Thời gian kết thúc (ISO 8601 format, ví dụ: 2024-01-15T23:59:59+07:00)"
                },
                "max_results": {
                    "type": "integer",
                    "description": "Số lượng event tối đa (mặc định 10)"
                }
            },
            "required": ["time_min"]
        }
    },
    {
        "name": "add_event",
        "description": "Thêm event mới vào Google Calendar. GỌI list_events TRƯỚC để kiểm tra conflict.",
        "parameters": {
            "type": "object",
            "properties": {
                "summary": {
                    "type": "string",
                    "description": "Tiêu đề event"
                },
                "start_time": {
                    "type": "string",
                    "description": "Thời gian bắt đầu (ISO 8601 format)"
                },
                "end_time": {
                    "type": "string",
                    "description": "Thời gian kết thúc (ISO 8601 format, optional)"
                },
                "description": {
                    "type": "string",
                    "description": "Mô tả chi tiết (optional)"
                },
                "location": {
                    "type": "string",
                    "description": "Địa điểm (optional)"
                }
            },
            "required": ["summary", "start_time"]
        }
    },
    {
        "name": "update_event",
        "description": "Cập nhật thông tin event có sẵn. GỌI list_events TRƯỚC để lấy event_id.",
        "parameters": {
            "type": "object",
            "properties": {
                "event_id": {
                    "type": "string",
                    "description": "ID của event cần update (lấy từ list_events)"
                },
                "summary": {
                    "type": "string",
                    "description": "Tiêu đề mới (optional)"
                },
                "start_time": {
                    "type": "string",
                    "description": "Thời gian bắt đầu mới (ISO 8601, optional)"
                },
                "end_time": {
                    "type": "string",
                    "description": "Thời gian kết thúc mới (ISO 8601, optional)"
                },
                "description": {
                    "type": "string",
                    "description": "Mô tả mới (optional)"
                },
                "location": {
                    "type": "string",
                    "description": "Địa điểm mới (optional)"
                }
            },
            "required": ["event_id"]
        }
    },
    {
        "name": "delete_event",
        "description": "Xóa event khỏi Google Calendar. GỌI list_events TRƯỚC để lấy event_id cần xóa.",
        "parameters": {
            "type": "object",
            "properties": {
                "event_id": {
                    "type": "string",
                    "description": "ID của event cần xóa (lấy từ list_events)"
                }
            },
            "required": ["event_id"]
        }
    },
    {
        "name": "get_current_time",
        "description": "Lấy thời gian hiện tại để tính toán timeMin/timeMax. Sử dụng khi cần xác định hôm nay, ngày mai, etc.",
        "parameters": {
            "type": "object",
            "properties": {
                "format": {
                    "type": "string",
                    "description": "Format mong muốn: iso8601, date, datetime"
                }
            }
        }
    }
]'

# Hàm get current time
get_current_time_impl() {
    local format="${1:-iso8601}"
    
    if command -v python3 &> /dev/null; then
        python3 -c "
from datetime import datetime
import json
import sys

format_arg = sys.argv[1] if len(sys.argv) > 1 else 'iso8601'
now = datetime.now()

if format_arg == 'iso8601':
    result = now.strftime('%Y-%m-%dT%H:%M:%S+07:00')
elif format_arg == 'date':
    result = now.strftime('%Y-%m-%d')
else:
    result = now.strftime('%Y-%m-%d %H:%M:%S')

print(json.dumps({'time': result, 'timestamp': int(now.timestamp())}))
" "$format"
    else
        local time=$(date '+%Y-%m-%dT%H:%M:%S+07:00')
        echo "{\"time\": \"$time\"}"
    fi
}

# Hàm xử lý function call
handle_function_call() {
    local func_name="$1"
    local args="$2"
    
    case "$func_name" in
        list_events)
            if command -v python3 &> /dev/null; then
                local params=$(echo "$args" | python3 -c "
import sys, json
try:
    args = json.load(sys.stdin)
    time_min = args.get('time_min', '')
    time_max = args.get('time_max', '')
    max_results = args.get('max_results', 10)
    print(f'{time_min}|{time_max}|{max_results}')
except:
    print('||10')
" 2>/dev/null)
                IFS='|' read -r time_min time_max max_results <<< "$params"
                "$SCRIPT_DIR/calendar.sh" list "$time_min" "$time_max" "$max_results"
            fi
            ;;
            
        add_event)
            if command -v python3 &> /dev/null; then
                local params=$(echo "$args" | python3 -c "
import sys, json
try:
    args = json.load(sys.stdin)
    summary = args.get('summary', '')
    start_time = args.get('start_time', '')
    end_time = args.get('end_time', '')
    description = args.get('description', '')
    location = args.get('location', '')
    print(f'{summary}|{start_time}|{end_time}|{description}|{location}')
except:
    print('||||')
" 2>/dev/null)
                IFS='|' read -r summary start_time end_time description location <<< "$params"
                "$SCRIPT_DIR/calendar.sh" add "$summary" "$start_time" "$end_time" "$description" "$location"
            fi
            ;;
            
        update_event)
            if command -v python3 &> /dev/null; then
                local params=$(echo "$args" | python3 -c "
import sys, json
try:
    args = json.load(sys.stdin)
    event_id = args.get('event_id', '')
    summary = args.get('summary', '')
    start_time = args.get('start_time', '')
    end_time = args.get('end_time', '')
    description = args.get('description', '')
    location = args.get('location', '')
    print(f'{event_id}|{summary}|{start_time}|{end_time}|{description}|{location}')
except:
    print('|||||')
" 2>/dev/null)
                IFS='|' read -r event_id summary start_time end_time description location <<< "$params"
                "$SCRIPT_DIR/calendar.sh" update "$event_id" "$summary" "$start_time" "$end_time" "$description" "$location"
            fi
            ;;
            
        delete_event)
            if command -v python3 &> /dev/null; then
                local event_id=$(echo "$args" | python3 -c "
import sys, json
try:
    args = json.load(sys.stdin)
    print(args.get('event_id', ''))
except:
    print('')
" 2>/dev/null)
                "$SCRIPT_DIR/calendar.sh" delete "$event_id"
            fi
            ;;
            
        get_current_time)
            if command -v python3 &> /dev/null; then
                local format=$(echo "$args" | python3 -c "
import sys, json
try:
    args = json.load(sys.stdin)
    print(args.get('format', 'iso8601'))
except:
    print('iso8601')
" 2>/dev/null)
                get_current_time_impl "$format"
            else
                get_current_time_impl "iso8601"
            fi
            ;;
            
        *)
            echo "{\"error\": \"Unknown function: $func_name\"}"
            ;;
    esac
}

# Build conversation history
conversation='[{"role": "user", "parts": [{"text": "'"$escaped_message"'"}]}]'
tool_calls_made=0
max_iterations=10

# Multi-turn conversation loop
while [ $tool_calls_made -lt $max_iterations ]; do
    # Gọi Gemini API
    response=$(curl -s -X POST \
        "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key=$GEMINI_API_KEY" \
        -H 'Content-Type: application/json' \
        -d "{
          \"contents\": $conversation,
          \"tools\": [{\"functionDeclarations\": $FUNCTION_DECLARATIONS}],
          \"systemInstruction\": {\"parts\": [{\"text\": \"$SYSTEM_INSTRUCTION\"}]}
        }")
    
    # Parse response để kiểm tra có function call không
    if command -v python3 &> /dev/null; then
        parse_result=$(echo "$response" | python3 -c "
import sys, json
try:
    data = json.load(sys.stdin)
    candidates = data.get('candidates', [])
    
    if not candidates:
        print('NO_RESPONSE')
        sys.exit(0)
    
    content = candidates[0].get('content', {})
    parts = content.get('parts', [])
    
    # Kiểm tra function call
    for part in parts:
        if 'functionCall' in part:
            func_call = part['functionCall']
            func_name = func_call.get('name', '')
            args = json.dumps(func_call.get('args', {}))
            print(f'FUNCTION_CALL|{func_name}|{args}')
            sys.exit(0)
    
    # Kiểm tra text response
    for part in parts:
        if 'text' in part:
            print(f'TEXT|{part[\"text\"]}')
            sys.exit(0)
    
    print('NO_RESPONSE')
except Exception as e:
    print(f'ERROR|{str(e)}')
" 2>/dev/null)
    else
        parse_result="ERROR|No python3 available"
    fi
    
    IFS='|' read -r result_type result_value result_extra <<< "$parse_result"
    
    case "$result_type" in
        FUNCTION_CALL)
            tool_calls_made=$((tool_calls_made + 1))
            
            # Execute function
            func_result=$(handle_function_call "$result_value" "$result_extra")
            
            # DEBUG: Show function result
            # echo "[DEBUG] Function: $result_value" >&2
            # echo "[DEBUG] Result: $func_result" >&2
            
            # Add function call và response vào conversation
            if command -v python3 &> /dev/null; then
                # Create temp files to safely pass data
                temp_dir=$(mktemp -d 2>/dev/null || mktemp -d -t 'calendar_tmp')
                echo "$conversation" > "$temp_dir/conversation.json"
                echo "$result_value" > "$temp_dir/func_name.txt"
                echo "$result_extra" > "$temp_dir/func_args.json"
                echo "$func_result" > "$temp_dir/func_result.json"
                
                # Create Python script
                cat > "$temp_dir/process.py" <<'PYEOF'
import sys, json

# Read data from files
with open(sys.argv[1], 'r') as f:
    conversation = json.load(f)
with open(sys.argv[2], 'r') as f:
    func_name = f.read().strip()
with open(sys.argv[3], 'r') as f:
    func_args_str = f.read().strip()
with open(sys.argv[4], 'r') as f:
    func_result_str = f.read().strip()

# Parse function arguments
try:
    func_args = json.loads(func_args_str)
except Exception as e:
    func_args = {}

# Add model response with function call
conversation.append({
    'role': 'model',
    'parts': [{
        'functionCall': {
            'name': func_name,
            'args': func_args
        }
    }]
})

# Parse function result
try:
    func_result_json = json.loads(func_result_str)
except:
    func_result_json = {'result': func_result_str}

# Add function response
conversation.append({
    'role': 'function',
    'parts': [{
        'functionResponse': {
            'name': func_name,
            'response': {
                'content': func_result_json
            }
        }
    }]
})

print(json.dumps(conversation))
PYEOF
                
                # Run Python script
                conversation=$(python3 "$temp_dir/process.py" "$temp_dir/conversation.json" "$temp_dir/func_name.txt" "$temp_dir/func_args.json" "$temp_dir/func_result.json")
                
                # Cleanup
                rm -rf "$temp_dir"
            fi
            
            # Continue loop để Gemini xử lý function response
            continue
            ;;
            
        TEXT)
            # Final response từ Gemini
            echo "$result_value"
            exit 0
            ;;
            
        NO_RESPONSE)
            echo "❌ Không nhận được phản hồi từ AI"
            exit 1
            ;;
            
        ERROR)
            echo "❌ Lỗi: $result_value"
            exit 1
            ;;
    esac
done

echo "⚠️ Đã đạt giới hạn số lượng function calls ($max_iterations)"
exit 1
