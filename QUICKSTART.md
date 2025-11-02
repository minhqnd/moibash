# 🚀 QUICK START GUIDE

## Bắt đầu nhanh trong 3 bước!

### Bước 1️⃣: Cài đặt
```bash
cd moibash
chmod +x *.sh
```

### Bước 2️⃣: Thiết lập API Key

**Cách nhanh nhất:**
```bash
# Tạo file .env
echo "GEMINI_API_KEY='your-api-key-here'" > .env
```

**Hoặc dùng script tự động:**
```bash
./setup.sh
```

**Lấy API key tại:**
- Truy cập: https://aistudio.google.com/app/apikey
- Tạo API key mới (MIỄN PHÍ)
- Copy và paste vào

### Bước 3️⃣: Chạy Chat
```bash
./main.sh
```

## 🎉 Xong! Bắt đầu chat!

### Lệnh chat:
- Nhập bất kỳ câu hỏi nào
- `/help` - Xem hướng dẫn
- `/clear` - Xóa màn hình
- `/exit` hoặc `Ctrl+C` - Thoát

### Ví dụ chat:
```
➜ Giải thích process trong hệ điều hành

➜ Sự khác biệt giữa thread và process là gì?

➜ Hướng dẫn viết bash script

➜ Hôm nay học gì nhỉ?
```

## ⚠️ Nếu có lỗi?

### Test kết nối:
```bash
./test_api.sh
```

### Cài lại API key:
```bash
./setup.sh
```

### Reload shell:
```bash
source ~/.zshrc
```

## 📚 Đọc thêm
Xem file `README.md` để biết chi tiết!

---
**Chúc bạn chat vui vẻ với Gemini AI! 🤖✨**
