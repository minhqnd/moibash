# 🎉 Moibash v1.1.0 - Cải Tiến Lớn!

## Tóm Tắt Thay Đổi

### ✅ Script Đơn Giản Hơn
- **Trước**: 5 script files (install.sh, install_remote.sh, system_check.sh, update.sh, uninstall.sh)
- **Sau**: 2 script files (install.sh, moibash.sh)
- **Lợi ích**: Dễ maintain, ít confusion, faster development

### ✅ Cài Đặt Thống Nhất
```bash
# Một script cho tất cả:
./install.sh                    # Local install
curl ... install.sh | bash      # Remote install
./install.sh --uninstall       # Uninstall
```

### ✅ Auto-Update
- Tự động check update mỗi ngày
- Thông báo khi có version mới
- Update dễ dàng: `moibash --update`

### ✅ Yêu Cầu Python 3.6+
- Validate trong quá trình install
- Hướng dẫn rõ ràng nếu thiếu
- Hỗ trợ các filesystem/calendar agents

## Cách Cập Nhật

### Nếu đã cài moibash:
```bash
moibash --update
```

### Cài đặt mới:
```bash
curl -fsSL https://raw.githubusercontent.com/minhqnd/moibash/main/install.sh | bash
```

## Files Đã Thay Đổi

### ➕ Thêm Mới:
- `REQUIREMENTS.md` - Chi tiết yêu cầu hệ thống
- `MIGRATION_GUIDE.md` - Hướng dẫn migrate
- Auto-update logic trong `moibash.sh`

### 🔄 Cập Nhật:
- `install.sh` - Gộp tất cả install logic
- `moibash.sh` - Thêm auto-update check
- `README.md` - Cập nhật hướng dẫn
- `CHANGELOG.md` - Thêm v1.1.0 notes

### ❌ Xóa Bỏ:
- `install_remote.sh` → Gộp vào `install.sh`
- `system_check.sh` → Gộp vào `install.sh`
- `update.sh` → Gộp vào `moibash.sh`
- `uninstall.sh` → Gộp vào `install.sh --uninstall`

## Testing

Đã test trên macOS. Cần test thêm:
- [ ] Ubuntu/Debian
- [ ] CentOS/RHEL
- [ ] WSL

## Documentation

Xem chi tiết:
- [CHANGELOG.md](CHANGELOG.md)
- [MIGRATION_GUIDE.md](MIGRATION_GUIDE.md)
- [REQUIREMENTS.md](REQUIREMENTS.md)

---
**Version**: 1.1.0  
**Date**: November 7, 2025
