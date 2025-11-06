#!/bin/bash

# intent.sh - Phân loại intent của user message
# Sử dụng Gemini để phân loại: chat, image_create, google_search

# Load .env
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
if [ -f "$SCRIPT_DIR/../.env" ]; then
    set -a
    source "$SCRIPT_DIR/../.env"
    set +a
fi

USER_MESSAGE="$1"

if [ -z "$USER_MESSAGE" ]; then
    echo "chat"
    exit 0
fi

# System instruction để phân loại intent
SYSTEM_INSTRUCTION="Bạn là một intent classifier. Phân loại câu hỏi của user vào 1 trong 7 loại:

1. filesystem: BẤT KỲ YÊU CẦU NÀO về thao tác với file/folder trên hệ thống
   - Tạo file: 'tạo file', 'create file', 'viết file'
   - Đọc file: 'đọc file', 'xem file', 'hiển thị nội dung'
   - Sửa file: 'sửa file', 'đổi tên file', 'rename', 'chỉnh sửa'
   - Xóa file: 'xóa file', 'delete file', 'remove'
   - Chạy code: 'chạy file', 'thực thi', 'run code', 'execute'
   - Liệt kê: 'list file', 'bao nhiêu file', 'đếm file', 'tìm file'

2. calendar: BẤT KỲ YÊU CẦU NÀO về lịch, lịch trình, sự kiện, cuộc họp, hẹn gặp
   - Xem lịch: 'lịch trình hôm nay', 'lịch tuần này', 'có hẹn gì không'
   - Thêm lịch: 'thêm lịch họp', 'tạo event', 'đặt hẹn'
   - Sửa/xóa lịch: 'xóa lịch họp', 'hủy cuộc hẹn', 'dời lịch'

3. weather: Hỏi về thời tiết, nhiệt độ, mưa nắng tại một địa điểm cụ thể
   - 'thời tiết', 'nhiệt độ', 'trời có mưa không'

4. image_create: Yêu cầu tạo ảnh, vẽ ảnh, generate image
   - 'vẽ', 'tạo ảnh', 'generate image'

5. music: BẤT KỲ YÊU CẦU NÀO liên quan đến âm nhạc, phát bài hát, nghe nhạc, hoặc tra cứu ca sĩ, album
   - Phát nhạc: 'phát bài', 'nghe bài', 'nghe nhạc', 'play song'
   - Tra cứu: 'ai hát bài', 'tác giả bài', 'album của', 'bài hát của ca sĩ'
   - Dừng phát: 'stop', 'dừng nhạc', 'pause'

6. google_search: Cần thông tin thời gian thực, tin tức, sự kiện mới nhất
   - 'tin tức', 'tìm kiếm', 'thông tin về'

7. chat: Các câu hỏi thông thường khác, trò chuyện, hỏi đáp kiến thức chung

QUAN TRỌNG: 
- Ưu tiên filesystem nếu có từ khóa: file, folder, tạo, xóa, sửa, đổi tên, chạy, execute, list, đếm, tìm kiếm file
- Ưu tiên calendar nếu có từ khóa: lịch, lịch trình, event, họp, hẹn, cuộc họp, appointment, meeting, schedule
- Ưu tiên music nếu có từ khóa: phát, nghe, nhạc, bài hát, itunes, album, ca sĩ, tác giả, stop, dừng

CHỈ TRẢ VỀ MỘT TRONG BẢY TỪ SAU: filesystem, calendar, weather, image_create, music, google_search, chat
KHÔNG GIẢI THÍCH GÌ CẢ, CHỈ TRẢ VỀ ĐÚNG MỘT TỪ KHÓA"

# Escape message
escaped_message=$(echo "$USER_MESSAGE" | sed 's/\\/\\\\/g' | sed 's/"/\\"/g')

# Gọi API để classify
response=$(curl -s -X POST \
    "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent?key=$GEMINI_API_KEY" \
    -H 'Content-Type: application/json' \
    -d "{
      \"contents\": [{
        \"parts\": [{\"text\": \"$escaped_message\"}]
      }],
      \"systemInstruction\": {
        \"parts\": [{\"text\": \"$SYSTEM_INSTRUCTION\"}]
      },
      \"generationConfig\": {
        \"temperature\": 0.1,
        \"maxOutputTokens\": 10
      }
    }")

# Parse intent bằng python
if command -v python3 &> /dev/null; then
    intent=$(echo "$response" | python3 -c "
import sys, json, re
try:
    data = json.load(sys.stdin)
    
    # Kiểm tra lỗi API (quota exceeded, etc.)
    if 'error' in data:
        # Fallback: Phân loại dựa trên từ khóa trong message
        message = '''$USER_MESSAGE'''.lower()
        
        # Filesystem keywords - kiểm tra trước
        if any(word in message for word in ['file', 'folder', 'tạo file', 'tao file', 'create file', 'xóa file', 'xoa file', 'delete file', 'đọc file', 'doc file', 'read file', 'sửa file', 'sua file', 'edit file', 'đổi tên', 'doi ten', 'rename', 'chạy', 'chay', 'run', 'execute', 'thực thi', 'thuc thi', 'bao nhiêu file', 'bao nhieu file', 'đếm file', 'dem file', 'list file', 'tìm file', 'tim file', 'search file']):
            print('filesystem')
        # Calendar keywords
        elif any(word in message for word in ['lịch', 'lich', 'schedule', 'event', 'họp', 'hop', 'hẹn', 'hen', 'meeting', 'appointment', 'cuộc họp', 'lịch trình']):
            print('calendar')
        # Weather keywords
        elif any(word in message for word in ['thời tiết', 'thoi tiet', 'weather', 'nhiệt độ', 'nhiet do', 'temperature', 'mưa', 'mua', 'rain', 'nắng', 'nang', 'sunny']):
            print('weather')
        # Image keywords
        elif any(word in message for word in ['vẽ', 've', 'draw', 'tạo ảnh', 'tao anh', 'create image', 'generate image', 'ảnh', 'anh', 'image']):
            print('image_create')
        # Music keywords
        elif any(word in message for word in ['phát', 'phat', 'nghe', 'nhạc', 'nhac', 'bài hát', 'bai hat', 'itunes', 'music', 'album', 'ca sĩ', 'ca si', 'tác giả', 'tac gia', 'stop', 'dừng', 'dung']):
            print('music')
        # Search keywords
        elif any(word in message for word in ['tìm kiếm', 'tim kiem', 'search', 'tin tức', 'tin tuc', 'news', 'thông tin', 'thong tin', 'information']):
            print('google_search')
        else:
            print('chat')
    else:
        # Parse response từ API
        text = data['candidates'][0]['content']['parts'][0]['text'].strip().lower()
        # Lấy intent từ text
        if 'filesystem' in text:
            print('filesystem')
        elif 'calendar' in text:
            print('calendar')
        elif 'weather' in text:
            print('weather')
        elif 'image_create' in text or 'image' in text:
            print('image_create')
        elif 'music' in text:
            print('music')
        elif 'google_search' in text or 'search' in text:
            print('google_search')
        else:
            print('chat')
except Exception as e:
    # Fallback nếu có lỗi parse
    message = '''$USER_MESSAGE'''.lower()
    
    if any(word in message for word in ['file', 'folder', 'tạo file', 'tao file', 'create file', 'xóa file', 'xoa file', 'delete file', 'đọc file', 'doc file', 'read file', 'sửa file', 'sua file', 'edit file', 'đổi tên', 'doi ten', 'rename', 'chạy', 'chay', 'run', 'execute', 'thực thi', 'thuc thi', 'bao nhiêu file', 'bao nhieu file', 'đếm file', 'dem file', 'list file', 'tìm file', 'tim file', 'search file']):
        print('filesystem')
    elif any(word in message for word in ['lịch', 'lich', 'schedule', 'event', 'họp', 'hop', 'hẹn', 'hen', 'meeting', 'appointment', 'cuộc họp', 'lịch trình']):
        print('calendar')
    elif any(word in message for word in ['thời tiết', 'thoi tiet', 'weather', 'nhiệt độ', 'nhiet do', 'temperature', 'mưa', 'mua', 'rain', 'nắng', 'nang', 'sunny']):
        print('weather')
    elif any(word in message for word in ['vẽ', 've', 'draw', 'tạo ảnh', 'tao anh', 'create image', 'generate image', 'ảnh', 'anh', 'image']):
        print('image_create')
    elif any(word in message for word in ['phát', 'phat', 'nghe', 'nhạc', 'nhac', 'bài hát', 'bai hat', 'itunes', 'music', 'album', 'ca sĩ', 'ca si', 'tác giả', 'tac gia', 'stop', 'dừng', 'dung']):
        print('music')
    elif any(word in message for word in ['tìm kiếm', 'tim kiem', 'search', 'tin tức', 'tin tuc', 'news', 'thông tin', 'thong tin', 'information']):
        print('google_search')
    else:
        print('chat')
" 2>/dev/null)
else
    # Fallback: parse bằng grep hoặc keyword matching
    intent=$(echo "$response" | grep -o '"text"[[:space:]]*:[[:space:]]*"[^"]*"' | head -1 | sed 's/.*"text"[[:space:]]*:[[:space:]]*"//;s/".*//' | tr -d '\n' | tr '[:upper:]' '[:lower:]')
    
    # Nếu không parse được, dùng keyword matching
    if [ -z "$intent" ] || [[ "$response" == *"error"* ]]; then
        message_lower=$(echo "$USER_MESSAGE" | tr '[:upper:]' '[:lower:]')
        
        if [[ "$message_lower" =~ (file|folder|tạo\ file|tao\ file|xóa\ file|xoa\ file|đọc\ file|doc\ file|sửa\ file|sua\ file|đổi\ tên|doi\ ten|rename|chạy|chay|run|execute|bao\ nhiêu\ file|đếm\ file|list\ file|tìm\ file) ]]; then
            intent="filesystem"
        elif [[ "$message_lower" =~ (lịch|lich|schedule|event|họp|hop|hẹn|hen|meeting|appointment|lịch\ trình) ]]; then
            intent="calendar"
        elif [[ "$message_lower" =~ (thời\ tiết|thoi\ tiet|weather|nhiệt\ độ|nhiet\ do|mưa|mua|rain|nắng|nang) ]]; then
            intent="weather"
        elif [[ "$message_lower" =~ (phát|phat|nghe|nhạc|nhac|bài[[:space:]]?hát|bai[[:space:]]?hat|itunes|music|album|ca[[:space:]]?sĩ|ca[[:space:]]?si|tác[[:space:]]?giả|tac[[:space:]]?gia|thông[[:space:]]?tin\ bài|thong[[:space:]]?tin\ bai|phát\ bài|play) ]]; then
            intent="music"    
        elif [[ "$message_lower" =~ (vẽ|ve|draw|tạo\ ảnh|tao\ anh|image|ảnh|anh) ]]; then
            intent="image_create"
        elif [[ "$message_lower" =~ (tìm\ kiếm|tim\ kiem|search|tin\ tức|tin\ tuc|news) ]]; then
            intent="google_search"
        else
            intent="chat"
        fi
    else
        # Parse intent từ API response
        if [[ "$intent" == *"filesystem"* ]]; then
            intent="filesystem"
        elif [[ "$intent" == *"calendar"* ]]; then
            intent="calendar"
        elif [[ "$intent" == *"weather"* ]]; then
            intent="weather"
        elif [[ "$intent" == *"image"* ]]; then
            intent="image_create"
        elif [[ "$intent" == *"music"* ]]; then
            intent="music"    
        elif [[ "$intent" == *"search"* ]]; then
            intent="google_search"
        else
            intent="chat"
        fi
    fi
fi

# Đảm bảo intent hợp lệ
case "$intent" in
    filesystem|image_create|google_search|weather|calendar|music|chat)
        echo "$intent"
        ;;
    *)
        echo "chat"
        ;;
esac
