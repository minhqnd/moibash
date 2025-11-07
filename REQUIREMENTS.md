# Yêu Cầu Hệ Thống - Moibash

## 📋 Tổng Quan

Moibash là một ứng dụng bash script chạy trên terminal, yêu cầu một số công cụ và dependencies cơ bản để hoạt động.

## 🖥️ Hệ Điều Hành Hỗ Trợ

- **macOS** 10.14+ (Mojave trở lên)
- **Linux** (Ubuntu 18.04+, Debian 10+, CentOS 7+, Fedora 30+)
- **WSL** (Windows Subsystem for Linux)

## ⚙️ Yêu Cầu Bắt Buộc

### 1. Bash Shell
- **Phiên bản**: Bash 4.0 trở lên
- **Kiểm tra**: `bash --version`
- **Cài đặt**:
  ```bash
  # macOS (đã có sẵn, nhưng có thể cập nhật)
  brew install bash
  
  # Linux (thường đã có sẵn)
  sudo apt-get install bash  # Ubuntu/Debian
  sudo yum install bash       # CentOS/RHEL
  ```

### 2. Python 3
- **Phiên bản**: Python 3.6 trở lên (khuyến nghị 3.8+)
- **Kiểm tra**: `python3 --version`
- **Tại sao cần**: Một số agents (filesystem, calendar) sử dụng Python để xử lý JSON và logic phức tạp
- **Cài đặt**:
  ```bash
  # macOS
  brew install python3
  
  # Ubuntu/Debian
  sudo apt-get update
  sudo apt-get install python3 python3-pip
  
  # CentOS/RHEL
  sudo yum install python3 python3-pip
  
  # Fedora
  sudo dnf install python3 python3-pip
  ```

### 3. pip3 (Python Package Manager)
- **Kiểm tra**: `pip3 --version`
- **Tại sao cần**: Để cài đặt các thư viện Python nếu cần
- **Cài đặt**: Thường đi kèm với Python 3, nếu không:
  ```bash
  # macOS
  brew install python3
  
  # Ubuntu/Debian
  sudo apt-get install python3-pip
  
  # CentOS/RHEL
  sudo yum install python3-pip
  ```

### 4. curl
- **Phiên bản**: 7.50+ (khuyến nghị 7.70+)
- **Kiểm tra**: `curl --version`
- **Tại sao cần**: Để gọi các API (Gemini, Google Calendar, Weather, etc.)
- **Cài đặt**:
  ```bash
  # macOS (thường đã có sẵn)
  brew install curl
  
  # Ubuntu/Debian
  sudo apt-get install curl
  
  # CentOS/RHEL
  sudo yum install curl
  ```

### 5. Git
- **Phiên bản**: 2.0 trở lên
- **Kiểm tra**: `git --version`
- **Tại sao cần**: Để clone repository và cập nhật
- **Cài đặt**:
  ```bash
  # macOS
  brew install git
  
  # Ubuntu/Debian
  sudo apt-get install git
  
  # CentOS/RHEL
  sudo yum install git
  ```

## 🔑 API Keys (Bắt Buộc)

### Gemini API Key
- **Bắt buộc**: Có
- **Lấy từ**: [Google AI Studio](https://makersuite.google.com/app/apikey)
- **Miễn phí**: Có (với giới hạn)
- **Thiết lập**: Trong file `.env`
  ```bash
  GEMINI_API_KEY='your-api-key-here'
  ```

## 🔧 Yêu Cầu Tùy Chọn

### Các tính năng sau cần thêm dependencies:

#### Google Calendar (Tùy chọn)
Nếu bạn muốn sử dụng tính năng quản lý lịch:
- Google OAuth Client ID & Secret
- Lấy từ: [Google Cloud Console](https://console.cloud.google.com/)
- Thiết lập trong `.env`:
  ```bash
  GOOGLE_CLIENT_ID='your-client-id'
  GOOGLE_CLIENT_SECRET='your-client-secret'
  ```

#### Thư viện Python (Tùy chọn)
Một số tính năng nâng cao có thể cần:
```bash
pip3 install requests  # Cho HTTP requests nâng cao
pip3 install json      # Thường đã có sẵn
```

## 💾 Dung Lượng

- **Kích thước cài đặt**: ~5-10 MB
- **Bộ nhớ khi chạy**: ~50-100 MB RAM
- **Dung lượng cho logs/cache**: ~10-50 MB (tùy sử dụng)

## 🌐 Kết Nối Internet

- **Bắt buộc**: Có (cho hầu hết các tính năng)
- **Offline**: Chỉ có thể chat với AI (không có function calling)
- **Băng thông**: Tối thiểu 1 Mbps (khuyến nghị 5+ Mbps)

## ✅ Kiểm Tra Hệ Thống

Script cài đặt `install.sh` sẽ tự động kiểm tra tất cả yêu cầu:

```bash
# Remote install (tự động kiểm tra)
curl -fsSL https://raw.githubusercontent.com/minhqnd/moibash/main/install.sh | bash

# Local install (tự động kiểm tra)
./install.sh
```

Script sẽ kiểm tra:
- ✅ Bash version
- ✅ Python 3.6+ và pip3
- ✅ curl và git
- ✅ Internet connection
- ✅ Permissions
- ✅ API keys (yêu cầu nhập nếu chưa có)

Nếu thiếu bất kỳ dependency nào, script sẽ hiển thị hướng dẫn cài đặt cụ thể cho từng OS.

## 📱 Hỗ Trợ Nền Tảng

### ✅ Hoàn toàn hỗ trợ:
- macOS (Intel & Apple Silicon)
- Ubuntu 18.04+
- Debian 10+
- Linux Mint 19+
- Pop!_OS 20.04+

### ⚠️ Có thể hoạt động (chưa test đầy đủ):
- CentOS 7+
- Fedora 30+
- Arch Linux
- openSUSE

### ❌ Không hỗ trợ:
- Windows (trực tiếp) - Dùng WSL thay thế
- Android Termux (chưa test)
- iOS iSH (chưa test)

## 🔍 Troubleshooting

### "Python not found"
```bash
# Kiểm tra xem Python có được cài với tên khác không
which python
which python3
python --version
python3 --version

# Nếu có python nhưng không có python3, tạo symlink
sudo ln -s $(which python) /usr/local/bin/python3
```

### "Permission denied"
```bash
# Cấp quyền thực thi
chmod +x moibash.sh router.sh
chmod +x tools/**/*.sh tools/**/*.py
```

### "curl: command not found"
```bash
# Cài đặt curl
sudo apt-get install curl  # Ubuntu/Debian
brew install curl          # macOS
```

### "API Key invalid"
- Kiểm tra `.env` file
- Đảm bảo không có khoảng trắng thừa
- Key phải trong dấu nháy đơn: `GEMINI_API_KEY='key-here'`
- Lấy key mới từ [Google AI Studio](https://makersuite.google.com/app/apikey)

## 📚 Tài Liệu Liên Quan

- [INSTALL.md](INSTALL.md) - Hướng dẫn cài đặt chi tiết
- [README.md](README.md) - Tổng quan và sử dụng
- [QUICKSTART.md](QUICKSTART.md) - Bắt đầu nhanh
- [CONTRIBUTING.md](CONTRIBUTING.md) - Hướng dẫn đóng góp

## 💬 Hỗ Trợ

Nếu gặp vấn đề về yêu cầu hệ thống:
- Mở issue: [GitHub Issues](https://github.com/minhqnd/moibash/issues)
- Email: [minhqnd@example.com](mailto:minhqnd@example.com)

---

**Cập nhật**: November 7, 2025
