# 📁 Filesystem Tool — Tài liệu (Phiên bản rút gọn & cập nhật)

## Tổng quan

Filesystem Tool là bộ công cụ thao tác file được tích hợp trong dự án **moibash**. Mục tiêu của tài liệu này là cung cấp một hướng dẫn ngắn gọn, thực dụng cho các chức năng chính, quy trình an toàn (confirmation), ví dụ phổ biến và cách debug nhanh.

Phiên bản này tập trung vào: rõ ràng, ví dụ có thể chạy được, và quy tắc an toàn khi thực thi lệnh/sửa file.

---

## Kiến trúc & Flow hoạt động (tóm tắt)

- Agent (chat) → `function_call.py` → shell scripts (`*.sh`) → File system
- Mọi thao tác nguy hiểm (create/update/delete/execute) phải qua hệ thống xác nhận (confirmation) theo session.

Luồng cơ bản:
1. Người dùng yêu cầu (ví dụ: "đọc file X").
2. Agent gọi hàm tương ứng (ví dụ: read_file).
3. Hệ thống hiển thị thông báo/preview (nếu thay đổi). Người dùng chọn: 1) Allow once, 2) Allow always (session), 3) Cancel.
4. Nếu được phép: shell script chạy, kết quả trả về agent dưới dạng JSON + Markdown.

---

## Chức năng có sẵn (API nhanh)

Tất cả hàm trả về cấu trúc JSON chung: { success: boolean, content?: string, files?: [], output?: string, exit_code?: number, error?: string, path?: string }

- read_file(file_path, start_line?: int, end_line?: int)
  - Đọc file. Nếu lớn, ưu tiên đọc theo khúc (chunks).
  - Ví dụ: read_file("/full/path/to/file.txt")

- create_file(file_path, content)
  - Tạo file mới (text). Triggers confirmation.

- update_file(file_path, content, mode = "overwrite"|"append")
  - overwrite: thay toàn bộ; append: thêm vào cuối. Hiển thị diff preview.

- delete_file(file_path)
  - Xóa file hoặc thư mục. Yêu cầu confirmation.

- rename_file(old_path, new_path)
  - Đổi tên/move. Yêu cầu confirmation.

- list_files(dir_path, pattern = "*", recursive = false)
  - Trả về danh sách file/folder.

- search_files(dir_path, pattern, recursive = false)
  - Tìm theo pattern. Trả về danh sách file matching.

- shell(action = "command"|"file", target, args = "", working_dir = "")
  - action="command": chạy shell command (khuyến nghị).
  - action="file": chạy script file (ít dùng, có rủi ro đường dẫn).
  - Ví dụ: shell("command","ls -la /tmp")

---

## Quy tắc an toàn (Security & Confirmation)

- Bắt buộc validation đường dẫn: ưu tiên đường dẫn tuyệt đối; chặn path traversal và các thư mục hệ thống (`/etc`, `/root`, ...).
- Trước khi thực hiện các hành động destructive (create/update/delete/execute), hệ thống sẽ yêu cầu xác nhận theo 3 lựa chọn: 1 (Allow once), 2 (Allow always trong session), 3 (Cancel).
- Trước khi ghi đè hoặc xóa, tạo bản backup tạm `file.ext.bak` nếu có thể.

Path checks mẫu:
- Không cho phép `..` trong path.
- Bắt buộc path bắt đầu bằng `/` hoặc repo-relative dựa trên cấu hình agent.

---

## Diff preview

- Khi update (overwrite), agent hiển thị Git-style diff (hunk header, dòng thêm/bớt). Mục đích: user kiểm tra trước khi confirm.
- Khi append, chỉ hiển thị phần thêm.

Ví dụ preview (ký hiệu):

--- a/file.txt
++ b/file.txt
@@ -1,3 +1,4 @@
- Dòng cũ
+ Dòng mới

---

## Auto-fix & Test Loop (tóm tắt)

Hệ thống hỗ trợ một vòng lặp tối đa 3 lần để tự sửa lỗi thông dụng (syntax, import, small logic fixes) kèm test cơ bản. Quy trình:
1. Đọc file → phát hiện lỗi.
2. Gợi ý sửa → áp dụng (local) → chạy test nhanh (ví dụ: `python -m py_compile file.py` hoặc `bash -n script.sh`).
3. Nếu pass → commit thay đổi (hoặc apply) → báo kết quả.
4. Nếu fail → tối đa 3 lần thử, sau đó dừng và báo lỗi.

Lưu ý: chỉ áp dụng auto-fix cho các lỗi có độ an toàn cao. Thay đổi logic lớn cần review thủ công.

---

## Kiểm tra nhanh theo ngôn ngữ (recipes)

- Python: `python -m py_compile file.py` → `python -c "import file"` → `pytest` nếu có tests.
- Shell: `bash -n script.sh` (syntax), `shellcheck` (lint).
- JS/TS: `node --check file.js`, `npx tsc --noEmit` (TypeScript), `npx eslint`.

---

## Best practices (tóm tắt)

- Dùng đường dẫn tuyệt đối.
- Đọc lớn theo chunk cho file lớn.
- Dùng `shell("command", "...")` thay vì `file` khi có thể.
- Backup trước khi overwrite/xóa.
- Hạn chế granting "Allow always" trừ khi tin tưởng session.

---

## Quick start (thử nhanh)

1. Đảm bảo script có quyền thực thi:

```bash
chmod +x tools/filesystem/*.sh
```

2. Thử đọc file mẫu:

```bash
./tools/filesystem/function_call.py "liệt kê thư mục tools"
```

3. Tạo file thử (agent sẽ hỏi confirm):

```bash
echo "1" | ./tools/filesystem/function_call.py "tạo file demo.txt với nội dung Hello"
```

---

## Ví dụ JSON response (mẫu)

Success:

```json
{ "success": true, "content": "...", "path": "/full/path" }
```

Error:

```json
{ "success": false, "error": "File not found: /path/to/file", "exit_code": 1 }
```

---

## Troubleshooting nhanh

- "File not found": kiểm tra path, dùng `ls -la`.
- "Permission denied": kiểm tra quyền, `ls -la` và owner; nếu cần, chạy bằng user có quyền (không recommend sudo tự động).
- "Command not found": kiểm tra PATH hoặc dùng đường dẫn đầy đủ tới binary.

---

## API Reference (hàm và chữ ký)

def read_file(file_path: str, start_line: int = None, end_line: int = None) -> Dict
def create_file(file_path: str, content: str) -> Dict
def update_file(file_path: str, content: str, mode: str = "overwrite") -> Dict
def delete_file(file_path: str) -> Dict
def rename_file(old_path: str, new_path: str) -> Dict
def list_files(dir_path: str, pattern: str = "*", recursive: bool = False) -> Dict
def search_files(dir_path: str, pattern: str, recursive: bool = False) -> Dict
def shell(action: str, target: str, args: str = "", working_dir: str = "") -> Dict

---

## Gợi ý cải tiến tiếp theo (nên làm)

1. Thêm ví dụ cụ thể cho từng hàm ở cuối file (sample payloads).
2. Viết test unit cho `function_call.py` để mock các lệnh shell.
3. Tích hợp `shellcheck` / `flake8` trong CI để bảo đảm chất lượng script shell/python.

---

**Phiên bản**: 2.2 (rút gọn & cập nhật)
**Last Updated**: 2025-11-10
**Author**: moibash — tooling team
# 📁 Filesystem Tool Documentation

## Tổng quan

Filesystem Tool là một hệ thống quản lý file thông minh được tích hợp vào Code Agent, cho phép thực hiện các thao tác file system một cách an toàn và hiệu quả thông qua giao diện chat.

## 🏗️ Architecture

### Components chính

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   Code Agent    │───▶│  function_call   │───▶│  Shell Scripts  │
│   (Gemini AI)   │    │  .py (Python)    │    │  (.sh files)    │
└─────────────────┘    └──────────────────┘    └─────────────────┘
                              │
                              ▼
                       ┌─────────────────┐
                       │   File System   │
                       │   Operations    │
                       └─────────────────┘
```

### Flow hoạt động

```
1. User Request ──▶ 2. Gemini AI ──▶ 3. Function Call ──▶ 4. Confirmation ──▶ 5. Execute ──▶ 6. Response
     ↓                     ↓                     ↓                      ↓                   ↓              ↓
   "đọc file X"      "read_file(X)"       call_filesystem_script()   User confirm       Shell script   Markdown response
```

## 🔧 Functions có sẵn

### 1. `read_file(file_path, start_line?, end_line?)`
**Mục đích**: Đọc nội dung file
**Parameters**:
- `file_path`: Đường dẫn tuyệt đối hoặc tương đối
- `start_line` (optional): Dòng bắt đầu
- `end_line` (optional): Dòng kết thúc

**Examples**:
```bash
# Đọc toàn bộ file
read_file("/path/to/file.txt")

# Đọc từ dòng 10 đến 20
read_file("/path/to/file.txt", 10, 20)
```

### 2. `create_file(file_path, content)`
**Mục đích**: Tạo file mới với nội dung
**Parameters**:
- `file_path`: Đường dẫn file mới
- `content`: Nội dung file

**Examples**:
```bash
create_file("hello.py", "print('Hello World')")
```

### 3. `update_file(file_path, content, mode?)`
**Mục đích**: Cập nhật nội dung file
**Parameters**:
- `file_path`: Đường dẫn file
- `content`: Nội dung mới
- `mode`: "overwrite" (default) hoặc "append"

**Examples**:
```bash
# Thay thế toàn bộ nội dung
update_file("config.txt", "new_config=value")

# Thêm vào cuối file
update_file("log.txt", "New log entry", "append")
```

### 4. `delete_file(file_path)`
**Mục đích**: Xóa file hoặc thư mục
**Parameters**:
- `file_path`: Đường dẫn file/thư mục cần xóa

**Examples**:
```bash
delete_file("temp.txt")
delete_file("old_folder/")
```

### 5. `rename_file(old_path, new_path)`
**Mục đích**: Đổi tên file/thư mục
**Parameters**:
- `old_path`: Đường dẫn cũ
- `new_path`: Đường dẫn mới

**Examples**:
```bash
rename_file("old_name.txt", "new_name.txt")
```

### 6. `list_files(dir_path, pattern?, recursive?)`
**Mục đích**: Liệt kê files trong thư mục
**Parameters**:
- `dir_path`: Đường dẫn thư mục
- `pattern` (optional): Pattern tìm kiếm (default: "*")
- `recursive` (optional): Tìm kiếm đệ quy (default: false)

**Examples**:
```bash
# Liệt kê tất cả files
list_files(".")

# Tìm files Python
list_files(".", "*.py")

# Tìm files đệ quy
list_files(".", "*.txt", true)
```

### 7. `search_files(dir_path, pattern, recursive?)`
**Mục đích**: Tìm kiếm files theo pattern
**Parameters**:
- `dir_path`: Thư mục bắt đầu tìm
- `pattern`: Pattern tìm kiếm
- `recursive` (optional): Tìm kiếm đệ quy

**Examples**:
```bash
search_files(".", "*.py")
search_files("/src", "test_*.js", true)
```

### 8. `shell(action, target, args?, working_dir?)`
**Mục đích**: Thực thi lệnh shell hoặc chạy script
**Parameters**:
- `action`: "command" hoặc "file"
- `target`: Lệnh shell hoặc đường dẫn file
- `args` (optional): Arguments cho file execution
- `working_dir` (optional): Thư mục làm việc

**Examples**:
```bash
# Chạy lệnh shell
shell("command", "ls -la")

# Chạy script file
shell("file", "script.py", "--verbose")
```

## 🔒 Security & Safety

### Confirmation System
Tất cả operations nguy hiểm đều yêu cầu confirmation từ user:

- ✅ **Create/Update/Delete/Rename files**
- ✅ **Execute shell commands**
- ✅ **Run script files**

### Options:
- `1`: Allow once (chỉ lần này)
- `2`: Allow always (luôn luôn cho session này)
- `3`: Cancel (hủy)

### Path Security
- ✅ Validate absolute paths
- ❌ Block access to system directories (`/etc`, `/root`)
- ✅ Prevent path traversal attacks (`../../../etc/passwd`)

## 🎨 Diff Preview Feature

### Git-style Diff Display
Khi update file, hệ thống hiển thị diff preview với màu sắc:

```
╭─ Diff Preview: file.txt
--- a/file.txt
+++ b/file.txt
@@ -1,3 +1,4 @@
 Line 1: Unchanged
-Line 2: Old content
+Line 2: New content
 Line 3: Another line
+Line 4: Added line
╰─────────────────────────────────
```

### Color Scheme
- 🔴 **Red**: Deleted lines (`-`)
- 🟢 **Green**: Added lines (`+`)
- ⚪ **Gray**: Context lines
- 🔵 **Cyan**: Hunk headers (`@@`)
- **Bold**: File headers

### Supported Modes
- **Overwrite**: Show full diff (old vs new)
- **Append**: Show only added content

## 🔄 Auto-Fix & Test Loop

### Intelligent Bug Fixing
Agent tự động phát hiện và sửa lỗi code với quy trình test & verify:

```
1. Code Analysis ──▶ 2. Identify Issues ──▶ 3. Generate Fix ──▶ 4. Auto Test ──▶ 5. Verify ──▶ 6. Success/Fail
     ↓                      ↓                      ↓                     ↓                ↓              ↓
   Read file            Syntax errors         Apply fix           Run tests       Check output    Report result
   Check logic          Logic bugs            Diff preview        Exit codes      Error analysis  Next iteration
   Performance          Security issues       Confirmation        Output validation
```

### Test Strategies by Language

#### Python Files
```bash
# Syntax check
python -m py_compile file.py

# Import test
python -c "import file"

# Unit test (if exists)
python -m pytest test_file.py

# Linting
python -m flake8 file.py
```

#### JavaScript/Node.js Files
```bash
# Syntax check
node --check file.js

# Import test
node -e "require('./file.js')"

# Linting
npx eslint file.js

# TypeScript
npx tsc --noEmit file.ts
```

#### Java Files
```bash
# Compile check
javac -cp ".:lib/*" file.java

# Run test (if main method)
java -cp ".:lib/*" file

# Maven/Gradle
mvn compile test
gradle build
```

#### Shell Scripts
```bash
# Syntax check
bash -n script.sh

# Dry run
bash -x script.sh

# Linting
shellcheck script.sh
```

### Iteration Loop (Max 3 Attempts)
```python
attempt = 1
while attempt <= 3:
    # Apply fix
    update_file(file_path, fixed_content)

    # Test the fix
    result = shell("command", test_command)

    if result.exit_code == 0:
        return "✅ Fix successful"
    else:
        # Analyze error and try different approach
        attempt += 1

return "❌ Max attempts reached, manual intervention needed"
```

### Auto-Test Workflows

#### 1. Syntax Error Fix
```
Agent: Detect syntax error in line 15
Agent: Apply fix: missing semicolon
Agent: Test: python -m py_compile file.py
Agent: ✅ Success - syntax fixed
```

#### 2. Logic Bug Fix
```
Agent: Detect division by zero in function
Agent: Apply fix: add zero check
Agent: Test: run unit tests
Agent: ✅ Success - logic fixed
```

#### 3. Import Error Fix
```
Agent: Detect missing import
Agent: Apply fix: add import statement
Agent: Test: python -c "import file"
Agent: ✅ Success - import fixed
```

## 🔧 Enhanced Shell Operations

### Best Practices for Shell Execution

#### Use Command Action (Recommended)
```bash
# ✅ Good: Use "command" action for shell commands
shell("command", "python script.py --arg value")

# ✅ Good: Use "command" action for system tools
shell("command", "grep -r 'pattern' .")

# ❌ Avoid: "file" action (deprecated)
shell("file", "script.py")  # May cause path issues
```

#### Absolute Paths Required
```bash
# ✅ Good: Always use absolute paths
shell("command", "python /full/path/to/script.py")

# ❌ Bad: Relative paths may fail
shell("command", "python script.py")  # Depends on working directory
```

#### Working Directory Management
```bash
# Set working directory explicitly
shell("command", "npm install", "", "/path/to/project")

# Change directory then execute
shell("command", "cd /tmp && ls -la")
```

### Common Shell Patterns

#### File Operations
```bash
# Find files
shell("command", "find /path -name '*.py' -type f")

# Count lines
shell("command", "wc -l /path/to/file.txt")

# Check file type
shell("command", "file /path/to/file")
```

#### Code Analysis
```bash
# Find function definitions
shell("command", "grep -rn '^def ' /path/to/code")

# Check syntax
shell("command", "python -m py_compile /path/to/file.py")

# Run tests
shell("command", "pytest /path/to/tests")
```

#### System Operations
```bash
# Check disk usage
shell("command", "df -h")

# Process management
shell("command", "ps aux | grep python")

# Network check
shell("command", "curl -I http://localhost:3000")
```

## 📈 Performance Optimization

### Optimization Principles

#### 1. Minimize Tool Calls
```bash
# ❌ Bad: Multiple small reads
read_file("large.py", 1, 10)
read_file("large.py", 11, 20)
read_file("large.py", 21, 30)

# ✅ Good: Single large read
read_file("large.py", 1, 100)
```

#### 2. Use Shell for Complex Searches
```bash
# ❌ Bad: Python loop over many files
list_files(".")
# Then read each file individually

# ✅ Good: Use shell tools
shell("command", "grep -r 'pattern' /path/to/search")
shell("command", "find /path -name '*.py' -exec wc -l {} +")
```

#### 3. Batch Operations
```bash
# ❌ Bad: Individual operations
update_file("file1.txt", "content1")
update_file("file2.txt", "content2")
update_file("file3.txt", "content3")

# ✅ Good: Batch with shell
shell("command", "echo 'content1' > file1.txt")
shell("command", "echo 'content2' > file2.txt")
shell("command", "echo 'content3' > file3.txt")
```

#### 4. Smart Caching
```bash
# Cache expensive operations
# First call: search_files(".", "*.py") - expensive
# Subsequent calls: use cached results if files unchanged
```

### Memory Management
```bash
# Handle large files in chunks
read_file("huge.log", 1, 1000)     # First 1000 lines
read_file("huge.log", 1001, 2000)  # Next chunk

# Use streaming for very large files
shell("command", "head -n 100 huge.log")  # First 100 lines
shell("command", "tail -n 100 huge.log")  # Last 100 lines
```

### Network Efficiency
```bash
# Prefer local operations over network
# Cache remote data locally when possible
# Use compression for large data transfers
```

## 🛡️ Enhanced Safety & Error Handling

### Comprehensive Error Handling

#### 1. Path Validation
```python
# Validate paths before operations
if not path.startswith("/"):
    return {"error": "Absolute path required"}

if ".." in path:
    return {"error": "Path traversal not allowed"}

if path.startswith("/etc") or path.startswith("/root"):
    return {"error": "System path access denied"}
```

#### 2. File Permission Checks
```bash
# Check permissions before operations
shell("command", "test -r /path/to/file")  # Read permission
shell("command", "test -w /path/to/file")  # Write permission
shell("command", "test -x /path/to/file")  # Execute permission
```

#### 3. Fallback Strategies
```python
# Try multiple approaches
try:
    # Primary method
    result = shell("command", "python script.py")
except:
    try:
        # Fallback method
        result = shell("command", "python3 script.py")
    except:
        # Final fallback
        result = shell("command", "/usr/bin/python script.py")
```

#### 4. Recovery Mechanisms
```bash
# Backup before destructive operations
shell("command", "cp file.txt file.txt.bak")

# Rollback on failure
if operation_failed:
    shell("command", "mv file.txt.bak file.txt")
```

### Error Types & Solutions

#### File System Errors
```
ENOENT (File not found)
├── Cause: Incorrect path or deleted file
├── Solution: Check path exists, use absolute paths
└── Prevention: Validate paths before operations

EACCES (Permission denied)
├── Cause: Insufficient permissions
├── Solution: Check file ownership, use sudo if appropriate
└── Prevention: Test permissions first

ENOSPC (No space left)
├── Cause: Disk full
├── Solution: Free up space or use different location
└── Prevention: Check disk usage before large writes
```

#### Command Execution Errors
```
Command not found
├── Cause: Tool not installed or not in PATH
├── Solution: Install tool or use full path
└── Prevention: Check tool availability first

Non-zero exit code
├── Cause: Command failed
├── Solution: Check command syntax, input validation
└── Prevention: Test commands in isolation
```

#### Network Errors
```
Connection timeout
├── Cause: Network issues or service down
├── Solution: Retry with backoff, check connectivity
└── Prevention: Implement retry logic with exponential backoff
```

## 📝 Updated Usage Examples

### Advanced Code Fixing Workflow

#### 1. Auto-Fix Python Bug
```
User: "sửa lỗi trong file utils.py"
Agent: [READ] utils.py
       Found: SyntaxError in line 25: missing colon
       [AUTO-FIX] Attempt 1/3: Add missing colon
       [TEST] python -m py_compile utils.py
       ✅ Success: Syntax error fixed
       [UPDATE] utils.py applied
```

#### 2. Multi-Language Test Suite
```
User: "test tất cả files trong project"
Agent: [SEARCH] *.py,*.js,*.java
       Found: 15 files
       [TEST] Python files: 5/5 passed
       [TEST] JavaScript files: 3/3 passed
       [TEST] Java files: 2/2 passed
       ✅ All tests passed
```

#### 3. Performance Optimization
```
User: "tối ưu performance cho file large.py"
Agent: [READ] large.py
       [ANALYZE] Found: Inefficient loops, memory leaks
       [OPTIMIZE] Apply performance fixes
       [TEST] Benchmark before/after
       ✅ Performance improved by 40%
```

### Enhanced Shell Operations

#### 4. Safe File Operations
```
User: "backup và update config files"
Agent: [SHELL] cp config.json config.json.bak
       [UPDATE] config.json (with diff preview)
       Allow? [1/2/3] 1
       ✅ Config updated safely
```

#### 5. Code Analysis Pipeline
```
User: "analyze codebase quality"
Agent: [SHELL] find . -name '*.py' -exec python -m py_compile {} \;
       [SHELL] python -m flake8 . --count --statistics
       [SHELL] python -m pytest --cov=. --cov-report=html
       📊 Quality Report: 95% coverage, 12 style issues
```

#### 6. Batch Processing with Error Handling
```
User: "update all Python files with new header"
Agent: [SEARCH] *.py
       Found: 20 files
       [BATCH] Processing files...
       File 1/20: ✅ Updated
       File 2/20: ❌ Permission denied - skipped
       File 3/20: ✅ Updated
       ...
       📋 Summary: 18/20 updated, 2 skipped
```

## 📝 Usage Examples

### Basic File Operations

#### 1. Tạo và chỉnh sửa file
```
User: "tạo file hello.py với nội dung print('Hello World')"
Agent: [CREATE] hello.py
       Content: print('Hello World')
       Allow execution? [1/2/3]
User: 1
Agent: ✅ Đã tạo file hello.py thành công
```

#### 2. Đọc và phân tích code
```
User: "đọc file main.py và giải thích function chính"
Agent: [READ] main.py
       Read 150 lines...
       Function main(): xử lý dữ liệu đầu vào...
```

#### 3. Tìm và sửa bugs
```
User: "tìm tất cả files Python và kiểm tra có bugs không"
Agent: [SEARCH] *.py
       Found: utils.py, main.py, test.py
       [READ] utils.py
       Issue found: Missing error handling
       Suggested fix: try/except block
```

### Advanced Operations

#### 4. Bulk file operations
```
User: "xóa tất cả files .tmp trong thư mục current"
Agent: [SEARCH] *.tmp
       Found: temp1.tmp, temp2.tmp, temp3.tmp
       [DELETE] temp1.tmp → Confirm → ✅
       [DELETE] temp2.tmp → Confirm → ✅
       [DELETE] temp3.tmp → Confirm → ✅
```

#### 5. Code refactoring
```
User: "refactor function process_data trong utils.py"
Agent: [READ] utils.py
       [UPDATE] utils.py (with diff preview)
       --- old code
       +++ new code
       Allow? [1/2/3]
```

#### 6. Shell operations
```
User: "chạy lệnh grep để tìm function definitions"
Agent: [SHELL] grep -rn "^def " .
       Output: utils.py:10:def process_data
               main.py:25:def main
```

## 🔧 Configuration

### Environment Variables
```bash
# Debug mode
DEBUG=1

# Max iterations
FILESYSTEM_MAX_ITERATIONS=15

# Session state
FILESYSTEM_ALWAYS_ACCEPT=false
```

### File Paths
- **Scripts**: `tools/filesystem/*.sh`
- **Main agent**: `tools/filesystem/function_call.py`
- **Environment**: `.env`
- **History**: `chat_history_filesystem.txt`

## 📊 Response Formats

### Success Response
```json
{
  "success": true,
  "content": "file content here",
  "path": "/absolute/path/to/file"
}
```

### Error Response
```json
{
  "error": "File not found: /path/to/file",
  "exit_code": 1
}
```

### Markdown Formatting
Agent responses sử dụng markdown để dễ đọc:
- **Bold** cho file names: `**main.py**`
- *Italic* cho comments: `*processing data*`
- `Inline code` cho variables: `process_data()`
- Code blocks cho examples
- Bullet lists cho multiple items

## 🐛 Troubleshooting

### Common Issues

#### 1. "Command failed" errors
```
Cause: Shell command returned non-zero exit code
Solution: Check command syntax, file permissions
```

#### 2. "File not found" errors
```
Cause: Incorrect path or file doesn't exist
Solution: Use absolute paths, check spelling
```

#### 3. "Permission denied" errors
```
Cause: No write/read permissions
Solution: Check file permissions, use sudo if needed
```

#### 4. Diff preview not showing
```
Cause: File doesn't exist or binary file
Solution: Create file first, or use text files only
```

### Debug Mode
Enable debug để xem detailed logs:
```bash
DEBUG=1 ./tools/filesystem/function_call.py "your command"
```

### Recovery Steps
1. Check file permissions: `ls -la file`
2. Verify paths: `pwd` và `ls -la`
3. Test commands manually: `grep "pattern" file`
4. Check environment: `env | grep FILESYSTEM`

## 📈 Performance Tips

### Optimize Searches
```bash
# Good: Use specific patterns
search_files(".", "*.py")

# Better: Use git grep if in git repo
shell("command", "git grep 'pattern'")

# Best: Combine with find
shell("command", "find . -name '*.py' -exec grep -l 'pattern' {} \\;")
```

### Minimize Tool Calls
```bash
# Instead of multiple reads
read_file("large_file.txt", 1, 50)  # Read first 50 lines
read_file("large_file.txt", 51, 100)  # Read next 50

# Use grep for targeted search
shell("command", "grep -n 'function_name' file.txt")
```

### Batch Operations
```bash
# Instead of individual deletes
search_files(".", "*.tmp")  # Find all first
# Then delete each found file
```

## 🔄 Integration với Main Chat

### Router Flow
```
main.sh → router.sh → filesystem/function_call.py
                    ↓
              Gemini API → Function calls → Shell scripts → File operations
```

### Session Management
- **History**: Saved in `chat_history_filesystem.txt`
- **State**: `SESSION_STATE` for always_accept
- **Environment**: Loaded from `.env`

### Error Propagation
```
Tool Error → Agent Response → User Feedback
     ↓             ↓             ↓
JSON error → Markdown → "Không thể thực hiện: [error]"
```

## 📚 Best Practices

### 1. Always Verify Before Action
```bash
# Good: Check file exists first
list_files(".")  # See what's there
read_file("target.txt")  # Then read
```

### 2. Use Absolute Paths
```bash
# Good: Explicit paths
read_file("/Users/project/src/main.py")

# Avoid: Relative paths (may change)
/read_file("main.py")  # Depends on cwd
```

### 3. Handle Large Files Carefully
```bash
# Good: Read in chunks
read_file("large.log", 1, 100)  # First 100 lines
read_file("large.log", 101, 200)  # Next chunk

# Use grep for specific content
shell("command", "grep 'ERROR' large.log")
```

### 4. Backup Important Files
```bash
# Before major changes
shell("command", "cp important.txt important.bak")
update_file("important.txt", "new content")
```

### 5. Test Commands First
```bash
# Test shell command before using
shell("command", "ls -la")  # Test basic
shell("command", "grep 'pattern' file")  # Test complex
```

## 🚀 Advanced Features

### Code Analysis Workflows
1. **Explore codebase**: `list_files(".")` → `read_file()` key files
2. **Find patterns**: `search_files(".", "*.py")` → `grep` specific functions
3. **Analyze dependencies**: `shell("command", "grep -r 'import' .")`
4. **Fix issues**: `read_file()` → `update_file()` with diff preview
5. **Test changes**: `shell("file", "test_script.py")`

### Batch Processing
```bash
# Find all Python files
search_files(".", "*.py")

# Apply changes to multiple files
for file in found_files:
    update_file(file, "new_header", "append")
```

### Integration với Git
```bash
# Check git status
shell("command", "git status")

# See diffs
shell("command", "git diff")

# Commit changes
shell("command", "git add . && git commit -m 'Updated by agent'")
```

## 📋 API Reference

### Function Signatures
```python
def read_file(file_path: str, start_line: int = None, end_line: int = None) -> Dict
def create_file(file_path: str, content: str) -> Dict
def update_file(file_path: str, content: str, mode: str = "overwrite") -> Dict
def delete_file(file_path: str) -> Dict
def rename_file(old_path: str, new_path: str) -> Dict
def list_files(dir_path: str, pattern: str = "*", recursive: bool = False) -> Dict
def search_files(dir_path: str, pattern: str, recursive: bool = False) -> Dict
def shell(action: str, target: str, args: str = "", working_dir: str = "") -> Dict
```

### Response Schema
```json
{
  "success": boolean,
  "content": "string (for read/create/update)",
  "files": ["array of file objects (for list/search)"],
  "folders": ["array of folder strings"],
  "output": "string (for shell)",
  "exit_code": number,
  "error": "string (if failed)",
  "path": "absolute path"
}
```

## 🎯 Quick Start Guide

### 1. Basic Setup
```bash
# Clone repository
git clone <repo>
cd moibash

# Make scripts executable
chmod +x tools/filesystem/*.sh
chmod +x main.sh
```

### 2. First Test
```bash
# Test basic functionality
./tools/filesystem/function_call.py "liệt kê thư mục tools"
# Should show: chat.sh, intent.sh, image_create.sh, google_search.sh
```

### 3. Interactive Usage
```bash
# Start chat interface
./main.sh

# Try commands:
# "tạo file test.txt với nội dung hello"
# "đọc file test.txt"
# "sửa file test.txt thành 'hello world'"
# "xóa file test.txt"
```

### 4. Direct API Usage
```bash
# Direct function calls
echo "1" | ./tools/filesystem/function_call.py "chạy lệnh ls -la"
echo "2" | ./tools/filesystem/function_call.py "tạo file demo.py với nội dung print('demo')"
```

## 📞 Support & Contributing

### Reporting Issues
- Check debug logs: `DEBUG=1 ./tools/filesystem/function_call.py "command"`
- Verify file permissions: `ls -la tools/filesystem/`
- Test individual scripts: `./tools/filesystem/readfile.sh /path/to/file`

### Contributing
1. Fork repository
2. Create feature branch
3. Add tests for new functionality
4. Update documentation
5. Submit pull request

---

**Version**: 2.1 (with Auto-Fix & Test Loop)
**Last Updated**: November 8, 2025
**Author**: Code Agent System
**License**: MIT