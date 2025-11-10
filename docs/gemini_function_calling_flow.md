# 🔄 Gemini Function Calling Flow - Chi tiết

## 📋 Tổng quan

Gemini Function Calling trong Moibash sử dụng **multi-turn conversation loop** để thực hiện các tác vụ phức tạp thông qua việc gọi các function tuần tự.

## 🔁 Vòng lặp chính (Main Loop)

```python
while tool_calls_made < MAX_ITERATIONS:  # MAX_ITERATIONS = 50
    # 1. Gọi Gemini API với conversation history
    response = call_gemini_api(conversation, api_key)
    
    # 2. Parse response
    response_type, value, extra = parse_response(response)
    
    # 3. Xử lý theo loại response
    if response_type == "FUNCTION_CALL":
        # Thực thi function và tiếp tục loop
    elif response_type == "TEXT":
        # Final answer - dừng loop
    elif response_type == "ERROR":
        # Lỗi - dừng loop
```

## 🛑 Khi nào dừng vòng lặp?

### ✅ Dừng bình thường:
- **TEXT Response**: Gemini trả về câu trả lời cuối cùng
- **Hoàn thành task**: User intent đã được thực hiện đầy đủ

### ❌ Dừng bất thường:
- **ERROR**: Lỗi API hoặc parsing
- **NO_RESPONSE**: Không có response từ Gemini
- **MAX_ITERATIONS**: Vượt quá 50 function calls
- **KeyboardInterrupt**: User nhấn Ctrl+C

## 🎯 Cách Gemini chọn Function

### 🤖 Cơ chế chọn function:

1. **System Instruction**: Hướng dẫn Gemini về role và cách sử dụng functions
2. **Function Declarations**: Định nghĩa 8 functions với parameters chi tiết
3. **Conversation Context**: Lịch sử chat để hiểu context
4. **User Intent Analysis**: Phân tích yêu cầu user

### 📋 8 Functions có sẵn:

| Function | Mục đích | Confirmation | Backup |
|----------|----------|--------------|--------|
| `read_file` | Đọc nội dung file | ❌ Không | ❌ Không |
| `create_file` | Tạo file mới | ❌ Không | ❌ Không |
| `update_file` | Cập nhật file | ✅ Có (diff preview) | ✅ Có |
| `delete_file` | Xóa file/folder | ✅ Có | ✅ Có |
| `rename_file` | Đổi tên file | ✅ Có | ✅ Có |
| `list_files` | Liệt kê thư mục | ❌ Không | ❌ Không |
| `search_files` | Tìm kiếm files | ❌ Không | ❌ Không |
| `shell` | Chạy lệnh shell | ✅ Có | ❌ Không |

## ⚙️ Hoạt động của từng Function

### 1. 📖 `read_file(file_path)`
```python
# Input: {"file_path": "/path/to/file.txt"}
# Process:
result = call_filesystem_script("readfile", file_path)
# Output: {"content": "file content here"}
```

### 2. ✏️ `create_file(file_path, content)`
```python
# Input: {"file_path": "new_file.txt", "content": "Hello World"}
# Process: (No confirmation needed)
result = call_filesystem_script("createfile", file_path, content)
# Output: {"success": true, "path": "new_file.txt"}
```

### 3. 📝 `update_file(file_path, content, mode)`
```python
# Input: {"file_path": "file.txt", "content": "new content", "mode": "overwrite"}
# Process:
if not get_confirmation("update_file", args): return cancelled
backup_manager.backup_file(file_path, "update")  # Auto backup
show_diff_preview(old_content, new_content, file_path)  # Diff preview
result = call_filesystem_script("updatefile", file_path, content, mode)
```

### 4. 🗑️ `delete_file(file_path)`
```python
# Input: {"file_path": "/path/to/delete.txt"}
# Process:
if not get_confirmation("delete_file", args): return cancelled
backup_manager.backup_file(file_path, "delete")  # Auto backup
result = call_filesystem_script("deletefile", file_path)
```

### 5. 🏷️ `rename_file(old_path, new_path)`
```python
# Input: {"old_path": "old.txt", "new_path": "new.txt"}
# Process:
if not get_confirmation("rename_file", args): return cancelled
backup_manager.backup_file(old_path, "rename", new_path=new_path)
result = call_filesystem_script("renamefile", old_path, new_path)
```

### 6. 📂 `list_files(dir_path, pattern, recursive)`
```python
# Input: {"dir_path": ".", "pattern": "*.py", "recursive": "false"}
# Process:
resolved_dir, note = resolve_dir_path(dir_path)
result = call_filesystem_script("listfiles", resolved_dir, pattern, recursive)
# Output: {"files": ["file1.py", "file2.py", "subdir/file3.py"]}
```

### 7. 🔍 `search_files(dir_path, name_pattern, recursive)`
```python
# Input: {"dir_path": ".", "name_pattern": "*.txt", "recursive": "true"}
# Process:
resolved_dir, note = resolve_dir_path(dir_path)
result = call_filesystem_script("searchfiles", resolved_dir, name_pattern, recursive)
# Output: {"files": [{"path": "docs/readme.txt"}, {"path": "data/file.txt"}]}
```

### 8. 💻 `shell(action, command, file_path, args, working_dir)`
```python
# Input: {"action": "command", "command": "ls -la", "working_dir": "."}
# Process:
if not get_confirmation("shell", args): return cancelled
if action == "command":
    result = call_filesystem_script("shell", "command", command, "", working_dir)
elif action == "file":
    result = call_filesystem_script("shell", "file", file_path, args, working_dir)
```

## 🔐 Confirmation System

### 🛡️ Khi nào cần confirmation:
- `update_file`: Hiển thị diff preview + hỏi user
- `delete_file`: Hỏi user có chắc chắn xóa
- `rename_file`: Hỏi user có chắc chắn đổi tên
- `shell`: Hỏi user có chắc chắn chạy lệnh

### 💬 Confirmation Flow:
```
1. Hiển thị thông tin thao tác
2. Hỏi user: "1.Yes, 2.Yes always, 3.No"
3. Nếu "2. Yes always" → SESSION_STATE["always_accept"] = True
4. Tất cả thao tác sau không cần confirm nữa
```

## 💾 Backup System

### 🔄 Auto Backup cho:
- `update_file`: Backup file cũ trước khi update
- `delete_file`: Backup file trước khi xóa
- `rename_file`: Backup file với tên cũ

### 📁 Backup Location:
```
/tmp/moibash_backup_{PID}/
├── manifest.json          # Tracking operations
├── {timestamp}_{filename} # Backup files
```

### 🔙 Rollback:
```bash
# Rollback all operations in reverse order
for op in reversed(operations):
    if op["operation"] == "update":
        # Restore old content
    elif op["operation"] == "delete":
        # Restore deleted file
    elif op["operation"] == "rename":
        # Restore original name
```

## 📊 Conversation Flow

### 🔄 Multi-turn Loop Structure:
```
User Message
    ↓
[Conversation History] + [User Message]
    ↓
Gemini API Call (with function declarations)
    ↓
Gemini Response: FUNCTION_CALL + optional comment
    ↓
Execute Function → Get Result
    ↓
Add to Conversation:
- Model: function_call + comment
- Function: function_response
    ↓
Loop back to Gemini API
    ↓
Continue until TEXT response or error
```

### 📝 Conversation Format:
```json
[
  {"role": "user", "parts": [{"text": "tạo file test.txt"}]},
  {"role": "model", "parts": [
    {"text": "Đang tạo file..."},
    {"functionCall": {"name": "create_file", "args": {...}}}
  ]},
  {"role": "function", "parts": [{
    "functionResponse": {"name": "create_file", "response": {"content": {...}}}
  }]},
  {"role": "model", "parts": [{"text": "Đã tạo file thành công!"}]}
]
```

## 🎯 Smart Function Selection

### 🤖 Gemini Logic:
1. **Analyze User Intent**: Hiểu user muốn làm gì
2. **Check Available Functions**: Xem function nào phù hợp
3. **Plan Execution**: Có thể gọi nhiều functions tuần tự
4. **Safety First**: Ưu tiên functions an toàn, confirm cho nguy hiểm

### 📋 Examples:

**User: "đọc file main.py và chạy nó"**
```
1. Gemini: read_file("main.py") → Đọc nội dung
2. Gemini: shell(command="python3 main.py") → Chạy file
3. Gemini: TEXT "Đã chạy thành công!"
```

**User: "tạo file backup của config.json"**
```
1. Gemini: read_file("config.json") → Đọc nội dung
2. Gemini: create_file("config_backup.json", content) → Tạo backup
3. Gemini: TEXT "Đã tạo backup thành công!"
```

## ⚡ Performance & Limits

### 🔢 Limits:
- **MAX_ITERATIONS**: 50 function calls per conversation
- **API Timeout**: 30 seconds per call
- **History**: Last 10 messages for context
- **File Size**: Truncate large outputs

### 🚀 Optimizations:
- **Smart Path Resolution**: Tự động sửa đường dẫn sai
- **Caching**: Không có (do real-time nature)
- **Parallel**: Sequential execution (để đảm bảo safety)
- **Error Recovery**: Continue on partial failures

## 🔧 Error Handling

### 🛑 Error Types:
- **API Errors**: Network, quota, blocked content
- **Function Errors**: File not found, permission denied
- **Parsing Errors**: Invalid JSON, unexpected response
- **User Cancellation**: Ctrl+C, confirmation denied

### 🛟 Recovery:
- **Fallback Messages**: Generate response khi Gemini không trả lời
- **Partial Success**: Continue với operations còn lại
- **Clean Exit**: Proper cleanup on errors
- **Debug Mode**: Detailed logging khi DEBUG=1</content>
<parameter name="filePath">/Users/minhqnd/CODE/moibash/gemini_function_calling_flow.md