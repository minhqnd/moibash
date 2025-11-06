# 📁 Filesystem Agent

Agent thông minh để thao tác với file và folder trên hệ thống.

## Tính năng

- ✅ **Đọc file**: Xem nội dung file
- ✅ **Tạo file**: Tạo file mới với nội dung
- ✅ **Cập nhật file**: Sửa nội dung file (ghi đề hoặc append)
- ✅ **Xóa file/folder**: Xóa file hoặc folder (recursive)
- ✅ **Đổi tên**: Đổi tên file hoặc folder
- ✅ **Chạy lệnh shell**: Thực thi bất kỳ lệnh shell nào (ls, cat, cp, find, kill, v.v.)
- ✅ **Chạy script file**: Thực thi script (Python, Bash, Node.js)
- ✅ **Liệt kê**: List files và folders
- ✅ **Tìm kiếm**: Tìm file theo pattern
- ✅ **Ghi nhớ ngữ cảnh**: Hiểu và ghi nhớ lịch sử chat để xử lý các câu hỏi tiếp theo
- ✅ **Hiển thị rõ ràng**: Hiển thị tool nào đang được gọi với border và format đẹp mắt

## An toàn

Agent có cơ chế **xác nhận** trước khi thực hiện các thao tác nguy hiểm:
- Tạo file
- Cập nhật file
- Xóa file/folder
- Đổi tên file/folder
- Chạy lệnh shell hoặc script file

### Tùy chọn xác nhận

Khi cần xác nhận, bạn có 3 lựa chọn:

1. **y/yes/đồng ý**: Đồng ý thực hiện thao tác này
2. **a/always/luôn**: Luôn đồng ý (cho toàn bộ session hiện tại)
3. **n/no/từ chối**: Từ chối thao tác (hủy)

## Cách sử dụng

### Qua Chat Interface

```bash
./main.sh
```

Sau đó chat với các yêu cầu như:

```
tạo file hello.py với nội dung hello world và chạy nó cho tôi
đổi tên tất cả file có đuôi .exe thành .run
tìm kiếm tất cả các file .exe trong folder và xoá đi cho tôi
folder này đang có bao nhiêu file, bao nhiêu folder
```

### Ví dụ với ngữ cảnh (Context-aware)

```
➜ có file exe nào trong folder hiện tại và folder con không
Agent: Có 2 file .exe: test.exe, tools/ok.exe

➜ xóa cho tôi
Agent: [Hiểu ngữ cảnh: xóa 2 file .exe vừa tìm được]
      Đã xóa 2 file .exe thành công
```

### Trực tiếp (Testing)

```bash
# Test function calling
./tools/filesystem/function_call.py "tạo file test.py với nội dung print hello"

# Test filesystem operations
./tools/filesystem/filesystem.sh read "/path/to/file"
./tools/filesystem/filesystem.sh create "/path/to/file" "content"
./tools/filesystem/filesystem.sh list "."
```

## Ví dụ

### Tạo file Python và chạy

**User**: "tạo file hello.py với nội dung print hello world và chạy nó"

**Agent**:
1. Tạo file `hello.py` với nội dung `print("Hello World")`
2. Yêu cầu xác nhận
3. Chạy file `hello.py`
4. Hiển thị output

### Đổi tên nhiều file

**User**: "đổi tên tất cả file .txt thành .md"

**Agent**:
1. Tìm tất cả file `.txt`
2. Với mỗi file, yêu cầu xác nhận đổi tên
3. Đổi tên file
4. Báo kết quả

### Xóa file theo pattern

**User**: "xóa tất cả file .tmp"

**Agent**:
1. Tìm tất cả file `.tmp`
2. Với mỗi file, yêu cầu xác nhận xóa
3. Xóa file
4. Báo kết quả

### Đếm files

**User**: "folder này có bao nhiêu file"

**Agent**:
1. List files trong folder hiện tại
2. Đếm số lượng files và folders
3. Hiển thị kết quả

## Lưu ý

- Agent sử dụng **Gemini Function Calling** để hiểu và xử lý yêu cầu
- Tất cả thao tác nguy hiểm đều có xác nhận
- Đường dẫn có thể là tuyệt đối hoặc tương đối
- Hỗ trợ chạy script Python, Bash, Node.js

## Kiến trúc

```
filesystem/
├── function_call.py    # Gemini function calling + confirmation + context
├── shell.sh            # Unified shell execution (commands & scripts)
├── createfile.sh       # Create file
├── updatefile.sh       # Update file
├── deletefile.sh       # Delete file
├── renamefile.sh       # Rename file
├── readfile.sh         # Read file
├── listfiles.sh        # List files
├── searchfiles.sh      # Search files
└── README.md          # Documentation
```

**Flow**:
1. User yêu cầu → Intent classifier → Filesystem agent
2. Load chat history cho context
3. Function calling parse yêu cầu (có context)
4. Hiển thị tool đang được gọi (với border)
5. Yêu cầu confirmation (nếu cần)
6. Thực thi thao tác
7. Save chat history
8. Trả kết quả cho user

**Cải tiến mới**:
- ✅ Gộp `executefile.sh` và `processtool.sh` thành `shell.sh`
- ✅ Chat history để hiểu ngữ cảnh
- ✅ Hiển thị rõ ràng tool nào đang được gọi
- ✅ Backward compatible với `execute_file` và `run_command`
