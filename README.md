# 🤖 Chat Agent - Hệ Điều Hành

Đồ án môn **Hệ Điều Hành** - Chat Agent viết bằng Bash Script

## 📋 Mô tả

Đây là một ứng dụng chat terminal được viết bằng Bash Script, tích hợp với **Google Gemini API**:
- **agent.sh**: Tích hợp Gemini API để xử lý tin nhắn
- **main.sh**: Giao diện chat terminal

## ⚙️ Cài đặt & Cấu hình

### 1. Lấy Gemini API Key

1. Truy cập: https://aistudio.google.com/app/apikey
2. Đăng nhập với tài khoản Google
3. Tạo API key mới
4. Copy API key

### 2. Thiết lập API Key

**Cách 1: Dùng file .env (Đơn giản nhất)** ⭐

Tạo file `.env` trong thư mục project:
```bash
echo "GEMINI_API_KEY='your-api-key-here'" > .env
```

Hoặc copy từ template:
```bash
cp .env.example .env
# Sau đó chỉnh sửa .env và thay API key
```

**Cách 2: Dùng script tự động**
```bash
./setup.sh
```

**Cách 3: Thiết lập vĩnh viễn trong shell**

Thêm vào file `~/.zshrc` (hoặc `~/.bashrc` nếu dùng bash):
```bash
export GEMINI_API_KEY='your-api-key-here'
```

Sau đó reload shell:
```bash
source ~/.zshrc
```

### 3. Cấp quyền thực thi
```bash
chmod +x *.sh
```

### 4. Thiết lập API Key (Khuyến nghị)
```bash
./setup.sh
```
Script này sẽ hướng dẫn bạn:
- Nhập API key
- Tự động lưu vào shell config
- Test API ngay lập tức

### 5. Test kết nối (Tùy chọn)
```bash
./test_api.sh
```

### 6. Chạy chương trình
```bash
./main.sh
```

## 💬 Cách sử dụng

### Lệnh đặc biệt:
- `/help` - Hiển thị danh sách lệnh
- `/clear` - Xóa màn hình và lịch sử chat
- `/exit` hoặc `/quit` - Thoát chương trình
- `Ctrl+C` - Thoát nhanh

### Chat với Gemini AI:
Agent sử dụng **Google Gemini 2.0 Flash** để trả lời mọi câu hỏi của bạn:
- 🧠 **AI thông minh**: Trả lời đa dạng các chủ đề
- 🇻🇳 **Tiếng Việt tự nhiên**: Được tối ưu cho người Việt
- 💬 **Hội thoại linh hoạt**: Có thể chat về bất kỳ điều gì
- 📚 **Kiến thức rộng**: Lập trình, học tập, đời sống, v.v.

**Ví dụ câu hỏi:**
- "Giải thích process trong hệ điều hành"
- "Hướng dẫn viết bash script"
- "Sự khác biệt giữa thread và process"
- "Hôm nay học gì?"
- Chat bất kỳ chủ đề nào bạn muốn!

## 🎨 Tính năng

- 🤖 **Tích hợp Gemini AI**: Chat với AI thông minh từ Google
- ✨ Giao diện đẹp mắt với màu sắc ANSI
- 📝 Hiển thị timestamp cho mỗi tin nhắn
- 💾 Lưu lịch sử chat trong session
- � API calls với curl
- 🛡️ Xử lý lỗi và input validation
- ⚡ Fallback mode khi API không khả dụng

## 📂 Cấu trúc file

```
moibash/
├── agent.sh       # Tích hợp Gemini API
├── main.sh        # Giao diện chat terminal
├── setup.sh       # Script thiết lập API key
├── test_api.sh    # Script test kết nối API
└── README.md      # Hướng dẫn sử dụng
```

## 🔧 Yêu cầu hệ thống

- Bash shell (macOS, Linux, WSL trên Windows)
- Terminal hỗ trợ màu ANSI
- `curl` command (thường có sẵn)
- `jq` (tùy chọn, để parse JSON đẹp hơn)
- Kết nối internet (để gọi Gemini API)
- Gemini API Key (miễn phí tại Google AI Studio)

## 📸 Demo

```
╔═══════════════════════════════════════════════════════════╗
║                                                           ║
║          🤖  CHAT AGENT - HỆ ĐIỀU HÀNH  🤖               ║
║                                                           ║
║            Bash Script Chat Interface v1.0                ║
║                                                           ║
╚═══════════════════════════════════════════════════════════╝

[15:50:32] Agent: Xin chào! Tôi là Chat Agent...

➜ xin chào
[15:50:35] Bạn: xin chào
[15:50:35] Agent: Chào bạn! Hôm nay bạn thế nào? 😊

➜ 
```

## 👨‍💻 Tác giả

Sinh viên môn Hệ Điều Hành

## � Troubleshooting

### Lỗi: "Chưa thiết lập GEMINI_API_KEY"
**Giải pháp:**
```bash
./setup.sh
```

### Lỗi: "Không thể kết nối đến Gemini API"
**Kiểm tra:**
1. Kết nối internet: `ping google.com`
2. API key đúng chưa: `echo $GEMINI_API_KEY`
3. Test lại: `./test_api.sh`

### API key không hoạt động sau khi thiết lập
**Giải pháp:**
```bash
# Reload shell config
source ~/.zshrc   # hoặc source ~/.bashrc
```

### Agent trả về lỗi 400/401
**Nguyên nhân:** API key không hợp lệ hoặc hết hạn

**Giải pháp:**
1. Tạo API key mới tại: https://aistudio.google.com/app/apikey
2. Chạy lại: `./setup.sh`

### curl command not found
**Giải pháp:**
```bash
# macOS (nếu chưa có)
brew install curl

# Ubuntu/Debian
sudo apt-get install curl
```

## 🌟 Mở rộng

### Thêm tính năng có thể phát triển:
- 💾 Lưu lịch sử hội thoại vào file
- 🔄 Context-aware conversation (multi-turn)
- 🎨 Tùy chỉnh personality của AI
- 📊 Thống kê số tin nhắn, token usage
- 🔊 Text-to-speech cho response
- 🌐 Hỗ trợ nhiều model AI khác nhau

## �📝 License

Educational purpose - Đồ án môn học

---

*Được xây dựng với ❤️ bằng Bash Script và Gemini AI*
