# 🤖 Chat Agent - Hệ Điều Hành

Đồ án môn **Hệ Điều Hành** - Chat Agent với Intent Classification & Multiple Tools

## ✨ Tính năng

- 🧠 **Intent Classification** - Tự động phân loại ý định
- 💬 **Chat** - Trò chuyện thông thường  
- 🎨 **Image Prompt** - Tạo prompt cho AI art
- 🔍 **Google Search** - Tìm kiếm thông tin thời gian thực

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

## 🏗️ Kiến trúc

```
User Input
    ↓
agent.sh (router)
    ↓
intent.sh (classify)
    ↓
┌─────────┬──────────────┬──────────────┐
│ chat.sh │ image_create │ google_search │
└─────────┴──────────────┴──────────────┘
```

## 📁 Cấu trúc

```
moibash/
├── agent.sh           # Router chính
├── main.sh            # Chat UI
├── tools/
│   ├── intent.sh      # Intent classifier
│   ├── chat.sh        # Chat tool
│   ├── image_create.sh # Image prompt
│   └── google_search.sh # Search tool
└── .env               # API key
```

## 🎯 Intent Classification

Agent tự động phân loại 3 loại intent:

- **chat** - Câu hỏi thông thường, trò chuyện
- **image_create** - Yêu cầu tạo/vẽ ảnh  
- **google_search** - Cần thông tin thời gian thực

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
