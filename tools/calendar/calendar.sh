#!/bin/bash

# calendar.sh - Tương tác với Google Calendar API
# Hỗ trợ: list, add, update, delete events

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

# Hàm lấy access token
get_token() {
    local result=$("$SCRIPT_DIR/auth.sh" token)
    IFS='|' read -r status token <<< "$result"
    
    if [ "$status" == "SUCCESS" ]; then
        echo "$token"
        return 0
    else
        echo "❌ Lỗi: $token" >&2
        echo "💡 Vui lòng chạy: ./tools/calendar/auth.sh login" >&2
        return 1
    fi
}

# Hàm parse ISO datetime sang định dạng dễ đọc
parse_datetime() {
    local iso_date="$1"
    # Chuyển đổi ISO 8601 sang định dạng dễ đọc
    if command -v python3 &> /dev/null; then
        echo "$iso_date" | python3 -c "
import sys
from datetime import datetime
try:
    dt = datetime.fromisoformat(sys.stdin.read().strip().replace('Z', '+00:00'))
    print(dt.strftime('%Y-%m-%d %H:%M'))
except:
    print(sys.stdin.read().strip())
" 2>/dev/null
    else
        # Fallback: hiển thị raw
        echo "$iso_date"
    fi
}

# Hàm list events
list_events() {
    local time_min="$1"  # ISO 8601 format
    local time_max="$2"  # ISO 8601 format
    local max_results="${3:-10}"
    
    local token
    token=$(get_token) || return 1
    
    # Build query parameters
    local url="https://www.googleapis.com/calendar/v3/calendars/primary/events"
    url="${url}?orderBy=startTime&singleEvents=true&maxResults=${max_results}"
    
    if [ ! -z "$time_min" ]; then
        # URL encode the time_min (replace + with %2B, : with %3A)
        local encoded_time_min=$(echo "$time_min" | sed 's/+/%2B/g; s/:/%3A/g')
        url="${url}&timeMin=${encoded_time_min}"
    fi
    
    if [ ! -z "$time_max" ]; then
        # URL encode the time_max (replace + with %2B, : with %3A)
        local encoded_time_max=$(echo "$time_max" | sed 's/+/%2B/g; s/:/%3A/g')
        url="${url}&timeMax=${encoded_time_max}"
    fi
    
    # Gọi API
    local response=$(curl -s -X GET "$url" \
        -H "Authorization: Bearer $token" \
        -H "Accept: application/json")
    
    # Parse và format response
    if command -v python3 &> /dev/null; then
        echo "$response" | python3 -c "
import sys, json
try:
    data = json.load(sys.stdin)
    
    if 'error' in data:
        error_msg = data['error'].get('message', 'Unknown error')
        print(json.dumps({'error': error_msg}))
        sys.exit(0)
    
    items = data.get('items', [])
    
    events = []
    for item in items:
        event = {
            'id': item.get('id', ''),
            'summary': item.get('summary', 'No title'),
            'description': item.get('description', ''),
            'start': item.get('start', {}).get('dateTime', item.get('start', {}).get('date', '')),
            'end': item.get('end', {}).get('dateTime', item.get('end', {}).get('date', '')),
            'location': item.get('location', ''),
            'status': item.get('status', ''),
        }
        events.append(event)
    
    result = {
        'events': events,
        'count': len(events)
    }
    
    print(json.dumps(result, ensure_ascii=False))
except Exception as e:
    print(json.dumps({'error': str(e)}))
" 2>/dev/null
    else
        # Fallback
        echo "$response"
    fi
}

# Hàm add event
add_event() {
    local summary="$1"
    local start_time="$2"  # ISO 8601
    local end_time="$3"    # ISO 8601
    local description="$4"
    local location="$5"
    
    if [ -z "$summary" ] || [ -z "$start_time" ]; then
        echo "{\"error\": \"summary và start_time là bắt buộc\"}"
        return 1
    fi
    
    local token
    token=$(get_token) || return 1
    
    # Nếu không có end_time, mặc định là 1 giờ sau start_time
    if [ -z "$end_time" ]; then
        if command -v python3 &> /dev/null; then
            end_time=$(echo "$start_time" | python3 -c "
import sys
from datetime import datetime, timedelta
try:
    dt = datetime.fromisoformat(sys.stdin.read().strip().replace('Z', '+00:00'))
    end_dt = dt + timedelta(hours=1)
    print(end_dt.isoformat())
except:
    print('')
" 2>/dev/null)
        fi
        
        if [ -z "$end_time" ]; then
            end_time="$start_time"
        fi
    fi
    
    # Build request body using python for proper JSON escaping
    if command -v python3 &> /dev/null; then
        local request_body=$(python3 -c "
import json
import sys

data = {
    'summary': sys.argv[1],
    'start': {
        'dateTime': sys.argv[2],
        'timeZone': 'Asia/Ho_Chi_Minh'
    },
    'end': {
        'dateTime': sys.argv[3],
        'timeZone': 'Asia/Ho_Chi_Minh'
    }
}

if len(sys.argv) > 4 and sys.argv[4]:
    data['description'] = sys.argv[4]
if len(sys.argv) > 5 and sys.argv[5]:
    data['location'] = sys.argv[5]

print(json.dumps(data, ensure_ascii=False))
" "$summary" "$start_time" "$end_time" "$description" "$location" 2>/dev/null)
    else
        # Fallback: basic escaping
        local escaped_summary=$(echo "$summary" | sed 's/"/\\"/g')
        local escaped_desc=$(echo "$description" | sed 's/"/\\"/g')
        local escaped_loc=$(echo "$location" | sed 's/"/\\"/g')
        
        local request_body="{
            \"summary\": \"$escaped_summary\",
            \"start\": {
                \"dateTime\": \"$start_time\",
                \"timeZone\": \"Asia/Ho_Chi_Minh\"
            },
            \"end\": {
                \"dateTime\": \"$end_time\",
                \"timeZone\": \"Asia/Ho_Chi_Minh\"
            }"
        
        if [ ! -z "$description" ]; then
            request_body="${request_body},\"description\": \"$escaped_desc\""
        fi
        
        if [ ! -z "$location" ]; then
            request_body="${request_body},\"location\": \"$escaped_loc\""
        fi
        
        request_body="${request_body}}"
    fi
    
    # Gọi API
    local response=$(curl -s -X POST \
        "https://www.googleapis.com/calendar/v3/calendars/primary/events" \
        -H "Authorization: Bearer $token" \
        -H "Content-Type: application/json" \
        -d "$request_body")
    
    # Parse response
    if command -v python3 &> /dev/null; then
        echo "$response" | python3 -c "
import sys, json
try:
    data = json.load(sys.stdin)
    
    if 'error' in data:
        error_msg = data['error'].get('message', 'Unknown error')
        print(json.dumps({'error': error_msg}))
    else:
        result = {
            'success': True,
            'id': data.get('id', ''),
            'summary': data.get('summary', ''),
            'start': data.get('start', {}).get('dateTime', ''),
            'end': data.get('end', {}).get('dateTime', ''),
            'htmlLink': data.get('htmlLink', '')
        }
        print(json.dumps(result, ensure_ascii=False))
except Exception as e:
    print(json.dumps({'error': str(e)}))
" 2>/dev/null
    else
        echo "$response"
    fi
}

# Hàm update event
update_event() {
    local event_id="$1"
    local summary="$2"
    local start_time="$3"
    local end_time="$4"
    local description="$5"
    local location="$6"
    
    if [ -z "$event_id" ]; then
        echo "{\"error\": \"event_id là bắt buộc\"}"
        return 1
    fi
    
    local token
    token=$(get_token) || return 1
    
    # Lấy thông tin event hiện tại
    local current_event=$(curl -s -X GET \
        "https://www.googleapis.com/calendar/v3/calendars/primary/events/${event_id}" \
        -H "Authorization: Bearer $token")
    
    # Build request body (giữ nguyên các field không update)
    if command -v python3 &> /dev/null; then
        local request_body=$(echo "$current_event" | python3 -c "
import sys, json
try:
    data = json.load(sys.stdin)
    
    if 'error' in data:
        print('{}')
        sys.exit(0)
    
    # Update các field nếu được cung cấp
    if '$summary':
        data['summary'] = '$summary'
    if '$start_time':
        data['start'] = {'dateTime': '$start_time', 'timeZone': 'Asia/Ho_Chi_Minh'}
    if '$end_time':
        data['end'] = {'dateTime': '$end_time', 'timeZone': 'Asia/Ho_Chi_Minh'}
    if '$description':
        data['description'] = '$description'
    if '$location':
        data['location'] = '$location'
    
    print(json.dumps(data))
except:
    print('{}')
" 2>/dev/null)
    else
        echo "{\"error\": \"Cần python3 để update event\"}"
        return 1
    fi
    
    if [ "$request_body" == "{}" ]; then
        echo "{\"error\": \"Không tìm thấy event hoặc lỗi khi parse\"}"
        return 1
    fi
    
    # Gọi API update
    local response=$(curl -s -X PUT \
        "https://www.googleapis.com/calendar/v3/calendars/primary/events/${event_id}" \
        -H "Authorization: Bearer $token" \
        -H "Content-Type: application/json" \
        -d "$request_body")
    
    # Parse response
    if command -v python3 &> /dev/null; then
        echo "$response" | python3 -c "
import sys, json
try:
    data = json.load(sys.stdin)
    
    if 'error' in data:
        error_msg = data['error'].get('message', 'Unknown error')
        print(json.dumps({'error': error_msg}))
    else:
        result = {
            'success': True,
            'id': data.get('id', ''),
            'summary': data.get('summary', ''),
            'updated': data.get('updated', '')
        }
        print(json.dumps(result, ensure_ascii=False))
except Exception as e:
    print(json.dumps({'error': str(e)}))
" 2>/dev/null
    else
        echo "$response"
    fi
}

# Hàm delete event
delete_event() {
    local event_id="$1"
    
    if [ -z "$event_id" ]; then
        echo "{\"error\": \"event_id là bắt buộc\"}"
        return 1
    fi
    
    local token
    token=$(get_token) || return 1
    
    # Gọi API delete
    local response=$(curl -s -X DELETE \
        "https://www.googleapis.com/calendar/v3/calendars/primary/events/${event_id}" \
        -H "Authorization: Bearer $token" \
        -w "\nHTTP_CODE:%{http_code}")
    
    # Parse response
    local http_code=$(echo "$response" | grep "HTTP_CODE:" | sed 's/HTTP_CODE://')
    
    if [ "$http_code" == "204" ] || [ "$http_code" == "200" ]; then
        echo "{\"success\": true, \"message\": \"Đã xóa event thành công\"}"
    else
        echo "{\"error\": \"Không thể xóa event. HTTP code: $http_code\"}"
        return 1
    fi
}

# Main command handler
case "${1:-help}" in
    list)
        # ./calendar.sh list [time_min] [time_max] [max_results]
        list_events "$2" "$3" "$4"
        ;;
        
    add)
        # ./calendar.sh add "summary" "start_time" "end_time" "description" "location"
        add_event "$2" "$3" "$4" "$5" "$6"
        ;;
        
    update)
        # ./calendar.sh update "event_id" "summary" "start_time" "end_time" "description" "location"
        update_event "$2" "$3" "$4" "$5" "$6" "$7"
        ;;
        
    delete)
        # ./calendar.sh delete "event_id"
        delete_event "$2"
        ;;
        
    help|*)
        cat << 'EOF'
📅 Google Calendar Tool

Cách sử dụng:

1. List events:
   ./calendar.sh list [time_min] [time_max] [max_results]
   
   Ví dụ:
   ./calendar.sh list "2024-01-01T00:00:00+07:00" "2024-01-31T23:59:59+07:00" 10

2. Add event:
   ./calendar.sh add "summary" "start_time" "end_time" "description" "location"
   
   Ví dụ:
   ./calendar.sh add "Họp team" "2024-01-15T09:00:00+07:00" "2024-01-15T10:00:00+07:00" "Họp weekly" "Phòng A"

3. Update event:
   ./calendar.sh update "event_id" "summary" "start_time" "end_time" "description" "location"
   
   Ví dụ:
   ./calendar.sh update "abc123" "Họp team mới" "" "" "Nội dung mới" ""

4. Delete event:
   ./calendar.sh delete "event_id"
   
   Ví dụ:
   ./calendar.sh delete "abc123"

Ghi chú:
- Thời gian phải ở định dạng ISO 8601: YYYY-MM-DDTHH:MM:SS+07:00
- Để giữ nguyên một field khi update, truyền chuỗi rỗng ""

EOF
        ;;
esac
