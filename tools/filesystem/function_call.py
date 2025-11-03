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

# Constants
SCRIPT_DIR = Path(__file__).parent
ENV_FILE = SCRIPT_DIR / "../../.env"
MAX_ITERATIONS = int(os.environ.get('FILESYSTEM_MAX_ITERATIONS', '15'))
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
SYSTEM_INSTRUCTION = """Bạn là trợ lý quản lý file hệ thống thông minh.

KHI XỬ LÝ YÊU CẦU:
1. Hiểu rõ yêu cầu của user về file operations
2. Phân tích và quyết định các bước cần thực hiện
3. Gọi function tương ứng với đường dẫn chính xác
4. Xử lý kết quả và thông báo cho user

CÁC FUNCTION KHẢ DỤNG:
- read_file: Đọc nội dung file
- create_file: Tạo file mới với nội dung
- update_file: Cập nhật nội dung file (overwrite/append)
- delete_file: Xóa file hoặc folder
- rename_file: Đổi tên file/folder
- execute_file: Chạy file script (Python, Bash, Node.js)
- list_files: Liệt kê files trong thư mục
- search_files: Tìm kiếm files theo pattern

ĐƯỜNG DẪN:
- Sử dụng đường dẫn tuyệt đối hoặc tương đối
- Đường dẫn tương đối sẽ được tính từ thư mục hiện tại
- Ví dụ: "./test.py", "/tmp/test.txt", "folder/file.txt"
- list_files: nếu có thể liệt kê chi tiết ra, gồm bao nhiêu file, có các file gì, đuôi exetention gì, v.v.

VÍ DỤ XỬ LÝ:
User: "tạo file hello.py với nội dung hello world và chạy nó"
→ Step 1: create_file("hello.py", "print('Hello World')")
→ Step 2: execute_file("hello.py")

User: "đổi tên tất cả file .exe thành .run"
→ Step 1: search_files(".", "*.exe", recursive=true)
→ Step 2: Với mỗi file, rename_file(old, new)

User: "xóa tất cả file .exe trong folder này"
→ Step 1: search_files(".", "*.exe", recursive=true)
→ Step 2: Với mỗi file, delete_file(path)

User: "folder này có bao nhiêu file"
→ Step 1: list_files(".", recursive=false)
→ Trả về: số lượng files và folders

QUAN TRỌNG:
- Luôn xác nhận đường dẫn chính xác
- Chấp nhận luôn yêu cầu của user, không cần xác nhận lại trừ khi thao tác nguy hiểm
- Với bulk operations (đổi tên/xóa nhiều file), xử lý tuần tự
- Báo lỗi rõ ràng nếu không thực hiện được
- Hiển thị kết quả chi tiết cho user"""

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
        "name": "execute_file",
        "description": "Thực thi file script (Python, Bash, Node.js). CẦN XÁC NHẬN từ user.",
        "parameters": {
            "type": "object",
            "properties": {
                "file_path": {
                    "type": "string",
                    "description": "Đường dẫn file cần chạy"
                },
                "args": {
                    "type": "string",
                    "description": "Arguments cho script (optional)"
                },
                "working_dir": {
                    "type": "string",
                    "description": "Working directory (optional, mặc định là thư mục hiện tại)"
                }
            },
            "required": ["file_path"]
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
    }
]

# Debug mode
DEBUG = os.environ.get('DEBUG', '').lower() in ('true', '1', 'yes')

def debug_print(*args, **kwargs):
    """Print debug messages to stderr"""
    if DEBUG:
        print("[DEBUG]", *args, file=sys.stderr, **kwargs)

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
    elif action == "execute_file":
        print(f"▶️  Chạy file: {details.get('file_path', 'N/A')}", file=sys.stderr)
        if details.get('args'):
            print(f"   Arguments: {details.get('args')}", file=sys.stderr)
    
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
    
    # Các function cần confirmation
    needs_confirmation = ["create_file", "update_file", "delete_file", "rename_file", "execute_file"]
    
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
        
    elif func_name == "execute_file":
        file_path = args.get("file_path", "")
        exec_args = args.get("args", "")
        working_dir = args.get("working_dir", "")
        result = call_filesystem_script("executefile", file_path, exec_args, working_dir)
        
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
        
        # Initialize conversation
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
