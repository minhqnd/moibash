# Hướng dẫn cài đặt Moibash

## 📦 Cài đặt

### Bước 1: Clone repository

```bash
git clone https://github.com/minhqnd/moibash.git
cd moibash
```

### Bước 2: Cài đặt dependencies

**Python 3** (cho một số agents):
```bash
# macOS
brew install python3

# Ubuntu/Debian
sudo apt install python3 python3-pip
```

**curl** (cho API calls):
```bash
# macOS
brew install curl

# Ubuntu/Debian
sudo apt install curl
```

### Bước 3: Cấu hình API keys

Tạo file `.env` từ template:
```bash
cp .env.example .env
```

Chỉnh sửa file `.env` và thêm API keys của bạn:
```bash
# Gemini API (bắt buộc)
GEMINI_API_KEY='your-gemini-api-key-here'

# Google Calendar (tùy chọn)
GOOGLE_CLIENT_ID='your-client-id'
GOOGLE_CLIENT_SECRET='your-client-secret'
```

Lấy Gemini API key tại: https://ai.google.dev/

### Bước 4: Cài đặt symlink

Chạy script cài đặt để tạo symlink vào `/usr/local/bin`:

```bash
./install.sh
```

Script sẽ:
- Cấp quyền thực thi cho tất cả scripts
- Tạo symlink `/usr/local/bin/moibash` → `<install-dir>/moibash.sh`
- Yêu cầu sudo password nếu cần

**Lưu ý**: Trên macOS, nếu gặp lỗi `readlink -f`, script sẽ tự động fallback sang `realpath`.

### Bước 5: Test cài đặt

```bash
# Chạy từ bất kỳ đâu
moibash

# Kiểm tra version
moibash --version

# Xem hướng dẫn
moibash --help
```

## 🔄 Cập nhật

### Cách 1: Sử dụng command built-in (Khuyến nghị)

```bash
moibash --update
```

Script sẽ:
1. Kiểm tra git repository
2. Stash các thay đổi local (nếu có)
3. Fetch và hiển thị updates từ GitHub
4. Pull code mới
5. Restore các thay đổi local
6. Cập nhật quyền thực thi
7. Re-install symlink nếu cần

### Cách 2: Update thủ công

```bash
cd /path/to/moibash
git pull origin main
./install.sh
```

### Cách 3: Chạy update script trực tiếp

```bash
cd /path/to/moibash
./update.sh
```

## 🗑️ Gỡ cài đặt

### Gỡ symlink (giữ code)

```bash
cd /path/to/moibash
./uninstall.sh
```

Script sẽ:
- Xóa symlink từ `/usr/local/bin/moibash`
- Giữ nguyên thư mục moibash và dữ liệu

### Gỡ hoàn toàn

```bash
cd /path/to/moibash
./uninstall.sh
cd ..
rm -rf moibash
```

## 🔧 Troubleshooting

### Lỗi: "command not found: moibash"

**Nguyên nhân**: `/usr/local/bin` không nằm trong PATH

**Giải pháp**:
```bash
# Kiểm tra PATH
echo $PATH | grep /usr/local/bin

# Nếu không có, thêm vào ~/.zshrc hoặc ~/.bashrc
echo 'export PATH="/usr/local/bin:$PATH"' >> ~/.zshrc
source ~/.zshrc
```

### Lỗi: "readlink: illegal option -- f"

**Nguyên nhân**: macOS không có `readlink -f`

**Giải pháp**: Script đã tự động xử lý, nếu vẫn lỗi:
```bash
# Cài đặt GNU coreutils
brew install coreutils

# Hoặc chạy trực tiếp
cd /path/to/moibash
./moibash.sh
```

### Lỗi: "Permission denied"

**Nguyên nhân**: Không có quyền thực thi

**Giải pháp**:
```bash
chmod +x install.sh moibash.sh router.sh
chmod +x tools/*.sh tools/*/*.sh
```

### Lỗi khi update: "You have unstaged changes"

**Nguyên nhân**: Có thay đổi chưa commit

**Giải pháp**: Update script sẽ tự động stash, nhưng nếu muốn thủ công:
```bash
git stash
git pull origin main
git stash pop
```

### Lỗi: "Not a git repository"

**Nguyên nhân**: Tải code bằng zip thay vì git clone

**Giải pháp**:
```bash
# Clone lại từ GitHub
rm -rf moibash
git clone https://github.com/minhqnd/moibash.git
cd moibash
./install.sh
```

## 🚀 Sử dụng nâng cao

### Chạy từ thư mục bất kỳ

```bash
# Mở terminal ở bất kỳ đâu
cd ~/Documents
moibash

# Hoặc
cd /tmp
moibash
```

### Multiple installations

Nếu muốn có nhiều phiên bản:
```bash
# Clone vào các thư mục khác nhau
git clone https://github.com/minhqnd/moibash.git ~/moibash-stable
git clone https://github.com/minhqnd/moibash.git ~/moibash-dev

# Cài đặt với tên khác
cd ~/moibash-dev
# Sửa SYMLINK_NAME trong install.sh thành "moibash-dev"
./install.sh

# Giờ có cả 2
moibash        # Stable version
moibash-dev    # Dev version
```

### Development mode

Nếu đang phát triển và không muốn dùng symlink:
```bash
cd /path/to/moibash
./moibash.sh
```

### Auto-update via cron

Tự động update mỗi ngày:
```bash
# Mở crontab
crontab -e

# Thêm dòng (update lúc 3h sáng)
0 3 * * * cd /path/to/moibash && git pull origin main > /dev/null 2>&1
```

## 📝 Ghi chú

- **Symlink**: Moibash sử dụng symlink để có thể gọi từ bất kỳ đâu
- **Git**: Update script yêu cầu project phải được clone qua git
- **Permissions**: Một số operations cần sudo (chỉ khi tạo symlink)
- **Data**: Lịch sử chat và images được lưu trong thư mục cài đặt

## 🆘 Cần trợ giúp?

- 📖 Đọc [README.md](README.md) để hiểu cách hoạt động
- 🐛 Báo lỗi tại [GitHub Issues](https://github.com/minhqnd/moibash/issues)
- 💬 Hỏi đáp trong [Discussions](https://github.com/minhqnd/moibash/discussions)
