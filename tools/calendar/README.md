# 📅 Calendar Intent - Tính năng Quản lý Lịch

Tích hợp Google Calendar API với Gemini Function Calling để quản lý lịch thông minh.

## ✨ Tính năng

### 1. 🔐 OAuth2 Authentication
- Tạo link đăng nhập Google
- Lưu trữ access token & refresh token
- Tự động refresh token khi hết hạn
- Quản lý session an toàn

### 2. 📋 Quản lý Events
- **Xem lịch**: Truy vấn events theo khoảng thời gian
- **Thêm lịch**: Tạo event mới với đầy đủ thông tin
- **Sửa lịch**: Cập nhật thông tin event có sẵn
- **Xóa lịch**: Xóa events không cần thiết

### 3. 🤖 AI-Powered Function Calling
- Parse ngôn ngữ tự nhiên (tiếng Việt & English)
- Xử lý thời gian thông minh (hôm nay, ngày mai, sáng, chiều, tối)
- Multi-step operations (check → add/delete)
- Conflict detection
- Context-aware responses

## 📁 Cấu trúc

```
tools/calendar/
├── auth.sh            ✅ OAuth2 authentication & token management
├── calendar.sh        ✅ Google Calendar API wrapper
├── function_call.sh   ✅ Gemini Function Calling interface
└── README.md          ✅ Documentation
```

## 🚀 Cài đặt & Thiết lập

### Bước 1: Tạo Google Cloud Project

1. Truy cập [Google Cloud Console](https://console.cloud.google.com/)
2. Tạo project mới hoặc chọn project có sẵn
3. Bật Google Calendar API:
   - Vào **APIs & Services** → **Library**
   - Tìm "Google Calendar API"
   - Click **Enable**

### Bước 2: Tạo OAuth 2.0 Credentials

1. Vào **APIs & Services** → **Credentials**
2. Click **Create Credentials** → **OAuth client ID**
3. Chọn **Application type**: Desktop app
4. Đặt tên (ví dụ: "Moibash Calendar")
5. Download JSON credentials

### Bước 3: Cấu hình trong .env

Thêm vào file `.env` ở root của project:

```bash
# Gemini API (đã có)
GEMINI_API_KEY='your-gemini-api-key'

# Google Calendar OAuth (mới thêm)
GOOGLE_CLIENT_ID='your-client-id-from-credentials.json'
GOOGLE_CLIENT_SECRET='your-client-secret-from-credentials.json'
GOOGLE_REDIRECT_URI='urn:ietf:wg:oauth:2.0:oob'
```

**Lưu ý**: `GOOGLE_REDIRECT_URI='urn:ietf:wg:oauth:2.0:oob'` cho phép copy/paste auth code thủ công.

### Bước 4: Đăng nhập Google Calendar

```bash
./tools/calendar/auth.sh login
```

Flow:
1. Script tạo link đăng nhập
2. Mở link trong trình duyệt
3. Đăng nhập tài khoản Google
4. Authorize app
5. Copy authorization code
6. Paste vào terminal
7. Script tự động lưu tokens

## 💻 Cách sử dụng

### Option 1: Qua Chat Interface (Khuyến nghị)

```bash
./main.sh
```

Sau đó nhập các câu hỏi tự nhiên:

**Tiếng Việt:**
```
➜ lịch trình của tôi hôm nay
➜ thêm lịch đi ăn tối lúc 7h
➜ chiều nay tôi có lịch gì không
➜ xoá các lịch họp sáng nay và thêm lịch đi chơi golf
➜ sửa lịch họp 10h thành 11h
➜ lịch tuần này
```

**English:**
```
➜ what's my schedule today
➜ add meeting at 2pm tomorrow
➜ delete all morning meetings
➜ update my 3pm event to 4pm
```

### Option 2: Qua Router

```bash
./router.sh "lịch trình hôm nay"
```

### Option 3: Trực tiếp Function Calling

```bash
./tools/calendar/function_call.sh "thêm lịch họp team lúc 9h sáng mai"
```

### Option 4: Trực tiếp Calendar API

```bash
# List events
./tools/calendar/calendar.sh list "2024-01-01T00:00:00+07:00" "2024-01-31T23:59:59+07:00" 10

# Add event
./tools/calendar/calendar.sh add "Họp team" "2024-01-15T09:00:00+07:00" "2024-01-15T10:00:00+07:00" "Weekly meeting" "Phòng A"

# Update event
./tools/calendar/calendar.sh update "event_id" "Họp team mới" "" "" "Nội dung mới" ""

# Delete event
./tools/calendar/calendar.sh delete "event_id"
```

## 🎯 Ví dụ cụ thể

### 1. Xem lịch hôm nay

**Input:**
```
lịch trình của tôi hôm nay
```

**AI xử lý:**
- Determine current date
- Call `list_events` với timeMin = hôm nay 00:00, timeMax = hôm nay 23:59
- Format và hiển thị kết quả

**Output:**
```
📅 Lịch trình hôm nay (15/01/2024):

1. 09:00 - 10:00: Họp team
   📍 Phòng A
   
2. 14:00 - 15:00: Meeting với client
   📍 Zoom
   
3. 19:00 - 20:00: Đi ăn tối
   📍 Nhà hàng ABC
```

### 2. Thêm lịch mới

**Input:**
```
thêm lịch đi ăn tối lúc 7h
```

**AI xử lý:**
- Parse "7h" → 19:00
- Call `list_events` để check conflict tại 19:00
- Nếu không conflict, call `add_event`
- Confirm với user

**Output:**
```
✅ Đã thêm lịch thành công!

📅 Đi ăn tối
🕐 19:00 - 20:00 (hôm nay)
```

### 3. Xóa và thêm lịch (multi-step)

**Input:**
```
xoá các lịch họp sáng nay và thêm lịch đi chơi golf
```

**AI xử lý:**
1. Call `list_events` với timeMin = sáng nay 08:00, timeMax = 12:00
2. Tìm các event có "họp" trong title
3. Call `delete_event` cho từng event
4. Call `add_event` cho "Đi chơi golf" vào thời gian sáng
5. Summarize cho user

**Output:**
```
✅ Đã xử lý xong!

❌ Đã xóa 2 lịch họp:
   • 09:00 - 10:00: Họp team
   • 11:00 - 12:00: Họp review

✅ Đã thêm lịch mới:
   • 09:00 - 11:00: Đi chơi golf
```

### 4. Xem lịch chiều nay

**Input:**
```
chiều nay tôi có lịch gì không
```

**AI xử lý:**
- Parse "chiều nay" → 13:00-17:00 hôm nay
- Call `list_events`
- Natural response

**Output:**
```
📅 Chiều nay bạn có 1 lịch:

🕐 14:00 - 15:00: Meeting với client
📍 Zoom
📝 Thảo luận về project mới
```

## 🔧 API Reference

### auth.sh

```bash
# Đăng nhập
./auth.sh login

# Kiểm tra trạng thái
./auth.sh status

# Refresh token
./auth.sh refresh

# Lấy access token (cho scripts)
./auth.sh token

# Đăng xuất
./auth.sh logout

# Hướng dẫn
./auth.sh help
```

### calendar.sh

#### List Events
```bash
./calendar.sh list [time_min] [time_max] [max_results]
```

**Parameters:**
- `time_min`: ISO 8601 format (e.g., `2024-01-15T00:00:00+07:00`)
- `time_max`: ISO 8601 format (optional)
- `max_results`: Số lượng events (mặc định 10)

**Output:**
```json
{
  "events": [
    {
      "id": "abc123",
      "summary": "Họp team",
      "description": "Weekly meeting",
      "start": "2024-01-15T09:00:00+07:00",
      "end": "2024-01-15T10:00:00+07:00",
      "location": "Phòng A",
      "status": "confirmed"
    }
  ],
  "count": 1
}
```

#### Add Event
```bash
./calendar.sh add "summary" "start_time" "end_time" "description" "location"
```

**Output:**
```json
{
  "success": true,
  "id": "abc123",
  "summary": "Họp team",
  "start": "2024-01-15T09:00:00+07:00",
  "end": "2024-01-15T10:00:00+07:00",
  "htmlLink": "https://calendar.google.com/event?..."
}
```

#### Update Event
```bash
./calendar.sh update "event_id" "new_summary" "new_start" "new_end" "new_desc" "new_loc"
```

Để giữ nguyên một field, truyền chuỗi rỗng `""`.

#### Delete Event
```bash
./calendar.sh delete "event_id"
```

**Output:**
```json
{
  "success": true,
  "message": "Đã xóa event thành công"
}
```

### function_call.sh

```bash
./function_call.sh "user message"
```

Tự động xử lý:
- Parse natural language
- Extract actions & parameters
- Call appropriate functions
- Multi-turn conversation
- Generate natural responses

## 🧠 Function Calling Logic

### System Instruction

AI được hướng dẫn:

1. **LUÔN KIỂM TRA LỊCH TRƯỚC** khi add/update/delete
2. Parse thời gian tự nhiên sang ISO 8601
3. Multi-step operations khi cần
4. Xử lý conflict detection
5. Context-aware responses

### Available Functions

1. **get_current_time**: Lấy thời gian hiện tại
2. **list_events**: Xem danh sách events
3. **add_event**: Thêm event mới
4. **update_event**: Sửa event
5. **delete_event**: Xóa event

### Time Parsing

| Ngôn ngữ tự nhiên | ISO 8601 |
|-------------------|----------|
| hôm nay | Current date 00:00-23:59 |
| ngày mai | Tomorrow 00:00-23:59 |
| tuần này | Next 7 days |
| sáng | 08:00-12:00 |
| chiều | 13:00-17:00 |
| tối | 18:00-22:00 |
| lúc 7h | 07:00 or 19:00 (context) |
| 2pm | 14:00 |

### Multi-Step Example

User: "xoá các lịch họp sáng nay và thêm lịch đi chơi golf"

**AI Flow:**
1. Parse: delete "họp" events + add "golf" event
2. Call `get_current_time` → get today's date
3. Call `list_events(today 08:00-12:00)` → find meetings
4. Call `delete_event(meeting_id_1)`
5. Call `delete_event(meeting_id_2)`
6. Call `add_event("Đi chơi golf", today 09:00-11:00)`
7. Generate summary response

## 🔒 Security

### Token Storage

- Tokens lưu trong `tools/calendar/.calendar_token`
- File permission: 600 (chỉ owner đọc/ghi)
- Không commit vào git (đã thêm vào .gitignore)

### Best Practices

- ✅ Sử dụng OAuth 2.0 standard
- ✅ Store tokens locally, not in code
- ✅ Auto refresh expired tokens
- ✅ Minimal scope (chỉ calendar access)
- ❌ Không share tokens
- ❌ Không commit credentials vào git

## 🐛 Troubleshooting

### Lỗi: "Chưa đăng nhập Google Calendar"

**Giải pháp:**
```bash
./tools/calendar/auth.sh login
```

### Lỗi: "Token expired"

**Giải pháp:**
```bash
./tools/calendar/auth.sh refresh
```

Hoặc script tự động refresh.

### Lỗi: "Invalid credentials"

**Kiểm tra:**
1. GOOGLE_CLIENT_ID đúng chưa?
2. GOOGLE_CLIENT_SECRET đúng chưa?
3. Đã enable Calendar API chưa?

### Lỗi: "Access denied"

**Giải pháp:**
1. Kiểm tra OAuth consent screen
2. Thêm email test user (nếu app chưa publish)
3. Re-authorize

## 📊 Thống kê & Giới hạn

### Google Calendar API Limits

- **Free tier**: 1,000,000 requests/day
- **Rate limit**: 10 queries/second/user
- **Batch size**: 1000 requests/batch

### Gemini API Limits

- **Free tier**: 50 requests/day
- **Pro tier**: No limit
- Xem thêm: [Gemini API Pricing](https://ai.google.dev/pricing)

## 🎉 Tính năng nâng cao

### 1. Conflict Detection

Tự động check trùng lịch khi thêm event mới:

```
User: thêm lịch họp lúc 9h
AI: ⚠️ Bạn đã có lịch "Họp team" lúc 9h-10h. Bạn có muốn:
    1. Thay đổi thời gian
    2. Hủy lịch cũ
    3. Giữ cả hai
```

### 2. Smart Time Parsing

Parse các format thời gian khác nhau:
- "7h tối" → 19:00
- "2 giờ chiều" → 14:00
- "9am tomorrow" → 09:00 ngày mai
- "tuần sau thứ 3" → Tuesday next week

### 3. Recurring Events

Support thêm event lặp lại:
```
User: thêm lịch họp team mỗi thứ 2 lúc 9h
AI: Tạo recurring event với RRULE
```

### 4. Reminder Integration

Thêm reminder cho events:
```
User: nhắc tôi trước 15 phút
AI: Set reminder cho event
```

### 5. Multi-Calendar Support

Quản lý nhiều calendar:
```
User: thêm vào calendar công việc
AI: Add to work calendar instead of primary
```

## 📚 References

- [Google Calendar API Documentation](https://developers.google.com/calendar/api)
- [OAuth 2.0 Guide](https://developers.google.com/identity/protocols/oauth2)
- [Gemini Function Calling](https://ai.google.dev/docs/function_calling)

## 🤝 Contributing

Nếu muốn thêm tính năng:

1. Fork repository
2. Tạo branch mới
3. Implement feature
4. Test thoroughly
5. Submit pull request

## 📝 License

MIT License - Sử dụng tự do với attribution.

---

**Tạo bởi**: Moibash Team  
**Version**: 1.0.0  
**Last updated**: 2025-01-02
