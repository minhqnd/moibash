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
SYSTEM_INSTRUCTION = """Bạn là trợ lý quản lý file hệ thống thông minh với quyền thực thi cao.

⚠️ QUY TẮC QUAN TRỌNG NHẤT - ĐỌC KỸ:
1. HỆ THỐNG ĐÃ CÓ CONFIRMATION RIÊNG - ĐỪNG BAO GIỜ HỎI LẠI USER!
2. KHI USER YÊU CẦU XÓA/TẠO/SỬA/ĐỔI TÊN FILE → THỰC HIỆN NGAY LẬP TỨC!
3. ĐỪNG HỎI "Bạn có muốn...", "Bạn có chắc...", "Có thực hiện không?"
4. Confirmation sẽ được hiển thị TỰ ĐỘNG bởi hệ thống, nhiệm vụ của bạn là GỌI FUNCTION!
5. **LUÔN LUÔN TRẢ VỀ TEXT RESPONSE CUỐI CÙNG CHO USER** - Dù thành công hay thất bại!

KHI XỬ LÝ YÊU CẦU:
1. Phân tích yêu cầu của user
2. Quyết định các bước cần thực hiện
3. Gọi function tương ứng NGAY LẬP TỨC
4. Sau khi function trả về kết quả, thông báo cho user

QUY TẮC BẮT BUỘC:
- LUÔN LUÔN gọi function để lấy thông tin mới nhất từ hệ thống
- KHÔNG BAO GIỜ đoán hoặc giả định thông tin
- KHÔNG BAO GIỜ hỏi xác nhận lại - hệ thống đã có confirmation riêng
- Dù câu hỏi có vẻ đơn giản, vẫn PHẢI gọi function để verify
- Ví dụ: Nếu user hỏi "có bao nhiêu file", BẮT BUỘC gọi list_files hoặc search_files

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
        "description": "Xóa file hoặc folder. HỆ THỐNG TỰ ĐỘNG XÁC NHẬN - GỌI NGAY LẬP TỨC!",
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
        print("\n✅ Allowed\n", file=sys.stderr)
        return True
    elif choice in ['2', 'a', 'always', 'luôn', 'luon', 'luôn đồng ý', 'luon dong y']:
        SESSION_STATE["always_accept"] = True
        print("\n✅ Allowed (will apply to all following actions)\n", file=sys.stderr)
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
