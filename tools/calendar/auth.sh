#!/bin/bash

# auth.sh - Xử lý OAuth2 cho Google Calendar API
# Tạo link đăng nhập và lưu token

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
TOKEN_FILE="$SCRIPT_DIR/.calendar_token"
CREDENTIALS_FILE="$SCRIPT_DIR/.credentials"

# Load .env để lấy credentials
if [ -f "$SCRIPT_DIR/../../.env" ]; then
    set -a
    source "$SCRIPT_DIR/../../.env"
    set +a
fi

# Hàm hiển thị hướng dẫn setup
show_setup_instructions() {
    cat << 'EOF'
📅 Hướng dẫn thiết lập Google Calendar API

1️⃣ Tạo Google Cloud Project:
   • Truy cập: https://console.cloud.google.com/
   • Tạo project mới hoặc chọn project có sẵn

2️⃣ Bật Google Calendar API:
   • Vào "APIs & Services" > "Library"
   • Tìm "Google Calendar API" và Enable

3️⃣ Tạo OAuth 2.0 Credentials:
   • Vào "APIs & Services" > "Credentials"
   • Click "Create Credentials" > "OAuth client ID"
   • Application type: "Desktop app"
   • Download JSON credentials

4️⃣ Cấu hình credentials:
   • Thêm vào file .env:
     GOOGLE_CLIENT_ID='your-client-id'
     GOOGLE_CLIENT_SECRET='your-client-secret'
     GOOGLE_REDIRECT_URI='http://localhost:8080'

5️⃣ Chạy authentication:
   ./tools/calendar/auth.sh login

EOF
}

# Hàm tạo URL đăng nhập
generate_auth_url() {
    if [ -z "$GOOGLE_CLIENT_ID" ]; then
        echo "❌ Lỗi: GOOGLE_CLIENT_ID chưa được thiết lập trong .env"
        echo ""
        show_setup_instructions
        exit 1
    fi

    # Redirect URI (có thể dùng localhost hoặc urn:ietf:wg:oauth:2.0:oob cho manual copy)
    local redirect_uri="${GOOGLE_REDIRECT_URI:-urn:ietf:wg:oauth:2.0:oob}"
    
    # Scope cho Google Calendar
    local scope="https://www.googleapis.com/auth/calendar"
    
    # URL encode scope
    local encoded_scope=$(echo "$scope" | sed 's/ /%20/g')
    local encoded_redirect=$(echo "$redirect_uri" | sed 's/:/%3A/g' | sed 's/\//%2F/g')
    
    # Tạo auth URL
    local auth_url="https://accounts.google.com/o/oauth2/v2/auth"
    auth_url="${auth_url}?client_id=${GOOGLE_CLIENT_ID}"
    auth_url="${auth_url}&redirect_uri=${encoded_redirect}"
    auth_url="${auth_url}&response_type=code"
    auth_url="${auth_url}&scope=${encoded_scope}"
    auth_url="${auth_url}&access_type=offline"
    auth_url="${auth_url}&prompt=consent"
    
    echo "$auth_url"
}

# Hàm đổi authorization code lấy tokens
exchange_code_for_tokens() {
    local auth_code="$1"
    
    if [ -z "$auth_code" ]; then
        echo "❌ Lỗi: Authorization code không được để trống"
        exit 1
    fi
    
    if [ -z "$GOOGLE_CLIENT_ID" ] || [ -z "$GOOGLE_CLIENT_SECRET" ]; then
        echo "❌ Lỗi: GOOGLE_CLIENT_ID hoặc GOOGLE_CLIENT_SECRET chưa được thiết lập"
        exit 1
    fi
    
    local redirect_uri="${GOOGLE_REDIRECT_URI:-urn:ietf:wg:oauth:2.0:oob}"
    
    echo "🔄 Đang đổi authorization code lấy tokens..."
    
    # Gọi token endpoint
    local response=$(curl -s -X POST "https://oauth2.googleapis.com/token" \
        -H "Content-Type: application/x-www-form-urlencoded" \
        -d "code=${auth_code}" \
        -d "client_id=${GOOGLE_CLIENT_ID}" \
        -d "client_secret=${GOOGLE_CLIENT_SECRET}" \
        -d "redirect_uri=${redirect_uri}" \
        -d "grant_type=authorization_code")
    
    # Parse response
    if command -v python3 &> /dev/null; then
        local parse_result=$(echo "$response" | python3 -c "
import sys, json
try:
    data = json.load(sys.stdin)
    if 'error' in data:
        print(f\"ERROR|{data.get('error_description', data['error'])}\")
    elif 'access_token' in data:
        print(f\"SUCCESS|{data['access_token']}|{data.get('refresh_token', '')}|{data.get('expires_in', 3600)}\")
    else:
        print('ERROR|Invalid response from Google')
except Exception as e:
    print(f'ERROR|{str(e)}')
" 2>/dev/null)
    else
        # Fallback parsing
        if echo "$response" | grep -q '"access_token"'; then
            local access_token=$(echo "$response" | grep -o '"access_token"[[:space:]]*:[[:space:]]*"[^"]*"' | sed 's/.*"access_token"[[:space:]]*:[[:space:]]*"//;s/".*//')
            local refresh_token=$(echo "$response" | grep -o '"refresh_token"[[:space:]]*:[[:space:]]*"[^"]*"' | sed 's/.*"refresh_token"[[:space:]]*:[[:space:]]*"//;s/".*//')
            parse_result="SUCCESS|${access_token}|${refresh_token}|3600"
        else
            parse_result="ERROR|Failed to parse response"
        fi
    fi
    
    IFS='|' read -r status access_token refresh_token expires_in <<< "$parse_result"
    
    if [ "$status" == "SUCCESS" ]; then
        # Lưu tokens với proper escaping
        local current_time=$(date +%s)
        local expiry_time=$((current_time + expires_in))
        
        # Create token file with secure writing
        touch "$TOKEN_FILE"
        chmod 600 "$TOKEN_FILE"
        printf 'ACCESS_TOKEN=%s\n' "$(printf '%q' "$access_token")" > "$TOKEN_FILE"
        printf 'REFRESH_TOKEN=%s\n' "$(printf '%q' "$refresh_token")" >> "$TOKEN_FILE"
        printf 'EXPIRY_TIME=%s\n' "$expiry_time" >> "$TOKEN_FILE"
        
        echo "✅ Đã lưu tokens thành công!"
        echo "📁 File: $TOKEN_FILE"
        return 0
    else
        echo "❌ Lỗi: $access_token"
        return 1
    fi
}

# Hàm refresh access token
refresh_access_token() {
    if [ ! -f "$TOKEN_FILE" ]; then
        echo "❌ Lỗi: Chưa có token. Vui lòng chạy: ./auth.sh login"
        return 1
    fi
    
    source "$TOKEN_FILE"
    
    if [ -z "$REFRESH_TOKEN" ]; then
        echo "❌ Lỗi: Không có refresh token. Vui lòng đăng nhập lại."
        return 1
    fi
    
    echo "🔄 Đang refresh access token..."
    
    local response=$(curl -s -X POST "https://oauth2.googleapis.com/token" \
        -H "Content-Type: application/x-www-form-urlencoded" \
        -d "refresh_token=${REFRESH_TOKEN}" \
        -d "client_id=${GOOGLE_CLIENT_ID}" \
        -d "client_secret=${GOOGLE_CLIENT_SECRET}" \
        -d "grant_type=refresh_token")
    
    # Parse response
    if command -v python3 &> /dev/null; then
        local parse_result=$(echo "$response" | python3 -c "
import sys, json
try:
    data = json.load(sys.stdin)
    if 'error' in data:
        print(f\"ERROR|{data.get('error_description', data['error'])}\")
    elif 'access_token' in data:
        print(f\"SUCCESS|{data['access_token']}|{data.get('expires_in', 3600)}\")
    else:
        print('ERROR|Invalid response')
except Exception as e:
    print(f'ERROR|{str(e)}')
" 2>/dev/null)
    else
        if echo "$response" | grep -q '"access_token"'; then
            local new_access_token=$(echo "$response" | grep -o '"access_token"[[:space:]]*:[[:space:]]*"[^"]*"' | sed 's/.*"access_token"[[:space:]]*:[[:space:]]*"//;s/".*//')
            parse_result="SUCCESS|${new_access_token}|3600"
        else
            parse_result="ERROR|Failed to parse response"
        fi
    fi
    
    IFS='|' read -r status new_access_token new_expires_in <<< "$parse_result"
    
    if [ "$status" == "SUCCESS" ]; then
        # Cập nhật token file với proper escaping
        local current_time=$(date +%s)
        local expiry_time=$((current_time + new_expires_in))
        
        # Update token file with secure writing
        printf 'ACCESS_TOKEN=%s\n' "$(printf '%q' "$new_access_token")" > "$TOKEN_FILE"
        printf 'REFRESH_TOKEN=%s\n' "$(printf '%q' "$REFRESH_TOKEN")" >> "$TOKEN_FILE"
        printf 'EXPIRY_TIME=%s\n' "$expiry_time" >> "$TOKEN_FILE"
        
        echo "✅ Đã refresh token thành công!"
        return 0
    else
        echo "❌ Lỗi refresh token: $new_access_token"
        return 1
    fi
}

# Hàm lấy valid access token
get_access_token() {
    if [ ! -f "$TOKEN_FILE" ]; then
        echo "ERROR|No token file. Please run: ./auth.sh login"
        return 1
    fi
    
    source "$TOKEN_FILE"
    
    local current_time=$(date +%s)
    
    # Kiểm tra xem token đã hết hạn chưa (trừ 60s để an toàn)
    if [ $((current_time + 60)) -ge "$EXPIRY_TIME" ]; then
        # Token hết hạn, cần refresh
        if ! refresh_access_token > /dev/null 2>&1; then
            echo "ERROR|Failed to refresh token"
            return 1
        fi
        source "$TOKEN_FILE"
    fi
    
    echo "SUCCESS|$ACCESS_TOKEN"
    return 0
}

# Hàm kiểm tra token status
check_token_status() {
    if [ ! -f "$TOKEN_FILE" ]; then
        echo "❌ Chưa đăng nhập"
        echo "💡 Chạy: ./tools/calendar/auth.sh login"
        return 1
    fi
    
    source "$TOKEN_FILE"
    
    local current_time=$(date +%s)
    local remaining=$((EXPIRY_TIME - current_time))
    
    echo "✅ Đã đăng nhập"
    echo "📅 Token hết hạn sau: $((remaining / 60)) phút"
    
    if [ "$remaining" -lt 300 ]; then
        echo "⚠️ Token sắp hết hạn, đang refresh..."
        refresh_access_token
    fi
    
    return 0
}

# Main command handler
case "${1:-help}" in
    login)
        echo "📅 Đăng nhập Google Calendar"
        echo "============================"
        echo ""
        
        # Tạo auth URL
        auth_url=$(generate_auth_url)
        
        echo "🔗 Mở link sau trong trình duyệt để đăng nhập:"
        echo ""
        echo "$auth_url"
        echo ""
        echo "📋 Sau khi đăng nhập, bạn sẽ nhận được authorization code."
        echo "📝 Nhập authorization code vào đây:"
        read -p "Authorization code: " auth_code
        
        if [ ! -z "$auth_code" ]; then
            exchange_code_for_tokens "$auth_code"
        else
            echo "❌ Authorization code không được để trống"
            exit 1
        fi
        ;;
        
    refresh)
        refresh_access_token
        ;;
        
    status)
        check_token_status
        ;;
        
    token)
        # Lấy token để sử dụng trong scripts khác
        get_access_token
        ;;
        
    logout)
        if [ -f "$TOKEN_FILE" ]; then
            rm "$TOKEN_FILE"
            echo "✅ Đã đăng xuất thành công"
        else
            echo "ℹ️ Chưa đăng nhập"
        fi
        ;;
        
    help|*)
        cat << 'EOF'
📅 Google Calendar Authentication Tool

Cách sử dụng:
  ./auth.sh login    - Đăng nhập và lưu token
  ./auth.sh status   - Kiểm tra trạng thái đăng nhập
  ./auth.sh refresh  - Refresh access token
  ./auth.sh token    - Lấy access token hiện tại
  ./auth.sh logout   - Đăng xuất (xóa token)
  ./auth.sh help     - Hiển thị hướng dẫn

Lần đầu sử dụng:
  1. Setup Google Cloud credentials trong .env
  2. Chạy: ./auth.sh login
  3. Làm theo hướng dẫn để authorize

EOF
        if [ "${1}" != "help" ]; then
            echo ""
            show_setup_instructions
        fi
        ;;
esac
