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

# Constants
SCRIPT_DIR = Path(__file__).parent
ENV_FILE = SCRIPT_DIR / "../../.env"
HISTORY_FILE = SCRIPT_DIR / "../../chat_history_filesystem.txt"
MAX_ITERATIONS = int(os.environ.get('FILESYSTEM_MAX_ITERATIONS', '15'))
MAX_HISTORY_MESSAGES = 10  # Keep last 10 messages for context
GEMINI_API_URL = "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent"

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
SYSTEM_INSTRUCTION = """Bạn là trợ lý quản lý file hệ thống thông minh với khả năng ghi nhớ ngữ cảnh cuộc trò chuyện.

KHI XỬ LÝ YÊU CẦU:
1. QUAN TRỌNG: Luôn xem xét lịch sử chat trước đó để hiểu ngữ cảnh
2. Nếu user dùng từ "nó", "chúng", "đó", "kia" - tham chiếu đến đối tượng trong câu trước
3. Nếu user nói "xóa cho tôi" mà không chỉ rõ - xem xét câu hỏi trước để biết xóa gì
4. Phân tích và quyết định các bước cần thực hiện
5. Gọi function tương ứng với đường dẫn chính xác
6. Xử lý kết quả và thông báo cho user

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

VÍ DỤ XỬ LÝ VỚI NGỮ CẢNH:
User: "có file exe nào trong folder hiện tại và folder con không"
→ Step 1: search_files(".", "*.exe", recursive=true)
→ Trả lời: "Có X file .exe: /path/tuyệt/đối/file1.exe, /path/tuyệt/đối/file2.exe..." (LUÔN hiển thị đường dẫn tuyệt đối)

User: "xóa cho tôi" (tiếp theo câu trên)
→ HIỂU NGỮ CẢNH: User muốn xóa các file .exe vừa tìm được
→ Step 1: Với mỗi file .exe, delete_file(path)

User: "xóa các file exe trong folder hiện tại và folder con"
→ Step 1: search_files(".", "*.exe", recursive=true)
→ Step 2: Với mỗi file, delete_file(path)

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
- Sau khi thực thi xong, báo kết quả thành công/thất bại
- Báo lỗi rõ ràng nếu không thực hiện được
- Hiển thị kết quả chi tiết cho user với đường dẫn đầy đủ
- shell function có thể: chạy lệnh shell (action="command") hoặc execute script file (action="file")
- Có thể kết hợp nhiều lệnh với pipe: ps aux | sort -nrk 4 | head -5
- Với yêu cầu phức tạp, dùng shell để thực thi trực tiếp thay vì nhiều bước

VÍ DỤ ĐÚNG KHI XÓA NHIỀU FILE:
User: "xóa các file .tmp"
❌ SAI: "Bạn có chắc muốn xóa các file sau không?..."
✅ ĐÚNG: 
→ Step 1: search_files(".", "*.tmp", recursive=false)  # LUÔN tìm/list trước, dù đã có trong context
→ Step 2: delete_file("/path/to/test1.tmp")
→ Step 3: delete_file("/path/to/test2.tmp")
→ Step 4: delete_file("/path/to/test3.tmp")
→ Trả lời: "Đã xóa thành công 3 files .tmp"

QUY TẮC QUAN TRỌNG CHO BULK DELETE/RENAME:
- Dù user vừa hỏi "có file X nào không" ở câu trước, khi user nói "xóa file X" thì VẪN PHẢI gọi search_files/list_files lại
- Lý do: Để user thấy rõ tool đang tìm kiếm trước khi xóa (tăng tính minh bạch)
- Flow bắt buộc: SEARCH/LIST → DELETE → REPORT RESULT"""

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
        "description": "Tạo file mới với nội dung. CẦN XÁC NHẬN từ user.",
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
        "description": "Cập nhật nội dung file. CẦN XÁC NHẬN từ user.",
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
        "description": "Xóa file hoặc folder. CẦN XÁC NHẬN từ user.",
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
        "description": "Đổi tên file hoặc folder. CẦN XÁC NHẬN từ user.",
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
        "description": "Thực thi lệnh shell hoặc chạy script file. CẦN XÁC NHẬN từ user cho các lệnh nguy hiểm.",
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

def display_width(text: str) -> int:
    """Calculate display width of text including emojis (emojis count as 2)"""
    import unicodedata
    width = 0
    for char in text:
        if unicodedata.east_asian_width(char) in ('F', 'W'):
            width += 2  # Full-width and wide characters
        else:
            width += 1
    return width

def pad_to_width(text: str, target_width: int) -> str:
    """Pad text to target display width, accounting for emojis"""
    current_width = display_width(text)
    if current_width >= target_width:
        return text
    return text + ' ' * (target_width - current_width)

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
    border = "╭" + "─" * BORDER_WIDTH + "╮"
    bottom = "╰" + "─" * BORDER_WIDTH + "╯"
    CONTENT_WIDTH = BORDER_WIDTH
    
    # Print border
    print(border, file=sys.stderr, flush=True)
    
    # Function name with icon
    icons = {
        "read_file": "📖",
        "create_file": "📝",
        "update_file": "✏️",
        "delete_file": "🗑️",
        "rename_file": "📝",
        "list_files": "📁",
        "search_files": "🔍",
        "shell": "⚡",
        "execute_file": "▶️",
        "run_command": "⚡"
    }
    icon = icons.get(func_name, "🔧")
    
    # Format function name and args
    if func_name == "shell":
        action = args.get("action", "")
        if action == "command":
            display = f"{icon}  Shell: {args.get('command', 'N/A')}"
        elif action == "file":
            display = f"{icon}  Shell: Execute {args.get('file_path', 'N/A')}"
        else:
            display = f"{icon}  Shell"
    elif func_name == "execute_file":
        display = f"{icon}  ExecuteFile: {args.get('file_path', 'N/A')}"
    elif func_name == "run_command":
        display = f"{icon}  RunCommand: {args.get('command', 'N/A')}"
    elif func_name == "list_files":
        dir_path = args.get("dir_path", ".")
        recursive = args.get("recursive", "false")
        pattern = args.get("pattern", "*")
        display = f"{icon}  ListFiles: {dir_path}"
        if pattern != "*":
            display += f" (pattern: {pattern})"
    elif func_name == "search_files":
        pattern = args.get("name_pattern", "*")
        dir_path = args.get("dir_path", ".")
        display = f"{icon}  FindFiles: '{pattern}' within {dir_path}"
    elif func_name == "read_file":
        display = f"{icon}  ReadFile: {args.get('file_path', 'N/A')}"
    elif func_name == "create_file":
        display = f"{icon}  CreateFile: {args.get('file_path', 'N/A')}"
    elif func_name == "update_file":
        display = f"{icon}  UpdateFile: {args.get('file_path', 'N/A')}"
    elif func_name == "delete_file":
        display = f"{icon}  DeleteFile: {args.get('file_path', 'N/A')}"
    elif func_name == "rename_file":
        display = f"{icon}  RenameFile: {args.get('old_path', '')} → {args.get('new_path', '')}"
    else:
        display = f"{icon}  {func_name}"
    
    # Truncate if too long, otherwise pad to width
    if display_width(display) > CONTENT_WIDTH - 4:
        # Truncate carefully considering emoji width
        truncated = ""
        current_w = 0
        for char in display:
            char_width = 2 if unicodedata.east_asian_width(char) in ('F', 'W') else 1
            if current_w + char_width > CONTENT_WIDTH - 7:
                break
            truncated += char
            current_w += char_width
        display = truncated + "..."
    
    line_content = f"│ ✓ {display} "
    padding_needed = CONTENT_WIDTH - display_width(line_content)
    print(f"{line_content}{' ' * padding_needed} │", file=sys.stderr, flush=True)
    
    # Print result if provided
    if result:
        print(f"│{' ' * CONTENT_WIDTH} │", file=sys.stderr, flush=True)
        
        # Format result based on function type
        if func_name == "search_files" or func_name == "list_files":
            if "files" in result:
                files = result["files"]
                count = len(files) if isinstance(files, list) else 0
                line = f"│    Found {count} matching file(s) "
                padding = CONTENT_WIDTH - display_width(line)
                print(f"{line}{' ' * padding} │", file=sys.stderr, flush=True)
        elif func_name == "read_file":
            if "content" in result:
                content = result["content"]
                lines = content.count('\n') + 1 if content else 0
                line = f"│    Read {lines} line(s) "
                padding = CONTENT_WIDTH - display_width(line)
                print(f"{line}{' ' * padding} │", file=sys.stderr, flush=True)
    
    print(bottom, file=sys.stderr, flush=True)

def print_tool_result(func_name: str, result: Dict[str, Any]):
    """Print result box AFTER the tool was executed - for ALL functions."""
    BORDER_WIDTH = get_terminal_width()
    border = "╭" + "─" * BORDER_WIDTH + "╮"
    bottom = "╰" + "─" * BORDER_WIDTH + "╯"
    CONTENT_WIDTH = BORDER_WIDTH

    def line(text: str = ""):
        pad = CONTENT_WIDTH - display_width(f"│ {text} ")
        print(f"│ {text}{' ' * pad}  │", file=sys.stderr)

    print(border, file=sys.stderr)
    
    # Icon cho từng loại function
    summary_icon = {
        "read_file": "📖",
        "list_files": "📁",
        "search_files": "🔍",
        "create_file": "✅",
        "update_file": "✅",
        "delete_file": "✅",
        "rename_file": "✅",
        "shell": "✅",
        "execute_file": "✅",
        "run_command": "✅"
    }.get(func_name, "🔧")
    
    line(f"{summary_icon}  Result")
    line()

    # Check for errors
    if isinstance(result, dict) and "error" in result:
        line(f"❌ Error: {result['error']}")
    # Search/List files results
    elif func_name in ("search_files", "list_files") and isinstance(result, dict):
        files = result.get("files")
        if isinstance(files, list):
            line(f"Found {len(files)} matching file(s)")
            # Show up to first 5 files (absolute paths)
            preview = files[:5]
            for fpath in preview:
                # Handle both string paths and dict objects
                if isinstance(fpath, dict):
                    display = fpath.get('path', str(fpath))
                else:
                    display = str(fpath)
                    
                if display_width(display) > CONTENT_WIDTH - 4:
                    truncated = ""
                    current_w = 0
                    for ch in display:
                        ch_w = 2 if unicodedata.east_asian_width(ch) in ('F','W') else 1
                        if current_w + ch_w > CONTENT_WIDTH - 7:
                            break
                        truncated += ch
                        current_w += ch_w
                    display = truncated + "..."
                line(f"- {display}")
            if len(files) > len(preview):
                line(f"… (+{len(files)-len(preview)} more)")
        else:
            line(str(result))
    # Read file result
    elif func_name == "read_file" and isinstance(result, dict):
        content = result.get("content", "")
        if isinstance(content, str):
            lines = content.splitlines()
            line(f"Read {len(lines)} line(s)")
            if lines:
                first = lines[0]
                if display_width(first) > CONTENT_WIDTH - 12:
                    first = first[:CONTENT_WIDTH-15] + "..."
                line(f"First: {first}")
        else:
            line("(No content)")
    # Create/Update/Delete/Rename results
    elif func_name in ("create_file", "update_file", "delete_file", "rename_file"):
        if isinstance(result, dict):
            if "success" in result:
                status = "✓ Success" if result["success"] else "✗ Failed"
                line(status)
            if "message" in result:
                line(result["message"])
            if "path" in result:
                line(f"Path: {result['path']}")
        else:
            line(str(result))
    # Shell/Execute results
    elif func_name in ("shell", "execute_file", "run_command"):
        if isinstance(result, dict):
            if "success" in result:
                status = "✓ Success" if result["success"] else "✗ Failed"
                line(status)
            if "output" in result:
                output = result["output"]
                # Truncate long output
                if len(output) > 200:
                    output = output[:200] + "..."
                # Show first few lines
                output_lines = output.splitlines()[:5]
                for out_line in output_lines:
                    if display_width(out_line) > CONTENT_WIDTH - 4:
                        out_line = out_line[:CONTENT_WIDTH-7] + "..."
                    line(out_line)
                if len(output.splitlines()) > 5:
                    line("… (output truncated)")
            if "exit_code" in result:
                line(f"Exit code: {result['exit_code']}")
        else:
            line(str(result))
    # Generic fallback
    else:
        raw = json.dumps(result, ensure_ascii=False) if isinstance(result, dict) else str(result)
        if display_width(raw) > CONTENT_WIDTH - 1:
            raw = raw[:CONTENT_WIDTH-4] + "..."
        line(raw)

    print(bottom, file=sys.stderr)

def get_confirmation(action: str, details: Dict[str, Any], is_batch: bool = False) -> bool:
    """
    Yêu cầu xác nhận từ user cho các thao tác nguy hiểm
    Returns: True nếu user đồng ý, False nếu từ chối
    
    Note: This function intentionally displays operation details to stderr for user confirmation.
    All sensitive data is sanitized via sanitize_for_display() before display.
    This is not logging - it's an interactive confirmation prompt.
    """
    # Nếu đã chọn "always accept", tự động chấp nhận
    if SESSION_STATE["always_accept"]:
        return True
    
    BORDER_WIDTH = get_terminal_width()
    border = "╭" + "─" * BORDER_WIDTH + "╮"
    bottom = "╰" + "─" * BORDER_WIDTH + "╯"
    CONTENT_WIDTH = BORDER_WIDTH
    
    # Print confirmation box
    print(border, file=sys.stderr)
    line = "│ ? Confirm Action "
    padding = CONTENT_WIDTH - display_width(line)
    print(f"{line}{' ' * padding} │", file=sys.stderr)
    print(f"│{' ' * CONTENT_WIDTH} │", file=sys.stderr)
    
    # Format thông tin dựa trên action (with sanitization)
    if action == "create_file":
        file_path = details.get('file_path', '')
        safe_path = sanitize_for_display(file_path, 60)
        line = f"│  📝 Create: {safe_path} "
        padding = CONTENT_WIDTH - display_width(line)
        print(f"{line}{' ' * padding} │", file=sys.stderr)
        content = sanitize_for_display(details.get('content', ''), 50)
        line = f"│     Content: {content} "
        padding = CONTENT_WIDTH - display_width(line)
        print(f"{line}{' ' * padding} │", file=sys.stderr)
    elif action == "update_file":
        file_path = details.get('file_path', '')
        safe_path = sanitize_for_display(file_path, 60)
        mode = details.get('mode', 'overwrite')
        line = f"│  ✏️  Update: {safe_path} "
        padding = CONTENT_WIDTH - display_width(line)
        print(f"{line}{' ' * padding}  │", file=sys.stderr)
        line = f"│     Mode: {mode} "
        padding = CONTENT_WIDTH - display_width(line)
        print(f"{line}{' ' * padding} │", file=sys.stderr)
    elif action == "delete_file":
        file_path = details.get('file_path', '')
        safe_path = sanitize_for_display(file_path, 60)
        line = f"│  🗑️  Delete: {safe_path} "
        padding = CONTENT_WIDTH - display_width(line)
        print(f"{line}{' ' * padding}  │", file=sys.stderr)
    elif action == "rename_file":
        old_path = sanitize_for_display(details.get('old_path', ''), 60)
        new_path = sanitize_for_display(details.get('new_path', ''), 60)
        line = "│  📝 Rename: "
        padding = CONTENT_WIDTH - display_width(line)
        print(f"{line}{' ' * padding} │", file=sys.stderr)
        line = f"│     From: {old_path} "
        padding = CONTENT_WIDTH - display_width(line)
        print(f"{line}{' ' * padding} │", file=sys.stderr)
        line = f"│     To: {new_path} "
        padding = CONTENT_WIDTH - display_width(line)
        print(f"{line}{' ' * padding} │", file=sys.stderr)
    elif action == "shell":
        shell_action = details.get('action', '')
        if shell_action == "command":
            command = sanitize_for_display(details.get('command', ''), 60)
            line = f"│  ⚡ Shell: {command} "
            padding = CONTENT_WIDTH - display_width(line)
            print(f"{line}{' ' * padding} │", file=sys.stderr)
        elif shell_action == "file":
            file_path = sanitize_for_display(details.get('file_path', ''), 60)
            line = f"│  ▶️  Execute: {file_path} "
            padding = CONTENT_WIDTH - display_width(line)
            print(f"{line}{' ' * padding} │", file=sys.stderr)
            if details.get('args'):
                args = sanitize_for_display(details.get('args', ''), 50)
                line = f"│     Args: {args} "
                padding = CONTENT_WIDTH - display_width(line)
                print(f"{line}{' ' * padding} │", file=sys.stderr)
        if details.get('working_dir'):
            working_dir = sanitize_for_display(details.get('working_dir', ''), 55)
            line = f"│     Working dir: {working_dir} "
            padding = CONTENT_WIDTH - display_width(line)
            print(f"{line}{' ' * padding} │", file=sys.stderr)
    
    print(f"│{' ' * CONTENT_WIDTH} │", file=sys.stderr)
    line = "│ Allow execution? "
    padding = CONTENT_WIDTH - display_width(line)
    print(f"{line}{' ' * padding} │", file=sys.stderr)
    print(f"│{' ' * CONTENT_WIDTH} │", file=sys.stderr)
    line = "│ ● 1. Yes, allow once "
    padding = CONTENT_WIDTH - display_width(line)
    print(f"{line}{' ' * padding} │", file=sys.stderr)
    line = "│   2. Yes, allow always "
    padding = CONTENT_WIDTH - display_width(line)
    print(f"{line}{' ' * padding} │", file=sys.stderr)
    line = "│   3. No, cancel (esc) "
    padding = CONTENT_WIDTH - display_width(line)
    print(f"{line}{' ' * padding} │", file=sys.stderr)
    print(f"│{' ' * CONTENT_WIDTH} │", file=sys.stderr)
    print(bottom, file=sys.stderr)
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
            return {"error": result.stderr or "Command failed"}
        
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
        pattern = args.get("pattern", "*")
        recursive = args.get("recursive", "false")
        result = call_filesystem_script("listfiles", dir_path, pattern, recursive)
        print_tool_result(func_name, result)
        
    elif func_name == "search_files":
        dir_path = args.get("dir_path", ".")
        name_pattern = args.get("name_pattern", "*")
        recursive = args.get("recursive", "true")
        result = call_filesystem_script("searchfiles", dir_path, name_pattern, recursive)
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
        return ("NO_RESPONSE", None, None)
    
    content = candidates[0].get("content", {})
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
    
    return ("NO_RESPONSE", None, None)

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
        
        # Load chat history for context
        chat_history = load_chat_history()
        debug_print(f"Loaded {len(chat_history)} messages from history")
        
        # Initialize conversation with history + new message
        conversation = chat_history + [
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
                
                # Save chat history (exclude initial history, only new conversation)
                new_messages = conversation[len(chat_history):]
                updated_history = chat_history + new_messages
                save_chat_history(updated_history)
                
                sys.exit(0)
                
            elif response_type == "NO_RESPONSE":
                print("❌ Không nhận được phản hồi từ AI", file=sys.stderr)
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
