# 📅 Calendar Tool - Quick Reference

## 🚀 Quick Start (3 bước)

### 1. Setup Google Cloud
```bash
# Truy cập: https://console.cloud.google.com/
# 1. Tạo project mới
# 2. Enable "Google Calendar API"
# 3. Tạo OAuth 2.0 credentials (Desktop app)
# 4. Download credentials
```

### 2. Cấu hình .env
```bash
echo "GOOGLE_CLIENT_ID='your-client-id'" >> .env
echo "GOOGLE_CLIENT_SECRET='your-client-secret'" >> .env
echo "GOOGLE_REDIRECT_URI='urn:ietf:wg:oauth:2.0:oob'" >> .env
```

### 3. Đăng nhập & Sử dụng
```bash
# Đăng nhập
./tools/calendar/auth.sh login

# Chạy chat
./main.sh

# Hỏi về lịch
➜ lịch trình của tôi hôm nay
➜ thêm lịch đi ăn tối lúc 7h
```

## 💬 Câu hỏi mẫu

### Xem lịch:
```
✓ lịch trình của tôi hôm nay
✓ lịch tuần này
✓ chiều nay tôi có lịch gì không
✓ what's my schedule today
✓ show me events this week
```

### Thêm lịch:
```
✓ thêm lịch đi ăn tối lúc 7h
✓ thêm lịch họp team lúc 9h sáng mai
✓ add meeting at 2pm tomorrow
✓ tạo lịch đi chơi golf chiều thứ 7
```

### Xóa lịch:
```
✓ xóa lịch họp 10h
✓ xóa tất cả lịch sáng nay
✓ delete my 3pm meeting
✓ xoá các lịch họp sáng nay
```

### Sửa lịch:
```
✓ sửa lịch 10h thành 11h
✓ đổi lịch họp sang chiều
✓ update my 2pm event to 3pm
```

### Multi-step (nâng cao):
```
✓ xoá các lịch họp sáng nay và thêm lịch đi chơi golf
✓ hủy lịch chiều và thêm lịch đi ăn tối
✓ delete morning meetings and add gym session
```

## 🔧 Commands

### Auth Commands
```bash
# Đăng nhập
./tools/calendar/auth.sh login

# Kiểm tra trạng thái
./tools/calendar/auth.sh status

# Refresh token
./tools/calendar/auth.sh refresh

# Đăng xuất
./tools/calendar/auth.sh logout
```

### Direct API Commands
```bash
# List events hôm nay
./tools/calendar/calendar.sh list \
  "2024-01-15T00:00:00+07:00" \
  "2024-01-15T23:59:59+07:00" \
  10

# Add event
./tools/calendar/calendar.sh add \
  "Họp team" \
  "2024-01-15T09:00:00+07:00" \
  "2024-01-15T10:00:00+07:00" \
  "Weekly meeting" \
  "Phòng A"

# Update event
./tools/calendar/calendar.sh update \
  "event_id" \
  "Title mới" \
  "" "" "" ""

# Delete event
./tools/calendar/calendar.sh delete "event_id"
```

### Function Calling
```bash
# Via function_call.sh
./tools/calendar/function_call.sh "lịch của tôi hôm nay"

# Via router
./router.sh "thêm lịch đi ăn tối lúc 7h"

# Via main interface (khuyến nghị)
./main.sh
```

## 📋 Time Parsing

| Ngôn ngữ tự nhiên | Thời gian |
|-------------------|-----------|
| hôm nay / today | Ngày hiện tại |
| ngày mai / tomorrow | Ngày tiếp theo |
| tuần này / this week | 7 ngày tới |
| sáng / morning | 08:00-12:00 |
| chiều / afternoon | 13:00-17:00 |
| tối / evening | 18:00-22:00 |
| lúc 7h | 07:00 hoặc 19:00 |
| 2pm | 14:00 |
| 9am | 09:00 |

## 🔑 Environment Variables

```bash
# .env file
GEMINI_API_KEY='your-gemini-api-key'
GOOGLE_CLIENT_ID='your-client-id'
GOOGLE_CLIENT_SECRET='your-client-secret'
GOOGLE_REDIRECT_URI='urn:ietf:wg:oauth:2.0:oob'
```

## 📁 Files

```
tools/calendar/
├── auth.sh           # OAuth authentication
├── calendar.sh       # API wrapper
├── function_call.sh  # Function calling interface
├── README.md         # Full documentation
└── .calendar_token   # Token storage (auto-created)
```

## 🐛 Troubleshooting

### "Chưa đăng nhập Google Calendar"
```bash
./tools/calendar/auth.sh login
```

### "Token expired"
```bash
./tools/calendar/auth.sh refresh
# Hoặc để script auto-refresh
```

### "Invalid credentials"
```bash
# Kiểm tra .env:
cat .env | grep GOOGLE
# Đảm bảo client ID & secret đúng
```

### "API not enabled"
```bash
# Vào Google Cloud Console
# APIs & Services → Library
# Enable "Google Calendar API"
```

## 📚 Docs

| File | Mô tả |
|------|-------|
| `tools/calendar/README.md` | Full documentation |
| `CALENDAR_IMPLEMENTATION.md` | Technical details |
| `CALENDAR_QUICK_REFERENCE.md` | This file |

## 🎯 Examples Flow

### Example 1: Xem lịch hôm nay
```
User: lịch trình của tôi hôm nay

AI Flow:
  1. get_current_time
  2. list_events(today 00:00 - today 23:59)
  3. Format & respond

Output:
  📅 Lịch trình hôm nay:
  1. 09:00 - 10:00: Họp team
  2. 14:00 - 15:00: Meeting
```

### Example 2: Thêm lịch
```
User: thêm lịch đi ăn tối lúc 7h

AI Flow:
  1. Parse "7h" → 19:00
  2. list_events(today 19:00 - 20:00) # Check conflict
  3. add_event("Đi ăn tối", 19:00, 20:00)
  4. Confirm

Output:
  ✅ Đã thêm lịch thành công!
  📅 Đi ăn tối
  🕐 19:00 - 20:00
```

### Example 3: Xóa và thêm (multi-step)
```
User: xoá các lịch họp sáng nay và thêm lịch đi chơi golf

AI Flow:
  1. list_events(today 08:00 - 12:00)
  2. Find events with "họp"
  3. delete_event(meeting1)
  4. delete_event(meeting2)
  5. add_event("Đi chơi golf", 09:00, 11:00)
  6. Summarize

Output:
  ✅ Đã xử lý xong!
  
  ❌ Đã xóa 2 lịch họp:
     • 09:00 - 10:00: Họp team
     • 11:00 - 12:00: Họp review
  
  ✅ Đã thêm lịch mới:
     • 09:00 - 11:00: Đi chơi golf
```

## 🎉 Tips

### 1. Dùng Chat Interface
Khuyến nghị dùng `./main.sh` thay vì gọi trực tiếp functions.

### 2. Natural Language
Nói tự nhiên, AI sẽ hiểu:
- ✓ "lịch hôm nay"
- ✓ "thêm lịch ăn tối"
- ✗ "list_events 2024-01-15..."

### 3. Multi-step Operations
AI tự động xử lý nhiều bước:
- "xóa họp và thêm golf" → AI tự chia thành: delete + add

### 4. Check trước khi thêm
AI luôn check conflict trước khi add event.

### 5. Context-aware
AI hiểu context:
- "sửa lịch đó thành 11h" → AI biết "lịch đó" là lịch vừa nhắc đến

## 🔐 Security Notes

- ✅ Token lưu local với permission 600
- ✅ Không commit token vào git
- ✅ Auto-refresh expired tokens
- ❌ Không share token
- ❌ Không commit credentials

## ⚡ Performance

- Calendar API: Fast (< 1s)
- OAuth refresh: ~ 1s
- Function calling: ~ 2-3s
- Multi-step: ~ 5-10s (depending on steps)

## 📊 Limits

- **Google Calendar API**: 1,000,000 requests/day
- **Gemini API Free**: 50 requests/day
- **Function calls**: Max 10 iterations per request

---

**Need help?** Xem `tools/calendar/README.md` để biết chi tiết!
