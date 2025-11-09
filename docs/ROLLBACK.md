# Tính năng Rollback cho Filesystem

## Tổng quan

Tính năng rollback cho phép bạn hoàn tác các thay đổi file trong phiên làm việc hiện tại. Mọi thao tác thay đổi file (cập nhật, xóa, đổi tên) đều được tự động backup, và bạn có thể khôi phục về trạng thái ban đầu bất cứ lúc nào.

## Cách hoạt động

### Automatic Backup
Khi bạn thực hiện các thao tác sau, hệ thống tự động tạo backup:
- **Cập nhật file** (`update_file`): Backup nội dung cũ trước khi ghi đè
- **Xóa file/folder** (`delete_file`): Backup toàn bộ file/folder trước khi xóa
- **Đổi tên file** (`rename_file`): Backup file gốc trước khi đổi tên

### Backup Storage
- Tất cả backup được lưu trong `/tmp/moibash_backup_<PID>/`
- Mỗi session (mỗi lần chạy moibash) có thư mục backup riêng
- Backup được đặt tên với timestamp để tránh trùng lặp
- File `manifest.json` lưu metadata của tất cả operations

### Session Scope
- Rollback chỉ ảnh hưởng đến session hiện tại
- Khi thoát moibash, backup vẫn được giữ trong `/tmp/` để bạn có thể restore thủ công nếu cần
- Các session khác nhau không ảnh hưởng lẫn nhau

## Lệnh sử dụng

### `/rollback`
Hoàn tác TẤT CẢ thay đổi file trong session hiện tại.

**Ví dụ:**
```
➜ /rollback
🔄 Đang rollback các thao tác filesystem...

✅ Đã rollback thành công!
Khôi phục được 3 file về trạng thái ban đầu.
```

### `/rollback-status`
Xem danh sách các file đã được backup.

**Ví dụ:**
```
➜ /rollback-status
📋 Trạng thái Backup:

Tổng số thao tác: 3

1. UPDATE - 20251109_195820_623436
   File: /home/user/test.py

2. DELETE - 20251109_195820_623775
   File: /home/user/old_file.txt

3. RENAME - 20251109_195830_123456
   File: /home/user/data.json
   → /home/user/data_backup.json
```

## Workflow ví dụ

### Kịch bản 1: Sửa nhầm file
```
➜ sửa file config.json, thêm logging level
✅ Đã cập nhật config.json thành công

➜ chạy lại app
❌ App crashed! Config file có lỗi

➜ /rollback
✅ Đã khôi phục config.json về trạng thái ban đầu
```

### Kịch bản 2: Xóa nhầm file quan trọng
```
➜ xóa các file log cũ trong thư mục logs/
⚠️  Cần xác nhận... [Y/n] y
✅ Đã xóa 5 file

➜ ối, xóa nhầm file quan trọng!

➜ /rollback
✅ Đã khôi phục 5 file về thư mục logs/
```

### Kịch bản 3: Kiểm tra trước khi rollback
```
➜ sửa nhiều file trong project

➜ /rollback-status
📋 Trạng thái Backup:
Tổng số thao tác: 10

1. UPDATE - main.py
2. UPDATE - utils.py
3. DELETE - temp.txt
...

➜ hmm, mình chỉ muốn giữ một số thay đổi
➜ /rollback
✅ Đã rollback toàn bộ

➜ giờ làm lại cẩn thận hơn
```

## Lưu ý quan trọng

### ✅ Được backup tự động
- Cập nhật nội dung file (overwrite hoặc append)
- Xóa file hoặc folder
- Đổi tên file/folder

### ❌ KHÔNG được backup
- Tạo file mới (`create_file`) - không cần backup vì file chưa tồn tại
- Đọc file (`read_file`) - không thay đổi file
- List/search file - không thay đổi file

### 🔐 An toàn
- Backup được tạo TRƯỚC KHI thực hiện thao tác
- Nếu thao tác thất bại, backup vẫn được giữ
- Rollback restore từ backup, không ảnh hưởng đến file khác
- Manifest file track đầy đủ metadata để debug

### ⚠️ Hạn chế
- Rollback là "all-or-nothing" - rollback toàn bộ session, không thể chọn từng file
- Backup lưu trong `/tmp/` nên có thể bị xóa khi reboot
- Nếu sửa cùng file nhiều lần, chỉ có backup đầu tiên được giữ (restore về trạng thái ban đầu nhất)

## License
Tính năng này là một phần của moibash project, sử dụng MIT License.
