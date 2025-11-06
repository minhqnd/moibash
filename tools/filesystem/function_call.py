#!/usr/bin/env python3
"""
function_call.py - Filesystem Function Calling với Gemini và Confirmation
Flow: User message → Gemini Function Calling → Confirm → Execute → Loop
"""

import os
import sys
import json
import subprocess
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
→ Trả lời: "Có X file .exe: path1, path2..."

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
- Chấp nhận luôn yêu cầu của user, không cần xác nhận lại trừ khi thao tác nguy hiểm
- Với bulk operations (đổi tên/xóa nhiều file), xử lý tuần tự
- Báo lỗi rõ ràng nếu không thực hiện được
- Hiển thị kết quả chi tiết cho user
- shell function có thể: chạy lệnh shell (action="command") hoặc execute script file (action="file")
- Có thể kết hợp nhiều lệnh với pipe: ps aux | sort -nrk 4 | head -5
- Với yêu cầu phức tạp, dùng shell để thực thi trực tiếp thay vì nhiều bước"""

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

def print_tool_call(func_name: str, args: Dict[str, Any]):
    """Print tool call information with border"""
    border = "╭" + "─" * 94 + "╮"
    bottom = "╰" + "─" * 94 + "╯"
    
    print(border, file=sys.stderr)
    
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
    
    print(f"│ {display:<92} │", file=sys.stderr)
    print(bottom, file=sys.stderr)

def get_confirmation(action: str, details: Dict[str, Any]) -> bool:
    """
    Yêu cầu xác nhận từ user cho các thao tác nguy hiểm
    Returns: True nếu user đồng ý, False nếu từ chối
    """
    # Nếu đã chọn "always accept", tự động chấp nhận
    if SESSION_STATE["always_accept"]:
        return True
    
    # Hiển thị thông tin thao tác
    print("\n" + "="*60, file=sys.stderr)
    print("⚠️  CẦN XÁC NHẬN THAO TÁC", file=sys.stderr)
    print("="*60, file=sys.stderr)
    
    # Format thông tin dựa trên action
    if action == "create_file":
        print(f"📝 Tạo file: {details.get('file_path', 'N/A')}", file=sys.stderr)
        content_preview = details.get('content', '')[:100]
        print(f"   Nội dung: {content_preview}...", file=sys.stderr)
    elif action == "update_file":
        print(f"✏️  Cập nhật file: {details.get('file_path', 'N/A')}", file=sys.stderr)
        print(f"   Mode: {details.get('mode', 'overwrite')}", file=sys.stderr)
    elif action == "delete_file":
        print(f"🗑️  Xóa: {details.get('file_path', 'N/A')}", file=sys.stderr)
    elif action == "rename_file":
        print(f"📝 Đổi tên:", file=sys.stderr)
        print(f"   Từ: {details.get('old_path', 'N/A')}", file=sys.stderr)
        print(f"   Sang: {details.get('new_path', 'N/A')}", file=sys.stderr)
    elif action == "shell":
        shell_action = details.get('action', '')
        if shell_action == "command":
            print(f"⚡ Chạy lệnh: {details.get('command', 'N/A')}", file=sys.stderr)
        elif shell_action == "file":
            print(f"▶️  Chạy file: {details.get('file_path', 'N/A')}", file=sys.stderr)
            if details.get('args'):
                print(f"   Arguments: {details.get('args')}", file=sys.stderr)
        if details.get('working_dir'):
            print(f"   Working dir: {details.get('working_dir')}", file=sys.stderr)
    
    print("\nTùy chọn:", file=sys.stderr)
    print("  y/yes/đồng ý  - Đồng ý thực hiện", file=sys.stderr)
    print("  a/always/luôn - Luôn đồng ý (cho cả session)", file=sys.stderr)
    print("  n/no/từ chối  - Từ chối (hủy thao tác)", file=sys.stderr)
    print("="*60, file=sys.stderr)
    print("Lựa chọn của bạn: ", end='', file=sys.stderr, flush=True)
    
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
    if choice in ['y', 'yes', 'đồng ý', 'dong y', 'có', 'co']:
        print("✅ Đã chấp nhận\n", file=sys.stderr)
        return True
    elif choice in ['a', 'always', 'luôn', 'luon', 'luôn đồng ý', 'luon dong y']:
        SESSION_STATE["always_accept"] = True
        print("✅ Đã chọn luôn đồng ý cho session này\n", file=sys.stderr)
        return True
    else:
        print("❌ Đã từ chối thao tác\n", file=sys.stderr)
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
    
    # Print tool call
    print_tool_call(func_name, args)
    
    # Các function cần confirmation
    needs_confirmation = ["create_file", "update_file", "delete_file", "rename_file", "shell", "execute_file", "run_command"]
    
    # Kiểm tra và yêu cầu confirmation nếu cần
    if func_name in needs_confirmation:
        if not get_confirmation(func_name, args):
            return {
                "error": "User từ chối thao tác",
                "cancelled": True
            }
    
    # Thực thi function
    if func_name == "read_file":
        file_path = args.get("file_path", "")
        result = call_filesystem_script("readfile", file_path)
        
    elif func_name == "create_file":
        file_path = args.get("file_path", "")
        content = args.get("content", "")
        result = call_filesystem_script("createfile", file_path, content)
        
    elif func_name == "update_file":
        file_path = args.get("file_path", "")
        content = args.get("content", "")
        mode = args.get("mode", "overwrite")
        result = call_filesystem_script("updatefile", file_path, content, mode)
        
    elif func_name == "delete_file":
        file_path = args.get("file_path", "")
        result = call_filesystem_script("deletefile", file_path)
        
    elif func_name == "rename_file":
        old_path = args.get("old_path", "")
        new_path = args.get("new_path", "")
        result = call_filesystem_script("renamefile", old_path, new_path)
        
    elif func_name == "list_files":
        dir_path = args.get("dir_path", ".")
        pattern = args.get("pattern", "*")
        recursive = args.get("recursive", "false")
        result = call_filesystem_script("listfiles", dir_path, pattern, recursive)
        
    elif func_name == "search_files":
        dir_path = args.get("dir_path", ".")
        name_pattern = args.get("name_pattern", "*")
        recursive = args.get("recursive", "true")
        result = call_filesystem_script("searchfiles", dir_path, name_pattern, recursive)
        
    elif func_name == "shell":
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
    
    # Backward compatibility for old function names
    elif func_name == "execute_file":
        # Map to shell with action="file"
        file_path = args.get("file_path", "")
        exec_args = args.get("args", "")
        working_dir = args.get("working_dir", "")
        result = call_filesystem_script("shell", "file", file_path, exec_args, working_dir)
    
    elif func_name == "run_command":
        # Map to shell with action="command"
        command = args.get("command", "")
        working_dir = args.get("working_dir", "")
        result = call_filesystem_script("shell", "command", command, "", working_dir)
    
    else:
        result = {"error": f"Unknown function: {func_name}"}
    
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
