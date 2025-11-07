# 🚀 Quick Start Guide

## TL;DR - Cài đặt trong 30 giây

```bash
git clone https://github.com/minhqnd/moibash.git && cd moibash
cp .env.example .env
# Thêm GEMINI_API_KEY vào .env
./install.sh
moibash
```

## 📋 Prerequisites

- **macOS** hoặc **Linux** (Bash/Zsh)
- **Git** (để clone và update)
- **Python 3** (cho một số tools)
- **curl** (cho API calls)
- **Gemini API Key** - [Lấy miễn phí tại đây](https://ai.google.dev/)

## 🎯 Cài đặt từng bước

### 1️⃣ Clone repository

```bash
git clone https://github.com/minhqnd/moibash.git
cd moibash
```

### 2️⃣ Setup API key

```bash
# Copy template
cp .env.example .env

# Mở file .env và thêm API key
nano .env  # hoặc vim, code, etc.
```

Thêm vào `.env`:
```bash
GEMINI_API_KEY='your-actual-api-key-here'
```

### 3️⃣ Cài đặt

```bash
./install.sh
```

### 4️⃣ Chạy

```bash
moibash
```

Xong! 🎉

## 💬 Sử dụng cơ bản

### Khởi động chat

```bash
moibash
```

### Các lệnh trong chat

| Lệnh | Mô tả |
|------|-------|
| `/help` | Xem danh sách lệnh |
| `/clear` | Xóa màn hình |
| `/exit` hoặc `/quit` | Thoát |

### Ví dụ chat

```
➜ hello
Agent: Xin chào! Tôi là Chat Agent...

➜ thời tiết Hà Nội
Agent: 🌤️ Thời tiết tại Hà Nội: 25°C, nắng đẹp...

➜ tạo file test.txt với nội dung hello world
⚠️  CẦN XÁC NHẬN THAO TÁC
Lựa chọn của bạn: y
Agent: ✅ Đã tạo file thành công!

➜ /exit
👋 Tạm biệt!
```

## 🔄 Cập nhật

### Tự động (khuyến nghị)

```bash
moibash --update
```

### Thủ công

```bash
cd /path/to/moibash
git pull origin main
./install.sh
```

## ❓ Troubleshooting

### "command not found: moibash"

```bash
# Kiểm tra symlink
ls -la /usr/local/bin/moibash

# Nếu không có, chạy lại install
cd /path/to/moibash
./install.sh
```

### "API key not found"

```bash
# Kiểm tra .env
cat .env

# Đảm bảo có dòng:
# GEMINI_API_KEY='your-key-here'
```

### "Permission denied"

```bash
chmod +x moibash.sh router.sh install.sh
./install.sh
```

## 📚 Next Steps

- 📖 Đọc [README.md](README.md) để hiểu chi tiết cách hoạt động
- 🔧 Xem [INSTALL.md](INSTALL.md) để biết hướng dẫn chi tiết
- 🛠️ Explore các tools trong `tools/`
- 🎨 Customize theo nhu cầu

## 🆘 Cần giúp đỡ?

- 🐛 [Report bugs](https://github.com/minhqnd/moibash/issues)
- 💬 [Discussions](https://github.com/minhqnd/moibash/discussions)
- 📧 Contact: [minhqnd](https://github.com/minhqnd)

## 🎉 Enjoy!

```bash
moibash
➜ bắt đầu nào!
```
