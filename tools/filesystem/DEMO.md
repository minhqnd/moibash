# 🎯 Demo: Filesystem Agent

Tài liệu này minh họa cách sử dụng Filesystem Agent trong các tình huống thực tế.

## Scenario 1: Tạo và chạy Python Hello World

### User Request
```
tạo file hello world bằng python và chạy nó cho tôi
```

### Agent Workflow

1. **Phân loại Intent**: `filesystem`
2. **Function Calling**:
   - `create_file("hello.py", "print('Hello World')")`
   - Yêu cầu xác nhận từ user
   - User chọn: `y` (đồng ý)
   - Tạo file thành công
3. **Execute**:
   - `execute_file("hello.py")`
   - Yêu cầu xác nhận
   - User chọn: `y` (đồng ý)
   - Chạy file và hiển thị output: `Hello World`

### Expected Output
```
⚠️  CẦN XÁC NHẬN THAO TÁC
================================================
📝 Tạo file: hello.py
   Nội dung: print('Hello World')...

Tùy chọn:
  y/yes/đồng ý  - Đồng ý thực hiện
  a/always/luôn - Luôn đồng ý (cho cả session)
  n/no/từ chối  - Từ chối (hủy thao tác)
================================================
Lựa chọn của bạn: y
✅ Đã chấp nhận

⚠️  CẦN XÁC NHẬN THAO TÁC
================================================
▶️  Chạy file: hello.py
...
================================================
Lựa chọn của bạn: y
✅ Đã chấp nhận

✅ Đã tạo và chạy file hello.py thành công!
Output: Hello World
```

## Scenario 2: Đổi tên tất cả file .exe thành .run

### User Request
```
đổi tên tất cả file có đuôi exe thành run
```

### Agent Workflow

1. **Phân loại Intent**: `filesystem`
2. **Function Calling**:
   - `search_files(".", "*.exe", recursive=true)`
   - Tìm thấy: file1.exe, file2.exe, test.exe
3. **Rename Loop**:
   - `rename_file("file1.exe", "file1.run")` → Xác nhận
   - User chọn: `a` (luôn đồng ý)
   - `rename_file("file2.exe", "file2.run")` → Auto accept
   - `rename_file("test.exe", "test.run")` → Auto accept
4. **Kết quả**: Đổi tên 3 files thành công

### Expected Output
```
✅ Tìm thấy 3 files .exe:
- file1.exe
- file2.exe  
- test.exe

⚠️  CẦN XÁC NHẬN THAO TÁC
================================================
📝 Đổi tên:
   Từ: file1.exe
   Sang: file1.run
...
================================================
Lựa chọn của bạn: a
✅ Đã chọn luôn đồng ý cho session này

✅ Đã đổi tên thành công 3 files:
- file1.exe → file1.run
- file2.exe → file2.run
- test.exe → test.run
```

## Scenario 3: Tìm và xóa tất cả file .exe

### User Request
```
tìm kiếm tất cả các file exe trong folder và folder con sau đó xoá đi cho tôi
```

### Agent Workflow

1. **Phân loại Intent**: `filesystem`
2. **Function Calling**:
   - `search_files(".", "*.exe", recursive=true)`
   - Tìm thấy: temp/file1.exe, cache/old.exe
3. **Delete Loop**:
   - `delete_file("temp/file1.exe")` → Xác nhận
   - User chọn: `y` (đồng ý)
   - `delete_file("cache/old.exe")` → Xác nhận
   - User chọn: `y` (đồng ý)
4. **Kết quả**: Xóa 2 files thành công

### Expected Output
```
✅ Tìm thấy 2 files .exe:
- temp/file1.exe
- cache/old.exe

⚠️  CẦN XÁC NHẬN THAO TÁC
================================================
🗑️  Xóa: temp/file1.exe
...
================================================
Lựa chọn của bạn: y
✅ Đã chấp nhận

⚠️  CẦN XÁC NHẬN THAO TÁC
================================================
🗑️  Xóa: cache/old.exe
...
================================================
Lựa chọn của bạn: y
✅ Đã chấp nhận

✅ Đã xóa thành công 2 files .exe
```

## Scenario 4: Đếm files và folders

### User Request
```
folder này đang có bao nhiêu file, bao nhiêu folder
```

### Agent Workflow

1. **Phân loại Intent**: `filesystem`
2. **Function Calling**:
   - `list_files(".", pattern="*", recursive=false)`
   - Không cần xác nhận (operation read-only)
3. **Kết quả**: Hiển thị số lượng files và folders

### Expected Output
```
📊 Thống kê folder hiện tại:
- Số lượng files: 15
- Số lượng folders: 3

📁 Chi tiết:
Files:
- main.sh (6528 bytes)
- router.sh (6906 bytes)
- .env.example (828 bytes)
...

Folders:
- tools/
- images/
- tmp/
```

## Scenario 5: Từ chối thao tác nguy hiểm

### User Request
```
xóa tất cả file txt
```

### Agent Workflow

1. **Phân loại Intent**: `filesystem`
2. **Function Calling**:
   - `search_files(".", "*.txt", recursive=true)`
   - Tìm thấy 5 files
3. **Delete Loop**:
   - `delete_file("important.txt")` → Xác nhận
   - User chọn: `n` (từ chối)
   - Agent báo lỗi và dừng

### Expected Output
```
✅ Tìm thấy 5 files .txt

⚠️  CẦN XÁC NHẬN THAO TÁC
================================================
🗑️  Xóa: important.txt
...
================================================
Lựa chọn của bạn: n
❌ Đã từ chối thao tác

❌ Đã hủy thao tác xóa file theo yêu cầu của bạn.
```

## Lưu ý về An toàn

### Các thao tác cần xác nhận
- ✅ Tạo file (`create_file`)
- ✅ Cập nhật file (`update_file`)
- ✅ Xóa file/folder (`delete_file`)
- ✅ Đổi tên (`rename_file`)
- ✅ Chạy file (`execute_file`)

### Các thao tác không cần xác nhận
- ✅ Đọc file (`read_file`)
- ✅ List files (`list_files`)
- ✅ Tìm kiếm files (`search_files`)

### Session "Always Accept"
- Khi chọn `a/always/luôn`, tất cả thao tác trong session sẽ được tự động chấp nhận
- Giúp xử lý nhanh các bulk operations
- Reset khi kết thúc session

## Testing

Để test filesystem agent mà không cần API key:

```bash
# Test basic operations
./tools/filesystem/filesystem.sh create "test.py" "print('test')"
./tools/filesystem/filesystem.sh read "test.py"
./tools/filesystem/filesystem.sh execute "test.py"
./tools/filesystem/filesystem.sh delete "test.py"

# Run integration tests
bash /tmp/test_filesystem_integration.sh
```
