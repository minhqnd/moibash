#!/usr/bin/env python3
"""
function_call.py - Filesystem Function Calling với Gemini và Confirmation
Flow: User message → Gemini Function Calling → Confirm → Execute → Loop
"""

import os
import sys
import json
import subprocess
import unicodedata
from pathlib import Path
from typing import Dict, List, Optional, Any
import requests
import time
import re

# Constants
SCRIPT_DIR = Path(__file__).parent
ENV_FILE = SCRIPT_DIR / "../../.env"
HISTORY_FILE = SCRIPT_DIR / "../../chat_history_filesystem.txt"
MAX_ITERATIONS = int(os.environ.get('FILESYSTEM_MAX_ITERATIONS', '15'))
MAX_HISTORY_MESSAGES = 10  # Keep last 10 messages for context
GEMINI_API_URL = "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash-lite:generateContent"

# Session state for "always accept"
SESSION_STATE = {
    "always_accept": False
}

# Load environment variables
def load_env():
    """Load environment variables from .env file"""
    if ENV_FILE.exists():
        with open(ENV_FILE) as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    key, value = line.split('=', 1)
                    # Remove quotes if present
                    value = value.strip().strip('"').strip("'")
                    os.environ[key] = value

load_env()

# System instruction
SYSTEM_INSTRUCTION = """Bạn là CODE AGENT thông minh - trợ lý lập trình với quyền đọc, phân tích và sửa code.

🎯 VAI TRÒ CỦA BẠN:
- Đọc và hiểu codebase (không chỉ single file)
- Phân tích code structure, dependencies, patterns
- Tìm bugs, suggest improvements, optimize code
- Sửa code theo yêu cầu hoặc tự động fix issues
- Giải thích code một cách rõ ràng và dễ hiểu

⚠️ QUY TẮC QUAN TRỌNG NHẤT - ĐỌC KỸ:
1. HỆ THỐNG ĐÃ CÓ CONFIRMATION RIÊNG - ĐỪNG BAO GIỜ HỎI LẠI USER!
2. KHI USER YÊU CẦU XÓA/TẠO/SỬA/ĐỔI TÊN FILE → THỰC HIỆN NGAY LẬP TỨC!
3. ĐỪNG HỎI "Bạn có muốn...", "Bạn có chắc...", "Có thực hiện không?"
4. Confirmation sẽ được hiển thị TỰ ĐỘNG bởi hệ thống, nhiệm vụ của bạn là GỌI FUNCTION!
5. **LUÔN LUÔN TRẢ VỀ TEXT RESPONSE CUỐI CÙNG CHO USER** - Dù thành công hay thất bại!

🚨 QUY TẮC BẮT BUỘC CHO DELETE/RENAME:
**TUYỆT ĐỐI KHÔNG ĐƯỢC GỌI delete_file() hoặc rename_file() MÀ KHÔNG SEARCH TRƯỚC!**

❌ SAI - GỌI TRỰC TIẾP:
User: "xóa test markdown"
→ delete_file("test.md")  # SAI! Không biết file có tồn tại không, đường dẫn đúng chưa

✅ ĐÚNG - SEARCH TRƯỚC:
User: "xóa test markdown" hoặc "xóa file test.md"
→ Step 1: search_files(".", "*.md", recursive=true)  # BẮT BUỘC TÌM TRƯỚC!
→ Step 2: Kiểm tra result:
   - Nếu KHÔNG tìm thấy "test.md" → Trả lời: "❌ Không tìm thấy file test.md"
   - Nếu TÌM THẤY → Lấy absolute path từ search result
→ Step 3: delete_file("/absolute/path/to/test.md")  # Dùng absolute path từ search
→ Step 4: Trả lời: "✅ Đã xóa file test.md"

✅ ĐÚNG - VÍ DỤ KHÁC:
User: "xóa file config.json"
→ Step 1: search_files(".", "config.json", recursive=true)
→ Step 2: Nếu tìm thấy → delete_file("/path/found/config.json")
→ Step 3: Báo kết quả

User: "đổi tên old.txt thành new.txt"
→ Step 1: search_files(".", "old.txt", recursive=true)
→ Step 2: Nếu tìm thấy → rename_file("/path/found/old.txt", "new.txt")
→ Step 3: Báo kết quả

🚀 NGUYÊN TẮC HIỆU SUẤT & TỐI ƯU:
1. **Gather context FIRST, act SECOND** - Đọc files liên quan trước khi modify
2. **Don't make assumptions** - Verify bằng tools thay vì đoán
3. **Minimize tool calls** - Đọc large chunks thay vì nhiều small reads
4. **Use grep/search smartly** - Tìm pattern trước khi đọc nhiều files
5. **Plan complex tasks** - Break down thành steps, verify từng step
6. **Handle errors gracefully** - Có fallback strategy khi tool fails

⚡ OPTIMIZATION STRATEGIES:
- Dùng `shell` với grep/find thay vì read nhiều files
- Search pattern trước, chỉ đọc relevant files
- Đọc file 1 lần với large range thay vì nhiều lần small ranges
- Dùng `head`/`tail` để limit output khi chỉ cần vài dòng
- Với large files, grep specific patterns thay vì read toàn bộ

KHI XỬ LÝ YÊU CẦU:
1. Phân tích yêu cầu của user
2. **Thu thập context cần thiết TRƯỚC** (đọc files, search patterns)
3. Plan các bước thực hiện
4. **TỰ ĐỘNG thực hiện tất cả các bước** - KHÔNG cần hỏi user xác nhận bằng lời
5. Verify kết quả sau mỗi bước
6. Report kết quả cuối cùng chi tiết cho user

🎯 QUY TRÌNH TỰ ĐỘNG HÓA VỚI TEST & VERIFY:

**Khi user yêu cầu "sửa file X có lỗi" hoặc "fix bug trong file Y":**
→ Step 1: ĐỌC file để xem code (read_file)
→ Step 2: PHÂN TÍCH code để tìm bugs (syntax errors, logic errors, runtime errors)
→ Step 3: TỰ ĐỘNG SỬA file ngay lập tức với code đúng (update_file) - KHÔNG HỎI!
→ Step 4: **TEST file đã sửa** bằng cách chạy (shell):
   - Python: `python file.py` hoặc `python -m py_compile file.py`
   - JavaScript: `node file.js` hoặc `npm test`
   - Java: `javac file.java && java ClassName`
   - Shell: `bash -n file.sh` (syntax check)
→ Step 5: **KIỂM TRA OUTPUT**:
   - ✅ Nếu chạy thành công (exit code = 0) và không có errors → DONE!
   - ❌ Nếu vẫn lỗi → QUAY LẠI Step 2, phân tích lỗi mới, sửa lại (loop)
→ Step 6: **GIỚI HẠN**: Max 3 lần sửa. Nếu sau 3 lần vẫn lỗi → báo cáo user
→ Step 7: BÁO CÁO kết quả chi tiết:
   "✅ Đã sửa thành công file X:
    - Lỗi đã fix: [list]
    - Thay đổi: [changes]
    - Test result: [output]
    - Exit code: 0"

**Khi user yêu cầu "phân tích và tối ưu code":**
→ Step 1: ĐỌC file
→ Step 2: PHẢN TÍCH issues (performance, readability, bugs)
→ Step 3: TỰ ĐỘNG APPLY tất cả improvements (update_file) - KHÔNG HỎI!
→ Step 4: **TEST code sau khi optimize**
→ Step 5: **VERIFY kết quả giống như trước** (behavior không thay đổi)
→ Step 6: BÁO CÁO: "Đã tối ưu: [improvements made], Test passed ✅"

**Khi user nói "file X lỗi, không biết lỗi ở đâu":**
→ Step 1: ĐỌC file
→ Step 2: TÌM tất cả lỗi (syntax, logic, runtime)
→ Step 3: TỰ ĐỘNG SỬA tất cả lỗi tìm được (update_file) - KHÔNG HỎI!
→ Step 4: **CHẠY TEST** để verify (shell):
   ```bash
   python file.py  # hoặc node/java/etc
   ```
→ Step 5: **ĐÁNH GIÁ kết quả**:
   - Nếu chạy OK → Report success
   - Nếu còn lỗi → Sửa lại (max 3 iterations)
→ Step 6: BÁO CÁO chi tiết:
   "✅ Đã fix X lỗi trong file.py:
    1. Line 10: Typo 'returnc' → 'return'
    2. Line 5: Division by zero - added check
    3. Line 15: Type error - added isinstance check
    
    📊 Test Results:
    Output: [actual output]
    Exit code: 0
    ✅ File hoạt động đúng!"

🧪 TEST STRATEGIES:

**Xác định loại file và test command:**
- `.py` → `python file.py` hoặc `python -m pytest file.py`
- `.js` → `node file.js` hoặc `npm test`
- `.java` → `javac file.java && java ClassName`
- `.sh` → `bash -n file.sh` (syntax) hoặc `bash file.sh`
- `.rb` → `ruby file.rb`
- `.go` → `go run file.go`

**⚠️ QUAN TRỌNG - Xử lý đường dẫn file khi test:**
1. **Nếu file path là relative** (vd: "test.py", "./script.sh"):
   - PHẢI tìm absolute path trước khi chạy
   - Dùng: `shell("command", "find . -name 'filename' -type f")` 
   - Hoặc: `shell("command", "realpath filename")`
   - Sau đó dùng absolute path để execute

2. **Để test Python file:**
   ❌ KHÔNG: `shell("file", "test.py")` → Sẽ lỗi "Invalid file path"
   ✅ ĐÚNG: `shell("command", "python test.py")` → Chạy trực tiếp với command
   ✅ HOẶC: Tìm absolute path → `shell("file", "/absolute/path/test.py")`

3. **Best practice cho testing:**
   ```
   Option 1 (Recommended): Dùng shell command trực tiếp
   → shell("command", "python test.py")
   → shell("command", "node script.js")
   
   Option 2: Tìm absolute path trước
   → shell("command", "realpath test.py")  # Get absolute path
   → shell("file", "/full/path/test.py")  # Execute with absolute path
   ```

**Phân tích test output:**
1. **Exit code = 0** + no error messages → ✅ SUCCESS
2. **Exit code ≠ 0** → ❌ FAIL, đọc error message
3. **SyntaxError** → Sửa syntax
4. **TypeError/ValueError** → Sửa logic
5. **ImportError** → Thêm imports hoặc install dependencies
6. **"Invalid file path"** → Dùng absolute path hoặc shell command

**Loop until success (max 3 iterations):**
```
Iteration 1: Fix → Test (with shell command!) → If fail, analyze error
Iteration 2: Fix error from iteration 1 → Test → If fail, analyze
Iteration 3: Final fix → Test → Report result (pass/fail)
```

🔴 QUAN TRỌNG - TEST & VERIFY:
- LUÔN LUÔN test sau khi sửa code
- KHÔNG được skip testing - this is MANDATORY!
- Nếu test fail, TỰ ĐỘNG sửa lại (không hỏi user)
- Max 3 lần sửa - sau đó report nếu vẫn không thành công
- Report chi tiết: code changes + test output + exit code

🔴 QUAN TRỌNG - HÀNH ĐỘNG TỰ ĐỘNG:
- ĐỪNG hỏi "Bạn muốn tôi sửa không?" → Just DO IT!
- ĐỪNG hỏi "Tôi có nên apply changes không?" → Just APPLY!
- ĐỪNG hỏi "Có cần test không?" → Just TEST and report results!
- User chỉ cần confirm qua confirmation box của hệ thống (1/2/3)
- Nhiệm vụ của bạn là THỰC HIỆN, không phải HỎI!

QUY TẮC BẮT BUỘC:
- LUÔN LUÔN gọi function để lấy thông tin mới nhất từ hệ thống
- KHÔNG BAO GIỜ đoán hoặc giả định thông tin - verify with tools!
- KHÔNG BAO GIỜ hỏi xác nhận lại - hệ thống đã có confirmation riêng
- Dù câu hỏi có vẻ đơn giản, vẫn PHẢI gọi function để verify
- **Trước khi modify file, ĐỌC NỘI DUNG để hiểu context**
- Khi lỗi xảy ra, explain clearly và suggest alternatives

CÁC FUNCTION KHẢ DỤNG:
- read_file: Đọc nội dung file
- create_file: Tạo file mới với nội dung
- update_file: Cập nhật nội dung file (overwrite/append)
- delete_file: Xóa file hoặc folder
- rename_file: Đổi tên file/folder
- list_files: Liệt kê files trong thư mục
- search_files: Tìm kiếm files theo pattern
- shell: Thực thi lệnh shell hoặc chạy script file (thay thế cho execute_file và run_command)

ĐƯỜNG DẪN:
- Sử dụng đường dẫn tuyệt đối hoặc tương đối
- Đường dẫn tương đối sẽ được tính từ thư mục hiện tại
- Ví dụ: "./test.py", "/tmp/test.txt", "folder/file.txt"
- list_files: nếu có thể liệt kê chi tiết ra, gồm bao nhiêu file, có các file gì, đuôi exetention gì, v.v.

VÍ DỤ XỬ LÝ - LUÔN THỰC HIỆN NGAY:

User: "xóa các file txt trong folder hiện tại"
❌ SAI: "Đã tìm thấy 1 file txt. Bạn có muốn xóa không?"
✅ ĐÚNG:
→ Step 1: search_files(".", "*.txt", recursive=false)
→ Step 2: delete_file("/path/to/file1.txt")  # THỰC HIỆN NGAY, KHÔNG HỎI!
→ Step 3: delete_file("/path/to/file2.txt")
→ Trả lời: "Đã xóa thành công 2 files .txt"

User: "xóa file test.md" hoặc "xóa test markdown"
⚠️ BẮT BUỘC - PHẢI TÌM KIẾM FILE TRƯỚC KHI XÓA:
→ Step 1: search_files(".", "test.md", recursive=true) HOẶC search_files(".", "*.md", recursive=true)
   - Nếu KHÔNG TÌM THẤY file → BÁO LỖI NGAY: "❌ Không tìm thấy file test.md trong thư mục hiện tại"
   - Nếu TÌM THẤY → Tiếp tục Step 2
→ Step 2: delete_file("/absolute/path/to/test.md")  # Dùng absolute path từ search result
→ Trả lời: "✅ Đã xóa file test.md tại /absolute/path/to/test.md"

User: "xóa các file exe trong folder hiện tại và folder con"
✅ ĐÚNG:
→ Step 1: search_files(".", "*.exe", recursive=true)
→ Step 2: delete_file(path) cho từng file  # KHÔNG HỎI!
→ Trả lời: "Đã xóa thành công X files .exe"

User: "tạo file hello.py với nội dung hello world"
✅ ĐÚNG:
→ Step 1: create_file("hello.py", "print('Hello World')")  # THỰC HIỆN NGAY!
→ Trả lời: "Đã tạo file hello.py thành công"

User: "đổi tên test.txt thành backup.txt"
✅ ĐÚNG:
→ Step 1: rename_file("test.txt", "backup.txt")  # THỰC HIỆN NGAY!
→ Trả lời: "Đã đổi tên file thành công"

User: "tạo file hello.py với nội dung hello world và chạy nó"
→ Step 1: create_file("hello.py", "print('Hello World')")
→ Step 2: shell(action="file", file_path="hello.py")

User: "folder này có bao nhiêu file"
→ Step 1: list_files(".", recursive=false)
→ Trả về: số lượng files và folders

User: "tìm 5 tiến trình tốn ram nhất và kill cái đầu tiên"
→ Step 1: shell(action="command", command="ps aux --sort=-%mem | head -6")
→ Step 2: Phân tích output để lấy PID
→ Step 3: shell(action="command", command="kill -9 <PID>")

User: "liệt kê các file .txt trong thư mục này"
→ Step 1: shell(action="command", command="ls -la *.txt")

User: "copy file test.txt sang backup.txt"
→ Step 1: shell(action="command", command="cp test.txt backup.txt")

User: "file test.py bị lỗi, sửa giúp tôi" hoặc "fix bug trong file X"
✅ ĐÚNG - TỰ ĐỘNG VỚI TEST LOOP:
→ Step 1: read_file("test.py")  # ĐỌC code
→ Step 2: Phân tích tìm bugs (syntax errors, typos, logic errors)
→ Step 3: update_file("test.py", fixed_code)  # SỬA NGAY, KHÔNG HỎI!
→ Step 4: shell("command", "python test.py")  # TEST với shell command (KHÔNG dùng action="file")
→ Step 5: CHECK output & exit_code
   - If exit_code = 0 → SUCCESS! Go to Step 7
   - If exit_code ≠ 0 → Analyze error → Go to Step 3 (max 3 times)
→ Step 6: If still failing after 3 iterations → Report partial success
→ Step 7: Trả lời: "✅ Đã sửa 3 lỗi trong test.py:
  1. Line 10: Typo 'returnc' → 'return'
  2. Line 5: Division by zero - added check
  3. Line 15: Type error - added isinstance check
  
  📊 Test Result:
  Command: python test.py
  Output: Average: 0
          Processed: [30, 40, 60]
  Exit code: 0
  ✅ File chạy thành công!"

User: "file calculator.js lỗi không chạy được"
✅ ĐÚNG - AUTO FIX WITH ITERATION:
→ Iteration 1:
   read_file → find SyntaxError → fix → shell("command", "node calculator.js")
   Result: Still error "ReferenceError: multiply not defined"
→ Iteration 2:
   analyze error → add missing function → update_file → shell("command", "node calculator.js")
   Result: Still error "TypeError: Cannot read property"
→ Iteration 3:
   analyze error → fix property access → update_file → shell("command", "node calculator.js")
   Result: ✅ Success! exit_code = 0
→ Report: "✅ Fixed after 3 iterations:
   - Iteration 1: Fixed syntax error
   - Iteration 2: Added missing multiply function
   - Iteration 3: Fixed property access
   Final test: PASSED ✅"

User: "tối ưu code trong utils.py"
✅ ĐÚNG - TỰ ĐỘNG VỚI VERIFICATION:
→ Step 1: read_file("utils.py")
→ Step 2: Phân tích performance, readability issues
→ Step 3: shell("command", "python utils.py")  # Test BEFORE optimization
   Save output: "Original output: [baseline]"
→ Step 4: update_file("utils.py", optimized_code)  # APPLY NGAY!
→ Step 5: shell("command", "python utils.py")  # Test AFTER optimization
→ Step 6: COMPARE outputs - must be identical!
   - If different → ROLLBACK and report issue
   - If same → Success!
→ Trả lời: "✅ Đã tối ưu utils.py:
  - Simplified loops → 30% faster
  - Added type hints
  - Removed duplicate code
  - Better error handling
  
  📊 Verification:
  Before: [baseline output]
  After: [same output] ✅
  Behavior: UNCHANGED ✅
  Performance: IMPROVED ✅"

📚 WORKFLOWS CHO CODE ANALYSIS & DEVELOPMENT:

**1. Phân tích codebase mới:**
→ Step 1: read_file("README.md") hoặc list_files(".") để hiểu structure
→ Step 2: search_files với patterns như "*.py", "*.js" để tìm code files
→ Step 3: Đọc main files để hiểu architecture
→ Trả lời: Tổng quan về project, tech stack, structure

**2. Tìm function/class definition:**
→ Step 1: search_files(".", "pattern", recursive=true) hoặc shell grep
→ Step 2: read_file(file_chứa_definition) để xem chi tiết
→ Trả lời: Vị trí, code, và giải thích function

**3. Analyze dependencies & imports:**
→ Step 1: shell(action="command", command="grep -rn 'import\\|require\\|from' .")
→ Step 2: Đọc các file liên quan để hiểu mối quan hệ
→ Trả lời: Dependency graph, potential issues

**4. Tìm bug hoặc optimize code:**
→ Step 1: Đọc file có vấn đề
→ Step 2: Analyze code, identify issues (syntax, logic, performance)
→ Step 3: Suggest fixes với markdown code blocks
→ Step 4: Nếu user đồng ý, update_file để apply fix
→ Trả lời: Issue found, suggested fix, và kết quả

**5. Add new feature hoặc modify code:**
→ Step 1: Đọc related files để hiểu current implementation
→ Step 2: Plan changes (tránh break existing code)
→ Step 3: update_file với new code
→ Step 4: Suggest testing commands
→ Trả lời: Changes made, how to test

**6. Refactor code:**
→ Step 1: Đọc code cần refactor
→ Step 2: Identify anti-patterns, code smells
→ Step 3: Apply best practices (DRY, SOLID, etc.)
→ Step 4: update_file với refactored code
→ Trả lời: What was refactored and why

**7. Tìm usage của function:**
→ Step 1: shell(action="command", command="grep -rn 'function_name' .")
→ Step 2: List tất cả nơi function được gọi
→ Trả lời: All usages với file:line numbers

🛡️ SAFETY & ERROR HANDLING:

**Trước khi modify code:**
1. ĐỌC file để understand current implementation
2. Identify dependencies và potential impact
3. Check for edge cases
4. Plan changes carefully để avoid breaking code

**Khi tool call fails:**
1. Explain error clearly cho user
2. Suggest alternative approaches
3. Nếu file không tồn tại, check spelling hoặc list directory
4. Nếu permission denied, suggest using shell với sudo (cẩn thận)

**Output management:**
- Nếu file quá lớn, dùng `head`/`tail` để xem sample
- Dùng grep để filter specific content thay vì read all
- Warn user nếu operation có thể tốn thời gian
- Handle truncated output gracefully

**Multi-file operations:**
1. List files first để verify scope
2. Explain what will be affected
3. Execute step by step, report progress
4. If error occurs mid-way, report which files succeeded/failed

SHELL COMMANDS HỮU ÍCH:
- `grep -rn "pattern" .` - Tìm text trong all files (fast!)
- `grep -rn "pattern" --include="*.py" .` - Tìm trong specific file types
- `find . -name "*.py"` - Tìm files theo extension
- `git grep "pattern"` - Tìm trong git repo (faster nếu có git)
- `wc -l file` - Đếm lines
- `head -20 file` / `tail -20 file` - Xem first/last lines
- `cat file | grep "pattern"` - Filter content
- `ls -lh` - List với human-readable sizes
- `du -sh folder` - Check folder size

QUAN TRỌNG:
- LUÔN đọc và hiểu ngữ cảnh từ lịch sử chat trước đó
- Khi user dùng đại từ (nó, chúng, đó) - tham chiếu đến đối tượng trong câu trước
- Luôn xác nhận đường dẫn chính xác
- LUÔN hiển thị đường dẫn TUYỆT ĐỐI (absolute path) khi liệt kê files (ví dụ: /Users/minhqnd/CODE/moibash/test.exe)
- **QUAN TRỌNG NHẤT**: KHI USER YÊU CẦU XÓA/ĐỔI TÊN/CẬP NHẬT FILE - THỰC HIỆN NGAY, ĐỪNG HỎI LẠI!
- Hệ thống đã có confirmation riêng, ĐỪNG hỏi lại user trong chat response
- Với bulk operations (xóa/đổi tên nhiều file), gọi function cho TỪNG file tuần tự
- Sau khi thực thi xong, **BẮT BUỘC phải trả về text response** báo kết quả thành công/thất bại
- Nếu function call thất bại (error), **VẪN PHẢI trả về text response** giải thích lỗi cho user
- Báo lỗi rõ ràng nếu không thực hiện được
- Hiển thị kết quả chi tiết cho user với đường dẫn đầy đủ
- shell function có thể: chạy lệnh shell (action="command") hoặc execute script file (action="file")
- Có thể kết hợp nhiều lệnh với pipe: ps aux | sort -nrk 4 | head -5
- Với yêu cầu phức tạp, dùng shell để thực thi trực tiếp thay vì nhiều bước

📝 ĐỊNH DẠNG RESPONSE:
- **LUÔN SỬ DỤNG MARKDOWN** khi có thể để làm cho response dễ đọc và đẹp mắt
- Sử dụng **bold** cho tên file/thư mục/function quan trọng
- Sử dụng *italic* cho ghi chú hoặc thông tin phụ
- Sử dụng code blocks (```) cho code snippets, luôn ghi rõ language
- Sử dụng inline code (`code`) cho variable names, function names, paths
- Sử dụng bullet lists (-) cho liệt kê files/issues/suggestions
- Sử dụng numbered lists (1., 2., 3.) cho các bước hướng dẫn
- Sử dụng headings (## ###) để structure response dài
- Ví dụ code analysis response:
```
## Analysis of `main.py`

Function **`process_data()`** tại line 45:
- *Input*: `data` (list)
- *Output*: `processed` (dict)
- *Issue*: Missing error handling for empty list

**Suggested fix:**
```python
def process_data(data):
    if not data:
        return {}
    # ... existing code
```
```

🧠 CODE ANALYSIS BEST PRACTICES:
- Khi phân tích code, LUÔN đọc multiple files để có full context
- Tìm hiểu dependencies trước khi suggest changes
- Explain WHY trước khi suggest fixes
- Consider edge cases và backward compatibility
- Suggest tests khi thêm/sửa code
- Prioritize readability và maintainability over "clever" code

💡 SMART SEARCH STRATEGIES:
- **Dùng grep TRƯỚC khi read nhiều files** - Faster và efficient hơn
- Pattern: `grep -rn "function_name" .` → found in 3 files → chỉ read 3 files đó
- Với git repos: Prefer `git grep` over `grep` (faster, respects .gitignore)
- Limit search scope: `--include="*.py"` hoặc search trong specific directories
- Combine tools: `find . -name "*.py" -exec grep -l "pattern" {} \\;`

📊 CONTEXT GATHERING PRINCIPLES:
1. **Start broad, then narrow**: List directory → search pattern → read specific files
2. **Verify assumptions**: Đừng assume file exists, list/search để confirm
3. **Understand before changing**: Read file + dependencies trước khi modify
4. **Check impact**: Grep usages của function/variable before renaming
5. **Test strategy**: Suggest how to verify changes work correctly

🎯 EFFICIENCY TIPS:
- 1 grep command > 10 read_file calls
- Read large chunk once > nhiều small reads
- search_files(".", "*.py") > list_files + filter manually
- shell với pipe > nhiều separate tool calls
- Check file exists (list/search) before trying to read

🔴 QUY TẮC BẮT BUỘC VỀ TEXT RESPONSE:
- SAU MỖI FUNCTION CALL (dù thành công hay thất bại) → BẮT BUỘC TRẢ VỀ TEXT RESPONSE
- Không được dừng lại sau function call mà không có text response
- Ví dụ thành công: "Đã tìm thấy 5 files trong thư mục tools"
- Ví dụ thất bại: "Không tìm thấy thư mục 'zxcvzxcv'. Vui lòng kiểm tra lại tên thư mục."
- Text response phải tự nhiên, thân thiện với người dùng Việt Nam

VÍ DỤ ĐÚNG KHI XÓA NHIỀU FILE:
User: "xóa các file .tmp"
❌ SAI: "Bạn có chắc muốn xóa các file sau không?..."
❌ SAI: "Đã tìm thấy 3 files. Bạn có muốn xóa không?"
✅ ĐÚNG: 
→ Step 1: search_files(".", "*.tmp", recursive=false)
→ Step 2: delete_file("/path/to/test1.tmp")  # GỌI NGAY!
→ Step 3: delete_file("/path/to/test2.tmp")  # GỌI NGAY!
→ Step 4: delete_file("/path/to/test3.tmp")  # GỌI NGAY!
→ Trả lời: "Đã xóa thành công 3 files .tmp"

🚫 CẤM TUYỆT ĐỐI:
- "Bạn có muốn..."
- "Bạn có chắc chắn..."
- "Có thực hiện không..."
- "Tôi có thể xóa nếu bạn đồng ý..."
- Bất kỳ câu hỏi xác nhận nào khác

✅ CHỈ ĐƯỢC:
- Gọi function ngay lập tức
- Báo kết quả sau khi thực thi
- "Đã xóa thành công..."
- "Đã tạo file..."
- "Đã đổi tên..."

⚠️ QUY TẮC ĐẶC BIỆT CHO DELETE/RENAME:
**BẮT BUỘC PHẢI TÌM FILE TRƯỚC KHI XÓA/ĐỔI TÊN!**

Khi user nói "xóa file X" hoặc "xóa test markdown":
1. **BẮT BUỘC**: Gọi search_files() hoặc list_files() TRƯỚC để tìm file
2. Kiểm tra kết quả search:
   - Nếu KHÔNG TÌM THẤY → BÁO LỖI NGAY: "❌ Không tìm thấy file X"
   - Nếu TÌM THẤY → Lấy absolute path từ search result
3. Gọi delete_file() với absolute path từ search result
4. Báo kết quả: "✅ Đã xóa file X tại /path"

❌ TUYỆT ĐỐI KHÔNG:
- Gọi delete_file("test.md") trực tiếp mà không search trước
- Gọi rename_file() mà không verify file tồn tại

✅ ĐÚNG:
```
User: "xóa test markdown"
→ Step 1: search_files(".", "*.md", recursive=true)
→ Step 2: Kiểm tra result - nếu tìm thấy "test.md"
→ Step 3: delete_file("/absolute/path/to/test.md")
→ Step 4: Báo kết quả
```

QUY TẮC QUAN TRỌNG CHO BULK DELETE/RENAME:
- Flow bắt buộc: SEARCH/LIST → DELETE (NGAY LẬP TỨC, KHÔNG HỎI!) → TEXT RESPONSE BÁO KẾT QUẢ
- Hệ thống sẽ tự động hiển thị confirmation box cho user
- Nhiệm vụ của bạn là GỌI FUNCTION, không phải hỏi user!

📋 LUỒNG XỬ LÝ BẮT BUỘC:
1. Nhận yêu cầu từ user
2. Gọi function (read/list/search/create/delete/rename/shell)
3. Nhận kết quả từ function
4. **BẮT BUỘC: Trả về text response** tóm tắt kết quả cho user (dù thành công hay lỗi)

❌ KHÔNG BAO GIỜ:
- Dừng lại sau function call mà không có text response
- Để user thấy "Không nhận được phản hồi từ AI"
- Bỏ qua việc báo kết quả cho user"""

# Function declarations
FUNCTION_DECLARATIONS = [
    {
        "name": "read_file",
        "description": "Đọc nội dung của một file",
        "parameters": {
            "type": "object",
            "properties": {
                "file_path": {
                    "type": "string",
                    "description": "Đường dẫn đến file cần đọc (tuyệt đối hoặc tương đối)"
                }
            },
            "required": ["file_path"]
        }
    },
    {
        "name": "create_file",
        "description": "Tạo file mới với nội dung. HỆ THỐNG TỰ ĐỘNG XÁC NHẬN - GỌI NGAY LẬP TỨC!",
        "parameters": {
            "type": "object",
            "properties": {
                "file_path": {
                    "type": "string",
                    "description": "Đường dẫn file cần tạo"
                },
                "content": {
                    "type": "string",
                    "description": "Nội dung của file"
                }
            },
            "required": ["file_path", "content"]
        }
    },
    {
        "name": "update_file",
        "description": "Cập nhật nội dung file. HỆ THỐNG TỰ ĐỘNG XÁC NHẬN - GỌI NGAY LẬP TỨC!",
        "parameters": {
            "type": "object",
            "properties": {
                "file_path": {
                    "type": "string",
                    "description": "Đường dẫn file cần cập nhật"
                },
                "content": {
                    "type": "string",
                    "description": "Nội dung mới"
                },
                "mode": {
                    "type": "string",
                    "description": "Mode: 'overwrite' (ghi đè) hoặc 'append' (thêm vào cuối)",
                    "enum": ["overwrite", "append"]
                }
            },
            "required": ["file_path", "content"]
        }
    },
    {
        "name": "delete_file",
        "description": "Xóa file hoặc folder. ⚠️ BẮT BUỘC: PHẢI gọi search_files() hoặc list_files() TRƯỚC để tìm absolute path, sau đó mới gọi delete_file() với absolute path từ search result. KHÔNG được gọi delete_file() trực tiếp với relative path!",
        "parameters": {
            "type": "object",
            "properties": {
                "file_path": {
                    "type": "string",
                    "description": "Đường dẫn file/folder cần xóa"
                }
            },
            "required": ["file_path"]
        }
    },
    {
        "name": "rename_file",
        "description": "Đổi tên file hoặc folder. HỆ THỐNG TỰ ĐỘNG XÁC NHẬN - GỌI NGAY LẬP TỨC!",
        "parameters": {
            "type": "object",
            "properties": {
                "old_path": {
                    "type": "string",
                    "description": "Đường dẫn cũ"
                },
                "new_path": {
                    "type": "string",
                    "description": "Đường dẫn mới"
                }
            },
            "required": ["old_path", "new_path"]
        }
    },
    {
        "name": "list_files",
        "description": "Liệt kê files và folders trong một thư mục",
        "parameters": {
            "type": "object",
            "properties": {
                "dir_path": {
                    "type": "string",
                    "description": "Đường dẫn thư mục (mặc định là thư mục hiện tại)"
                },
                "pattern": {
                    "type": "string",
                    "description": "Pattern để lọc files (ví dụ: '*.py', '*.txt'). Mặc định '*' (tất cả)"
                },
                "recursive": {
                    "type": "string",
                    "description": "'true' để list đệ quy, 'false' chỉ list thư mục hiện tại",
                    "enum": ["true", "false"]
                }
            }
        }
    },
    {
        "name": "search_files",
        "description": "Tìm kiếm files theo pattern trong thư mục (đệ quy)",
        "parameters": {
            "type": "object",
            "properties": {
                "dir_path": {
                    "type": "string",
                    "description": "Đường dẫn thư mục tìm kiếm (mặc định là thư mục hiện tại)"
                },
                "name_pattern": {
                    "type": "string",
                    "description": "Pattern tên file (ví dụ: '*.exe', 'test*.py')"
                },
                "recursive": {
                    "type": "string",
                    "description": "'true' để tìm đệ quy, 'false' chỉ tìm trong thư mục hiện tại",
                    "enum": ["true", "false"]
                }
            },
            "required": ["name_pattern"]
        }
    },
    {
        "name": "shell",
        "description": "Thực thi lệnh shell hoặc chạy script file. HỆ THỐNG TỰ ĐỘNG XÁC NHẬN CHO LỆNH NGUY HIỂM - GỌI NGAY LẬP TỨC!",
        "parameters": {
            "type": "object",
            "properties": {
                "action": {
                    "type": "string",
                    "description": "'command' để chạy lệnh shell, 'file' để chạy script file",
                    "enum": ["command", "file"]
                },
                "command": {
                    "type": "string",
                    "description": "Lệnh shell cần thực thi (chỉ dùng khi action='command'). Ví dụ: 'ls -la', 'ps aux | head -10', 'rm file.txt'"
                },
                "file_path": {
                    "type": "string",
                    "description": "Đường dẫn file script cần chạy (chỉ dùng khi action='file'). Hỗ trợ Python, Bash, Node.js"
                },
                "args": {
                    "type": "string",
                    "description": "Arguments cho script (optional, chỉ dùng khi action='file')"
                },
                "working_dir": {
                    "type": "string",
                    "description": "Working directory (optional, mặc định là thư mục hiện tại)"
                }
            },
            "required": ["action"]
        }
    }
]

# Debug mode
DEBUG = os.environ.get('DEBUG', '').lower() in ('true', '1', 'yes')

def debug_print(*args, **kwargs):
    """Print debug messages to stderr"""
    if DEBUG:
        print("[DEBUG]", *args, file=sys.stderr, **kwargs)

# ===== UI/ANSI helpers =====
# ANSI color/style codes
RESET = "\033[0m"
BOLD = "\033[1m"
DIM = "\033[2m"
RED = "\033[0;31m"
GREEN = "\033[0;32m"
YELLOW = "\033[0;33m"
BLUE = "\033[0;34m"
MAGENTA = "\033[0;35m"
CYAN = "\033[0;36m"
WHITE = "\033[1;37m"
GRAY = "\033[0;90m"

ANSI_PATTERN = re.compile(r"\x1b\[[0-9;]*m")

def strip_ansi(s: str) -> str:
    """Remove ANSI escape sequences from a string."""
    return ANSI_PATTERN.sub("", s or "")

def visible_len(s: str) -> int:
    """Length of string as displayed (excluding ANSI codes)."""
    return len(strip_ansi(s))

def color_for_func(func_name: str) -> str:
    """Pick a color for a given function name."""
    return {
        "read_file": CYAN,
        "create_file": GREEN,
        "update_file": YELLOW,
        "delete_file": RED,
        "rename_file": MAGENTA,
        "list_files": BLUE,
        "search_files": BLUE,
        "shell": GRAY,
        "execute_file": GRAY,
        "run_command": GRAY,
    }.get(func_name, WHITE)

def resolve_dir_path(dir_path: str) -> (str, Optional[str]):
    """Resolve a directory path; if it doesn't exist, try simple, safe corrections.
    Returns: (resolved_dir_path, note) where note is a human message if corrected.
    """
    if not dir_path or dir_path.strip() == "":
        return ".", None

    p = Path(dir_path)
    if p.exists():
        return dir_path, None

    # Try pluralization fix: add/remove trailing 's'
    if not dir_path.endswith('s'):
        cand = dir_path + 's'
        if Path(cand).exists():
            return cand, f"Directory '{dir_path}' not found. Using '{cand}'."
    else:
        cand = dir_path[:-1]
        if Path(cand).exists():
            return cand, f"Directory '{dir_path}' not found. Using '{cand}'."

    # Case-insensitive exact match in current directory
    try:
        entries = [e for e in os.listdir('.') if os.path.isdir(e)]
        for e in entries:
            if e.lower() == dir_path.lower():
                return e, f"Directory '{dir_path}' not found. Using '{e}'."
        # Substring heuristic: pick shortest containing dir
        candidates = [e for e in entries if dir_path.lower() in e.lower()]
        if candidates:
            best = sorted(candidates, key=len)[0]
            return best, f"Directory '{dir_path}' not found. Using '{best}'."
    except Exception:
        pass

    return dir_path, None

def sanitize_for_display(text: str, max_length: int = 100) -> str:
    """
    Sanitize text for display, preventing sensitive data exposure
    Returns truncated text without exposing full content
    """
    if not text:
        return "N/A"
    
    # Truncate long content
    if len(text) > max_length:
        return text[:max_length] + "..."
    
    return text

def load_chat_history() -> List[Dict]:
    """Load chat history from file"""
    if not HISTORY_FILE.exists():
        return []
    
    try:
        with open(HISTORY_FILE, 'r', encoding='utf-8') as f:
            content = f.read().strip()
            if not content:
                return []
            return json.loads(content)
    except Exception as e:
        debug_print(f"Error loading history: {e}")
        return []

def save_chat_history(history: List[Dict]):
    """Save chat history to file"""
    try:
        # Keep only last MAX_HISTORY_MESSAGES
        if len(history) > MAX_HISTORY_MESSAGES * 2:  # *2 because we have user+model pairs
            history = history[-(MAX_HISTORY_MESSAGES * 2):]
        
        with open(HISTORY_FILE, 'w', encoding='utf-8') as f:
            json.dump(history, f, ensure_ascii=False, indent=2)
    except Exception as e:
        debug_print(f"Error saving history: {e}")

def get_terminal_width() -> int:
    """Get terminal width with fallback"""
    try:
        import shutil
        terminal_width = shutil.get_terminal_size().columns
        return min(terminal_width - 2, 120)
    except:
        return 94

def print_box(lines: List[str], title: str = None):
    """
    Print a box with content lines
    Args:
        lines: List of strings to print inside the box
        title: Optional title for the box
    """
    BORDER_WIDTH = get_terminal_width()
    border_top = "╭" + "─" * BORDER_WIDTH + "╮"
    border_bottom = "╰" + "─" * BORDER_WIDTH + "╯"
    
    print(border_top, file=sys.stderr, flush=True)
    
    if title:
        # Print title line (respect visible width ignoring ANSI)
        tlen = visible_len(title)
        padding = BORDER_WIDTH - tlen - 2
        if padding < 0:
            # Hard truncate title to fit
            cut = tlen - (BORDER_WIDTH - 2)
            # naive truncate by removing last characters from raw title (safe as title is small)
            raw_no_ansi = strip_ansi(title)
            raw_no_ansi = raw_no_ansi[: max(0, (BORDER_WIDTH - 5))] + "..." if cut > 0 else raw_no_ansi
            title = raw_no_ansi
            tlen = visible_len(title)
            padding = max(0, BORDER_WIDTH - tlen - 2)
        print(f"│ {title}{' ' * padding} │", file=sys.stderr, flush=True)
        # Empty line after title
        # Empty line: "│" + spaces + "│" = BORDER_WIDTH + 2
        # So: 1 + spaces + 1 = BORDER_WIDTH + 2
        # Therefore: spaces = BORDER_WIDTH
        print(f"│{' ' * BORDER_WIDTH}│", file=sys.stderr, flush=True)
    
    for line in lines:
        # Calculate padding using visible length (exclude ANSI)
        vlen = visible_len(line)
        padding = BORDER_WIDTH - vlen - 2
        if padding < 0:
            # Truncate visible part to fit
            raw = strip_ansi(line)
            raw = raw[: max(0, BORDER_WIDTH - 5)] + "..."
            line = raw
            vlen = visible_len(line)
            padding = max(0, BORDER_WIDTH - vlen - 2)
        print(f"│ {line}{' ' * padding} │", file=sys.stderr, flush=True)
    
    print(border_bottom, file=sys.stderr, flush=True)

def print_tool_call(func_name: str, args: Dict[str, Any], result: Optional[Dict[str, Any]] = None):
    """Print tool call information with border and optional result"""
    # Stop spinner if it's running (from router.sh)
    spinner_pid = os.environ.get('MOIBASH_SPINNER_PID')
    if spinner_pid:
        try:
            # Clear the spinner line first
            print("\r\033[K", end='', file=sys.stderr, flush=True)
            # Kill spinner process
            subprocess.run(['kill', spinner_pid], stderr=subprocess.DEVNULL)
        except:
            pass
    
    BORDER_WIDTH = get_terminal_width()
    
    # Function name with prefix (no emoji)
    prefixes = {
        "read_file": "[READ]",
        "create_file": "[CREATE]",
        "update_file": "[UPDATE]",
        "delete_file": "[DELETE]",
        "rename_file": "[RENAME]",
        "list_files": "[LIST]",
        "search_files": "[SEARCH]",
        "shell": "[SHELL]",
        "execute_file": "[EXEC]",
        "run_command": "[RUN]"
    }
    prefix = prefixes.get(func_name, "[TOOL]")
    
    # Format function name and args
    if func_name == "shell":
        action = args.get("action", "")
        if action == "command":
            display = f"{prefix} {args.get('command', 'N/A')}"
        elif action == "file":
            display = f"{prefix} Execute: {args.get('file_path', 'N/A')}"
        else:
            display = f"{prefix}"
    elif func_name == "list_files":
        dir_path = args.get("dir_path", ".")
        pattern = args.get("pattern", "*")
        display = f"{prefix} {dir_path}"
        if pattern != "*":
            display += f" (pattern: {pattern})"
    elif func_name == "search_files":
        pattern = args.get("name_pattern", "*")
        dir_path = args.get("dir_path", ".")
        display = f"{prefix} '{pattern}' in {dir_path}"
    elif func_name == "rename_file":
        display = f"{prefix} {args.get('old_path', '')} → {args.get('new_path', '')}"
    elif func_name in ["read_file", "create_file", "update_file", "delete_file"]:
        display = f"{prefix} {args.get('file_path', 'N/A')}"
    elif func_name == "execute_file":
        display = f"{prefix} {args.get('file_path', 'N/A')}"
    elif func_name == "run_command":
        display = f"{prefix} {args.get('command', 'N/A')}"
    else:
        display = f"{prefix} {func_name}"
    
    # Truncate if too long (consider visible length)
    if visible_len(display) > BORDER_WIDTH - 4:
        # Keep room for the prefix symbols and ellipsis
        raw = display
        if visible_len(raw) > BORDER_WIDTH - 7:
            raw = raw[: (BORDER_WIDTH - 10)] + "..."
        display = raw

    # Colorize header line
    color = color_for_func(func_name)
    line = f"{GREEN}✓{RESET} {color}{BOLD}{display}{RESET}"
    # Use print_box helper
    print_box([line], title=None)

def print_tool_result(func_name: str, result: Dict[str, Any]):
    """Print result box AFTER the tool was executed - for ALL functions."""
    lines = []
    BORDER_WIDTH = get_terminal_width()
    
    # Check for errors
    if isinstance(result, dict) and "error" in result:
        lines.append(f"{RED}{BOLD}✗ Error:{RESET} {result['error']}")
        if isinstance(result, dict) and "exit_code" in result:
            lines.append(f"  Exit code: {WHITE}{result['exit_code']}{RESET}")
    # Search/List files results
    elif func_name in ("search_files", "list_files") and isinstance(result, dict):
        # Optional note when path auto-corrected
        if isinstance(result, dict) and result.get("note"):
            lines.append(f"{YELLOW}Note:{RESET} {result['note']}")
        files = result.get("files")
        if isinstance(files, list):
            lines.append(f"{CYAN}{BOLD}Found {len(files)} matching file(s){RESET}")
            lines.append("")
            # Show up to first 5 files
            preview = files[:5]
            for fpath in preview:
                if isinstance(fpath, dict):
                    display = fpath.get('path', str(fpath))
                else:
                    display = str(fpath)
                # Truncate if too long
                if len(display) > BORDER_WIDTH - 6:
                    display = display[:BORDER_WIDTH - 9] + "..."
                lines.append(f"  - {WHITE}{display}{RESET}")
            if len(files) > len(preview):
                lines.append(f"  ... (+{len(files)-len(preview)} more)")
        else:
            lines.append(str(result))
    # Read file result
    elif func_name == "read_file" and isinstance(result, dict):
        content = result.get("content", "")
        if isinstance(content, str):
            content_lines = content.splitlines()
            lines.append(f"{CYAN}{BOLD}Read {len(content_lines)} line(s){RESET}")
            if content_lines:
                first = content_lines[0]
                if len(first) > BORDER_WIDTH - 14:
                    first = first[:BORDER_WIDTH - 17] + "..."
                lines.append(f"  First: {first}")
        else:
            lines.append("(No content)")
    # Create/Update/Delete/Rename results
    elif func_name in ("create_file", "update_file", "delete_file", "rename_file"):
        if isinstance(result, dict):
            if "success" in result:
                ok = bool(result["success"]) if isinstance(result["success"], bool) else False
                status = f"{GREEN}✓ Success{RESET}" if ok else f"{RED}✗ Failed{RESET}"
                lines.append(f"{BOLD}{status}{RESET}")
            if "message" in result:
                lines.append(result["message"])
            if "path" in result:
                path = result['path']
                if len(path) > BORDER_WIDTH - 10:
                    path = path[:BORDER_WIDTH - 13] + "..."
                lines.append(f"  Path: {WHITE}{path}{RESET}")
        else:
            lines.append(str(result))
    # Shell/Execute results
    elif func_name in ("shell", "execute_file", "run_command"):
        if isinstance(result, dict):
            if "success" in result:
                ok = bool(result["success"]) if isinstance(result["success"], bool) else False
                status = f"{GREEN}✓ Success{RESET}" if ok else f"{RED}✗ Failed{RESET}"
                lines.append(f"{BOLD}{status}{RESET}")
            if "output" in result:
                output = result["output"]
                # Truncate long output
                if len(output) > 200:
                    output = output[:200] + "..."
                # Show first few lines
                output_lines = output.splitlines()[:5]
                for out_line in output_lines:
                    if len(out_line) > BORDER_WIDTH - 4:
                        out_line = out_line[:BORDER_WIDTH - 7] + "..."
                    lines.append(f"  {DIM}{out_line}{RESET}")
                if len(output.splitlines()) > 5:
                    lines.append("  ... (output truncated)")
            if "exit_code" in result:
                lines.append(f"  Exit code: {WHITE}{result['exit_code']}{RESET}")
        else:
            lines.append(str(result))
    # Generic fallback
    else:
        raw = json.dumps(result, ensure_ascii=False) if isinstance(result, dict) else str(result)
        if len(raw) > BORDER_WIDTH - 4:
            raw = raw[:BORDER_WIDTH - 7] + "..."
        lines.append(raw)
    
    # Print using print_box
    # Colorful title for results
    tcolor = color_for_func(func_name)
    title_text = f"{tcolor}{BOLD}{func_name.upper().replace('_', ' ')} RESULT{RESET}"
    print_box(lines, title=title_text)

def show_diff_preview(old_content: str, new_content: str, file_path: str) -> None:
    """
    Hiển thị diff preview giống git với màu đỏ (xóa) và xanh (thêm)
    """
    import difflib
    
    old_lines = old_content.splitlines(keepends=True)
    new_lines = new_content.splitlines(keepends=True)
    
    # Generate unified diff
    diff = difflib.unified_diff(
        old_lines,
        new_lines,
        fromfile=f"a/{file_path}",
        tofile=f"b/{file_path}",
        lineterm=''
    )
    
    print(f"\n{BOLD}{CYAN}╭─ Diff Preview: {file_path}{RESET}", file=sys.stderr)
    
    line_count = 0
    max_preview_lines = 50  # Giới hạn số dòng hiển thị
    
    for line in diff:
        if line_count >= max_preview_lines:
            print(f"{YELLOW}... (showing first {max_preview_lines} lines){RESET}", file=sys.stderr)
            break
            
        line = line.rstrip('\n')
        
        if line.startswith('---') or line.startswith('+++'):
            # File headers
            print(f"{BOLD}{line}{RESET}", file=sys.stderr)
        elif line.startswith('@@'):
            # Hunk header
            print(f"{CYAN}{line}{RESET}", file=sys.stderr)
        elif line.startswith('-'):
            # Deleted line
            print(f"{RED}{line}{RESET}", file=sys.stderr)
        elif line.startswith('+'):
            # Added line
            print(f"{GREEN}{line}{RESET}", file=sys.stderr)
        else:
            # Context line
            print(f"{GRAY}{line}{RESET}", file=sys.stderr)
        
        line_count += 1
    
    print(f"{BOLD}{CYAN}╰{'─' * 60}{RESET}\n", file=sys.stderr)

def get_confirmation(action: str, details: Dict[str, Any], is_batch: bool = False) -> bool:
    """
    Yêu cầu xác nhận từ user cho các thao tác nguy hiểm
    Returns: True nếu user đồng ý, False nếu từ chối
    
    Note: This function intentionally displays operation details to stderr for user confirmation.
    All sensitive data is sanitized via sanitize_for_display() before display.
    This is not logging - it is an interactive confirmation prompt.
    """
    # Nếu đã chọn "always accept", tự động chấp nhận
    if SESSION_STATE["always_accept"]:
        return True
    
    lines = []
    
    # Format thông tin dựa trên action (with sanitization)
    if action == "create_file":
        file_path = details.get('file_path', '')
        safe_path = sanitize_for_display(file_path, 60)
        lines.append(f"[CREATE] {safe_path}")
        content = sanitize_for_display(details.get('content', ''), 50)
        lines.append(f"  Content: {content}")
    elif action == "update_file":
        file_path = details.get('file_path', '')
        safe_path = sanitize_for_display(file_path, 60)
        mode = details.get('mode', 'overwrite')
        lines.append(f"[UPDATE] {safe_path}")
        lines.append(f"  Mode: {mode}")
        
        # Show diff preview if file exists and we have new content
        try:
            file_obj = Path(file_path)
            if file_obj.exists() and file_obj.is_file():
                old_content = file_obj.read_text()
                
                if mode == "overwrite":
                    new_content = details.get('content', '')
                elif mode == "append":
                    # For append mode, show what will be added
                    new_content = old_content + '\n' + details.get('content', '')
                else:
                    new_content = details.get('content', '')
                
                # Show diff preview FIRST (ở trên)
                show_diff_preview(old_content, new_content, safe_path)
                
                # Then show confirmation box (ở dưới - dễ nhìn hơn)
                lines.append("")
                lines.append("Allow execution?")
                lines.append("")
                lines.append("  1. Yes, allow once")
                lines.append("  2. Yes, allow always")
                lines.append("  3. No, cancel (esc)")
                lines.append("")
                
                confirm_title = f"{YELLOW}{BOLD}? CONFIRM ACTION{RESET}"
                print_box(lines, title=confirm_title)
                
                print("Choice: ", end='', file=sys.stderr, flush=True)
                
                # Get user choice
                try:
                    choice = input().strip().lower()
                except EOFError:
                    print("\n❌ Đã hủy thao tác (EOF)", file=sys.stderr)
                    return False
                except KeyboardInterrupt:
                    print("\n❌ Đã hủy thao tác (Ctrl+C)", file=sys.stderr)
                    raise
                
                # Process choice
                if choice in ['1', 'y', 'yes', 'đồng ý', 'dong y', 'có', 'co']:
                    print("\n✅ User Allowed\n", file=sys.stderr)
                    return True
                elif choice in ['2', 'a', 'always', 'luôn', 'luon', 'luôn đồng ý', 'luon dong y']:
                    SESSION_STATE["always_accept"] = True
                    print("\n✅ User Allowed (will apply to all following actions)\n", file=sys.stderr)
                    return True
                else:
                    print("\n❌ Cancelled\n", file=sys.stderr)
                    return False
        except Exception as e:
            debug_print(f"Error showing diff: {e}")
            # Fall through to normal confirmation
    elif action == "delete_file":
        file_path = details.get('file_path', '')
        safe_path = sanitize_for_display(file_path, 60)
        lines.append(f"[DELETE] {safe_path}")
    elif action == "rename_file":
        old_path = sanitize_for_display(details.get('old_path', ''), 60)
        new_path = sanitize_for_display(details.get('new_path', ''), 60)
        lines.append("[RENAME]")
        lines.append(f"  From: {old_path}")
        lines.append(f"  To: {new_path}")
    elif action == "shell":
        shell_action = details.get('action', '')
        if shell_action == "command":
            command = sanitize_for_display(details.get('command', ''), 60)
            lines.append(f"[SHELL] {command}")
        elif shell_action == "file":
            file_path = sanitize_for_display(details.get('file_path', ''), 60)
            lines.append(f"[EXEC] {file_path}")
            if details.get('args'):
                args = sanitize_for_display(details.get('args', ''), 50)
                lines.append(f"  Args: {args}")
        if details.get('working_dir'):
            working_dir = sanitize_for_display(details.get('working_dir', ''), 55)
            lines.append(f"  Working dir: {working_dir}")
    
    lines.append("")
    lines.append("Allow execution?")
    lines.append("")
    lines.append("  1. Yes, allow once")
    lines.append("  2. Yes, allow always")
    lines.append("  3. No, cancel (esc)")
    lines.append("")
    
    # Print using print_box (highlight title)
    confirm_title = f"{YELLOW}{BOLD}? CONFIRM ACTION{RESET}"
    print_box(lines, title=confirm_title)
    print("Choice: ", end='', file=sys.stderr, flush=True)
    
    # Đọc input từ user
    try:
        choice = input().strip().lower()
    except EOFError:
        print("\n❌ Đã hủy thao tác (EOF)", file=sys.stderr)
        return False
    except KeyboardInterrupt:
        print("\n❌ Đã hủy thao tác (Ctrl+C)", file=sys.stderr)
        # Re-raise to allow proper cleanup
        raise
    
    # Xử lý lựa chọn
    if choice in ['1', 'y', 'yes', 'đồng ý', 'dong y', 'có', 'co']:
        print("\n✅ User Allowed\n", file=sys.stderr)
        return True
    elif choice in ['2', 'a', 'always', 'luôn', 'luon', 'luôn đồng ý', 'luon dong y']:
        SESSION_STATE["always_accept"] = True
        print("\n✅ User Allowed (will apply to all following actions)\n", file=sys.stderr)
        return True
    else:
        print("\n❌ Cancelled\n", file=sys.stderr)
        return False

def call_filesystem_script(script_name: str, *args) -> Dict[str, Any]:
    """Call individual filesystem script and parse JSON response"""
    script_path = SCRIPT_DIR / f"{script_name}.sh"
    
    if not script_path.exists():
        return {"error": f"{script_name}.sh not found"}
    
    try:
        # Filter out empty strings from args
        cmd_args = [str(script_path)] + [str(arg) for arg in args if arg]
        debug_print(f"Calling: {' '.join(cmd_args)}")
        
        result = subprocess.run(
            cmd_args,
            capture_output=True,
            text=True,
            check=False
        )
        
        debug_print(f"Exit code: {result.returncode}")
        debug_print(f"Stdout: {result.stdout[:500]}")
        debug_print(f"Stderr: {result.stderr[:500]}")
        
        if result.returncode != 0:
            # Try to parse stdout as JSON first (script might return structured error)
            try:
                parsed = json.loads(result.stdout)
                if isinstance(parsed, dict) and "error" in parsed:
                    # Extract clean error message from nested JSON
                    return {"error": parsed["error"], "exit_code": result.returncode}
            except (json.JSONDecodeError, KeyError):
                pass
            
            # Fallback to raw stderr/stdout
            err_msg = (result.stderr or "").strip() or (result.stdout or "").strip() or "Command failed"
            return {"error": err_msg, "exit_code": result.returncode}
        
        # Try to parse JSON response
        try:
            return json.loads(result.stdout)
        except json.JSONDecodeError:
            # If not JSON, return as text
            return {"result": result.stdout.strip()}
            
    except Exception as e:
        debug_print(f"Exception: {str(e)}")
        return {"error": str(e)}

def handle_function_call(func_name: str, args: Dict[str, Any]) -> Dict[str, Any]:
    """Handle function call with confirmation for dangerous operations"""
    debug_print(f"Function: {func_name}")
    debug_print(f"Args: {json.dumps(args, ensure_ascii=False)}")
    
    # BẮT BUỘC: LUÔN HIỆN TOOL HEADER TRƯỚC KHI THỰC THI
    # Điều này giúp kiểm soát và theo dõi mọi function call
    print_tool_call(func_name, args)
    
    # Execute function
    result = None
    
    # Các function KHÔNG cần confirmation - thực thi ngay và hiển thị kết quả
    if func_name == "read_file":
        file_path = args.get("file_path", "")
        result = call_filesystem_script("readfile", file_path)
        print_tool_result(func_name, result)
        
    elif func_name == "list_files":
        dir_path = args.get("dir_path", ".")
        resolved_dir, note = resolve_dir_path(dir_path)
        pattern = args.get("pattern", "*")
        recursive = args.get("recursive", "false")
        result = call_filesystem_script("listfiles", resolved_dir, pattern, recursive)
        if isinstance(result, dict) and note:
            result["note"] = note
        print_tool_result(func_name, result)
        
    elif func_name == "search_files":
        dir_path = args.get("dir_path", ".")
        name_pattern = args.get("name_pattern", "*")
        recursive = args.get("recursive", "true")
        resolved_dir, note = resolve_dir_path(dir_path)
        result = call_filesystem_script("searchfiles", resolved_dir, name_pattern, recursive)
        if isinstance(result, dict) and note:
            result["note"] = note
        print_tool_result(func_name, result)
        
    # Functions cần confirmation - confirm sau đó thực thi và hiển thị result
    elif func_name == "create_file":
        if not get_confirmation(func_name, args):
            return {"error": "User cancelled", "cancelled": True}
        file_path = args.get("file_path", "")
        content = args.get("content", "")
        result = call_filesystem_script("createfile", file_path, content)
        print_tool_result(func_name, result)
        
    elif func_name == "update_file":
        if not get_confirmation(func_name, args):
            return {"error": "User cancelled", "cancelled": True}
        file_path = args.get("file_path", "")
        content = args.get("content", "")
        mode = args.get("mode", "overwrite")
        result = call_filesystem_script("updatefile", file_path, content, mode)
        print_tool_result(func_name, result)
        
    elif func_name == "delete_file":
        if not get_confirmation(func_name, args):
            return {"error": "User cancelled", "cancelled": True}
        file_path = args.get("file_path", "")
        result = call_filesystem_script("deletefile", file_path)
        print_tool_result(func_name, result)
        
    elif func_name == "rename_file":
        if not get_confirmation(func_name, args):
            return {"error": "User cancelled", "cancelled": True}
        old_path = args.get("old_path", "")
        new_path = args.get("new_path", "")
        result = call_filesystem_script("renamefile", old_path, new_path)
        print_tool_result(func_name, result)
        
    elif func_name == "shell":
        if not get_confirmation(func_name, args):
            return {"error": "User cancelled", "cancelled": True}
        action = args.get("action", "command")
        working_dir = args.get("working_dir", "")
        
        if action == "command":
            command = args.get("command", "")
            result = call_filesystem_script("shell", "command", command, "", working_dir)
        elif action == "file":
            file_path = args.get("file_path", "")
            exec_args = args.get("args", "")
            result = call_filesystem_script("shell", "file", file_path, exec_args, working_dir)
        else:
            result = {"error": "Invalid action for shell. Use 'command' or 'file'."}
        print_tool_result(func_name, result)
    
    # Backward compatibility
    elif func_name == "execute_file":
        if not get_confirmation(func_name, args):
            return {"error": "User cancelled", "cancelled": True}
        file_path = args.get("file_path", "")
        exec_args = args.get("args", "")
        working_dir = args.get("working_dir", "")
        result = call_filesystem_script("shell", "file", file_path, exec_args, working_dir)
        print_tool_result(func_name, result)
    
    elif func_name == "run_command":
        if not get_confirmation(func_name, args):
            return {"error": "User cancelled", "cancelled": True}
        command = args.get("command", "")
        working_dir = args.get("working_dir", "")
        result = call_filesystem_script("shell", "command", command, "", working_dir)
        print_tool_result(func_name, result)
    
    else:
        result = {"error": f"Unknown function: {func_name}"}
        print_tool_result(func_name, result)
    
    debug_print(f"Result: {json.dumps(result, ensure_ascii=False)[:500]}")
    return result

def call_gemini_api(conversation: List[Dict], api_key: str) -> Optional[Dict]:
    """Call Gemini API with conversation history"""
    payload = {
        "contents": conversation,
        "tools": [{"functionDeclarations": FUNCTION_DECLARATIONS}],
        "systemInstruction": {
            "parts": [{"text": SYSTEM_INSTRUCTION}]
        }
    }
    
    try:
        debug_print("Calling Gemini API...")
        response = requests.post(
            f"{GEMINI_API_URL}?key={api_key}",
            json=payload,
            timeout=30
        )
        response.raise_for_status()
        return response.json()
    except Exception as e:
        debug_print(f"API Error: {str(e)}")
        return None

def parse_response(response: Dict) -> tuple:
    """
    Parse Gemini response
    Returns: (response_type, value, extra)
    Types: FUNCTION_CALL, TEXT, NO_RESPONSE, ERROR
    """
    if not response:
        return ("ERROR", "No response from API", None)
    
    candidates = response.get("candidates", [])
    if not candidates:
        # Check for promptFeedback blocking
        prompt_feedback = response.get("promptFeedback", {})
        block_reason = prompt_feedback.get("blockReason")
        if block_reason:
            debug_print(f"Blocked by safety: {block_reason}")
            return ("ERROR", f"Request blocked: {block_reason}", None)
        return ("NO_RESPONSE", None, response)
    
    candidate = candidates[0]
    
    # Check if candidate was blocked
    finish_reason = candidate.get("finishReason")
    if finish_reason and finish_reason not in ("STOP", "MAX_TOKENS"):
        debug_print(f"Unusual finish reason: {finish_reason}")
        # Continue anyway to check for partial content
    
    content = candidate.get("content", {})
    parts = content.get("parts", [])
    
    # Check for function call
    for part in parts:
        if "functionCall" in part:
            func_call = part["functionCall"]
            func_name = func_call.get("name", "")
            func_args = func_call.get("args", {})
            return ("FUNCTION_CALL", func_name, func_args)
    
    # Check for text response
    for part in parts:
        if "text" in part:
            return ("TEXT", part["text"], None)
    
    # No content but check finish reason
    if finish_reason:
        debug_print(f"No content with finish_reason: {finish_reason}")
        return ("NO_RESPONSE", None, {"finishReason": finish_reason, "candidate": candidate})
    
    return ("NO_RESPONSE", None, response)

def main():
    """Main entry point"""
    try:
        # Get user message
        if len(sys.argv) < 2:
            print("❌ Lỗi: Vui lòng cung cấp yêu cầu về file!", file=sys.stderr)
            sys.exit(1)
        
        user_message = sys.argv[1]
        debug_print(f"User message: {user_message}")
    
        # Check API key
        api_key = os.environ.get("GEMINI_API_KEY")
        if not api_key:
            print("❌ Lỗi: Chưa thiết lập GEMINI_API_KEY!", file=sys.stderr)
            sys.exit(1)
        
        # Load chat history for context (DISABLED to avoid stale data)
        # chat_history = load_chat_history()
        # debug_print(f"Loaded {len(chat_history)} messages from history")
        chat_history = []  # Always start fresh
        
        # Initialize conversation with history + new message
        conversation = [
            {
                "role": "user",
                "parts": [{"text": user_message}]
            }
        ]
        
        # Multi-turn conversation loop
        tool_calls_made = 0
        
        while tool_calls_made < MAX_ITERATIONS:
            # Call Gemini API
            response = call_gemini_api(conversation, api_key)
            
            # Parse response
            response_type, value, extra = parse_response(response)
            debug_print(f"Response type: {response_type}")
            
            # Special handling: if NO_RESPONSE after a function call, provide fallback message
            if response_type == "NO_RESPONSE" and tool_calls_made > 0:
                # Gemini didn't respond after function call - create a fallback message
                last_turn = conversation[-1] if conversation else None
                if last_turn and last_turn.get("role") == "function":
                    func_response = last_turn["parts"][0]["functionResponse"]
                    func_name = func_response["name"]
                    func_result = func_response["response"]["content"]
                    
                    # Generate a simple fallback message based on result
                    if isinstance(func_result, dict):
                        if "error" in func_result:
                            fallback_msg = f"Đã xảy ra lỗi: {func_result['error']}"
                        elif func_name in ("list_files", "search_files"):
                            files = func_result.get("files", [])
                            fallback_msg = f"Tìm thấy {len(files)} file/thư mục."
                        elif func_name == "read_file":
                            fallback_msg = "Đã đọc file thành công."
                        elif func_name in ("create_file", "update_file"):
                            fallback_msg = "Đã lưu file thành công."
                        elif func_name == "delete_file":
                            fallback_msg = "Đã xóa file thành công."
                        elif func_name == "rename_file":
                            fallback_msg = "Đã đổi tên file thành công."
                        else:
                            fallback_msg = "Thao tác đã hoàn thành."
                    else:
                        fallback_msg = "Thao tác đã hoàn thành."
                    
                    print(fallback_msg)
                    sys.exit(0)
            
            if response_type == "FUNCTION_CALL":
                tool_calls_made += 1
                func_name = value
                func_args = extra
                
                # Execute function (với confirmation nếu cần)
                func_result = handle_function_call(func_name, func_args)
                
                # Add model response with function call to conversation
                conversation.append({
                    "role": "model",
                    "parts": [{
                        "functionCall": {
                            "name": func_name,
                            "args": func_args
                        }
                    }]
                })
                
                # Add function response to conversation
                conversation.append({
                    "role": "function",
                    "parts": [{
                        "functionResponse": {
                            "name": func_name,
                            "response": {
                                "content": func_result
                            }
                        }
                    }]
                })
                
                # Continue loop for Gemini to process function response
                continue
                
            elif response_type == "TEXT":
                # Final response from Gemini
                print(value)
                
                # Save chat history (DISABLED - not needed without context memory)
                # new_messages = conversation[len(chat_history):]
                # updated_history = chat_history + new_messages
                # save_chat_history(updated_history)
                
                sys.exit(0)
                
            elif response_type == "NO_RESPONSE":
                # Debug: print full response to understand what's happening
                if DEBUG and extra:
                    debug_print(f"NO_RESPONSE details: {json.dumps(extra, ensure_ascii=False, indent=2)}")
                print("❌ Không nhận được phản hồi từ AI. Vui lòng thử lại hoặc bật DEBUG=1 để xem chi tiết.", file=sys.stderr)
                sys.exit(1)
                
            elif response_type == "ERROR":
                print(f"❌ Lỗi: {value}", file=sys.stderr)
                sys.exit(1)
        
            print(f"⚠️ Đã đạt giới hạn số lượng function calls ({MAX_ITERATIONS})", file=sys.stderr)
            sys.exit(1)
    
    except KeyboardInterrupt:
        print("\n\n❌ Đã hủy bởi user (Ctrl+C)", file=sys.stderr)
        sys.exit(130)  # Standard exit code for Ctrl+C
    except Exception as e:
        print(f"❌ Lỗi không mong đợi: {str(e)}", file=sys.stderr)
        if DEBUG:
            import traceback
            traceback.print_exc(file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()
