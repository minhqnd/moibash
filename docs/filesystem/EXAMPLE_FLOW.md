# 📖 Example Flow: Filesystem Agent

Tài liệu này minh họa chi tiết flow hoạt động của Filesystem Agent.

## Architecture Overview

```
User Input
    ↓
main.sh (Chat Interface)
    ↓
router.sh (Intent Classification)
    ↓
tools/intent.sh (Phân loại: filesystem)
    ↓
tools/filesystem/function_call.py (Gemini Function Calling)
    ↓
[Confirmation] → User chọn y/a/n
    ↓
tools/filesystem/filesystem.sh (Execute)
    ↓
Result → User
```

## Detailed Example: Create and Run Python File

### 1. User Input
```bash
$ ./main.sh
➜ tạo file hello world bằng python và chạy nó cho tôi
```

### 2. Router Classification
File: `router.sh`
```bash
# Phân loại intent
intent=$(classify_intent "tạo file hello world bằng python và chạy nó cho tôi")
# Result: "filesystem"
```

### 3. Intent Classifier
File: `tools/intent.sh`
```python
# Keyword matching
message = "tạo file hello world bằng python và chạy nó cho tôi"
if any(word in message for word in ['file', 'tạo file', 'chạy']):
    intent = 'filesystem'
```

### 4. Function Calling (Agent)
File: `tools/filesystem/function_call.py`

#### Step 1: Gemini Function Call
```json
{
  "role": "user",
  "parts": [{
    "text": "tạo file hello world bằng python và chạy nó cho tôi"
  }]
}
```

Gemini Response:
```json
{
  "functionCall": {
    "name": "create_file",
    "args": {
      "file_path": "hello.py",
      "content": "print('Hello World')"
    }
  }
}
```

#### Step 2: Confirmation
```
⚠️  CẦN XÁC NHẬN THAO TÁC
====================================
📝 Tạo file: hello.py
   Nội dung: print('Hello World')...

Tùy chọn:
  y/yes/đồng ý  - Đồng ý thực hiện
  a/always/luôn - Luôn đồng ý (cho cả session)
  n/no/từ chối  - Từ chối (hủy thao tác)
====================================
Lựa chọn của bạn: y
```

User input: `y`

#### Step 3: Execute Create File
File: `tools/filesystem/filesystem.sh`
```bash
./filesystem.sh create "hello.py" "print('Hello World')"
```

Result:
```json
{
  "success": true,
  "path": "/current/dir/hello.py",
  "message": "Đã tạo file thành công"
}
```

#### Step 4: Gemini Function Response
```json
{
  "role": "function",
  "parts": [{
    "functionResponse": {
      "name": "create_file",
      "response": {
        "content": {
          "success": true,
          "path": "/current/dir/hello.py"
        }
      }
    }
  }]
}
```

#### Step 5: Gemini Next Function Call
```json
{
  "functionCall": {
    "name": "execute_file",
    "args": {
      "file_path": "hello.py"
    }
  }
}
```

#### Step 6: Confirmation (Execute)
```
⚠️  CẦN XÁC NHẬN THAO TÁC
====================================
▶️  Chạy file: hello.py

Tùy chọn:
  y/yes/đồng ý  - Đồng ý thực hiện
  a/always/luôn - Luôn đồng ý (cho cả session)
  n/no/từ chối  - Từ chối (hủy thao tác)
====================================
Lựa chọn của bạn: y
```

User input: `y`

#### Step 7: Execute File
```bash
./filesystem.sh execute "hello.py"
```

Result:
```json
{
  "success": true,
  "output": "Hello World",
  "exit_code": 0,
  "path": "/current/dir/hello.py"
}
```

#### Step 8: Gemini Final Response
```json
{
  "text": "✅ Đã tạo và chạy file hello.py thành công!\n\nKết quả:\nHello World\n\nFile được lưu tại: /current/dir/hello.py"
}
```

### 5. Display to User
```
Agent: ✅ Đã tạo và chạy file hello.py thành công!

Kết quả:
Hello World

File được lưu tại: /current/dir/hello.py
```

## Session State: Always Accept Mode

Khi user chọn `a` (always accept), các thao tác tiếp theo trong session sẽ không cần xác nhận:

```python
SESSION_STATE = {
    "always_accept": True  # Set khi user chọn 'a'
}

def get_confirmation(action, details):
    if SESSION_STATE["always_accept"]:
        return True  # Auto accept
    # ... prompt user
```

### Example với Always Accept
```bash
➜ đổi tên tất cả file .txt thành .md
```

Flow:
1. Search files: Tìm 5 files `.txt`
2. Rename file1.txt → Confirmation → User chọn `a`
3. Rename file2.txt → Auto accept (no prompt)
4. Rename file3.txt → Auto accept
5. Rename file4.txt → Auto accept
6. Rename file5.txt → Auto accept
7. Done: 5 files renamed

## Error Handling

### User Refuses Operation
```bash
➜ xóa tất cả file trong folder
```

```
⚠️  CẦN XÁC NHẬN THAO TÁC
====================================
🗑️  Xóa: important.txt
====================================
Lựa chọn của bạn: n
❌ Đã từ chối thao tác
```

Function returns:
```json
{
  "error": "User từ chối thao tác",
  "cancelled": true
}
```

Gemini receives this and responds:
```
❌ Đã hủy thao tác xóa file theo yêu cầu của bạn.
```

## Testing Without API Key

Test filesystem.sh directly:
```bash
# Create
./tools/filesystem/filesystem.sh create "test.py" "print('test')"

# Read  
./tools/filesystem/filesystem.sh read "test.py"

# Execute
./tools/filesystem/filesystem.sh execute "test.py"

# List
./tools/filesystem/filesystem.sh list "." "*" "false"

# Search
./tools/filesystem/filesystem.sh search "." "*.py" "true"

# Delete
./tools/filesystem/filesystem.sh delete "test.py"
```

## Function Declarations

Available functions for Gemini:
- `read_file(file_path)` - No confirmation
- `create_file(file_path, content)` - **Needs confirmation**
- `update_file(file_path, content, mode)` - **Needs confirmation**
- `delete_file(file_path)` - **Needs confirmation**
- `rename_file(old_path, new_path)` - **Needs confirmation**
- `execute_file(file_path, args, working_dir)` - **Needs confirmation**
- `list_files(dir_path, pattern, recursive)` - No confirmation
- `search_files(dir_path, name_pattern, recursive)` - No confirmation

## Security Features

1. **Mandatory Confirmation**: Tất cả thao tác nguy hiểm cần xác nhận
2. **Clear Information**: Hiển thị đầy đủ thông tin trước khi thực thi
3. **Three Options**: y (once), a (always), n (cancel)
4. **Session Scope**: Always accept chỉ trong session hiện tại
5. **Cancellable**: User có thể từ chối bất kỳ lúc nào

## Performance

- **Average Response Time**: 2-5 seconds (bao gồm Gemini API call)
- **Confirmation Time**: Depends on user input
- **File Operations**: Near instant (<100ms)
- **Function Calls**: Typically 1-3 calls per request
- **Max Iterations**: 15 function calls per conversation

## Limitations

1. **File Size**: Không đọc files > 10MB để tránh out of memory
2. **Permissions**: Chỉ thao tác files có quyền access
3. **Execution**: Chỉ hỗ trợ Python, Bash, Node.js scripts
4. **Path**: Đường dẫn phải valid và accessible
5. **API Quota**: Phụ thuộc vào Gemini API quota

## Best Practices

1. **Always Review**: Kiểm tra kỹ trước khi chọn "always accept"
2. **Backup Important Files**: Trước khi bulk delete/rename
3. **Test First**: Test với non-critical files trước
4. **Clear Requests**: Đưa ra yêu cầu rõ ràng và cụ thể
5. **Monitor Output**: Theo dõi output của execute operations
