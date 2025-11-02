# 🤖 Chat Agent - Hệ Điều Hành

Đồ án môn **Hệ Điều Hành** - Chat Agent với Intent Classification & Multiple Tools

## ✨ Tính năng

- 🧠 **Intent Classification** - Tự động phân loại ý định
- 💬 **Chat** - Trò chuyện thông thường  
- 🎨 **Image Prompt** - Tạo prompt cho AI art
- 🔍 **Google Search** - Tìm kiếm thông tin thời gian thực
- 🌤️ **Weather** - Thông tin thời tiết thời gian thực
- 📅 **Calendar** - Quản lý lịch với Google Calendar

## 🚀 Cách chạy (3 bước)

### 1. Lấy API Key (MIỄN PHÍ)
```
https://aistudio.google.com/app/apikey
```

### 2. Tạo file .env
```bash
echo "GEMINI_API_KEY='your-api-key-here'" > .env
```

### 3. Chạy
```bash
chmod +x *.sh tools/*.sh
./main.sh
```

## 💡 Ví dụ sử dụng

### Chat thông thường
```
➜ Tại sao bầu trời màu xanh?
Agent: Vì hiện tượng tán xạ Rayleigh...
```

### Tạo ảnh (AI Art Prompt)
```
➜ Vẽ một con mèo đội mũ phù thủy
🎨 Đang tạo prompt...
Prompt: A majestic fluffy Persian cat...
```

### Tìm kiếm Google
```
➜ Bản iOS mới nhất là bao nhiêu?
🔍 Đang tìm kiếm...
Agent: iOS 18.1 được phát hành...
```

### Quản lý Lịch
```
➜ lịch trình của tôi hôm nay
📅 Lịch trình hôm nay:
1. 09:00 - 10:00: Họp team

➜ thêm lịch đi ăn tối lúc 7h
✅ Đã thêm lịch thành công!
```

## 🏗️ Kiến trúc

```
User Input
    ↓
router.sh (agent)
    ↓
intent.sh (classify)
    ↓
┌─────────┬──────────────┬──────────────┬─────────┬──────────┐
│ chat.sh │ image_create │ google_search │ weather │ calendar │
└─────────┴──────────────┴──────────────┴─────────┴──────────┘
```

## 📁 Cấu trúc

```
moibash/
├── router.sh          # Router chính
├── main.sh            # Chat UI
├── tools/
│   ├── intent.sh      # Intent classifier
│   ├── chat.sh        # Chat tool
│   ├── image_create.sh # Image prompt
│   ├── google_search.sh # Search tool
│   ├── weather/       # Weather tool
│   │   ├── function_call.sh
│   │   └── weather.sh
│   └── calendar/      # Calendar tool (NEW)
│       ├── auth.sh
│       ├── calendar.sh
│       └── function_call.sh
└── .env               # API keys
```

## 🎯 Intent Classification

Agent tự động phân loại 5 loại intent:

- **chat** - Câu hỏi thông thường, trò chuyện
- **image_create** - Yêu cầu tạo/vẽ ảnh  
- **google_search** - Cần thông tin thời gian thực
- **weather** - Hỏi về thời tiết
- **calendar** - Quản lý lịch, xem/thêm/sửa/xóa sự kiện

## 💬 Lệnh

- `/help` - Xem lệnh
- `/clear` - Xóa màn hình
- `/exit` - Thoát

## 🔧 Yêu cầu

- Bash (macOS/Linux)
- curl
- python3 (cho JSON parsing)
- Internet
- Gemini API Key

---

*Đồ án môn Hệ Điều Hành - Intent-based Multi-tool Agent* 🎓
