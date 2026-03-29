#!/usr/bin/env python3
"""
function_call.py - Google Calendar Function Calling với Gemini
Flow: User message → Gemini Function Calling → Extract actions → Call calendar API
"""

import os
import sys
import json
import subprocess
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
import requests

# Constants
SCRIPT_DIR = Path(__file__).parent
ENV_FILE = SCRIPT_DIR / "../../.env"
MAX_ITERATIONS = 10
GEMINI_API_URL = "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash-lite:generateContent"

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
SYSTEM_INSTRUCTION = """Bạn là trợ lý quản lý lịch thông minh.

KHI XỬ LÝ YÊU CẦU:
1. LUÔN KIỂM TRA LỊCH HIỆN TẠI TRƯỚC khi thêm/xóa/sửa
2. Với yêu cầu XÓA: list_events trước, tìm event phù hợp, sau đó delete_event
3. Với yêu cầu THÊM: list_events trước để kiểm tra conflict, sau đó add_event
4. Với yêu cầu SỬA: list_events để tìm event, sau đó update_event
5. Parse thời gian tự nhiên sang ISO 8601 format (timezone +07:00)
6. Nếu không có giờ cụ thể, mặc định dùng giờ hợp lý

THỜI GIAN:
- 'hôm nay', 'today' → ngày hiện tại
- 'ngày mai', 'tomorrow' → ngày tiếp theo
- 'tuần này', 'this week' → 7 ngày tới
- 'sáng' → 08:00-12:00
- 'chiều' → 13:00-17:00
- 'tối' → 18:00-22:00

VÍ DỤ XỬ LÝ:
User: 'lịch trình hôm nay'
→ Call: list_events với timeMin=hôm nay 00:00, timeMax=hôm nay 23:59

User: 'thêm lịch đi ăn tối lúc 7h'
→ Step 1: list_events kiểm tra 19:00-20:00
→ Step 2: add_event('Đi ăn tối', '19:00', '20:00')

User: 'xóa lịch họp sáng nay'
→ Step 1: list_events sáng nay (08:00-12:00)
→ Step 2: Tìm event có 'họp' trong title
→ Step 3: delete_event(event_id)

QUAN TRỌNG - KHI TRẢ LỜI USER:
- LUÔN HIỂN THỊ thông tin chi tiết của từng event
- Với mỗi event, hiển thị: Tiêu đề, Thời gian, Địa điểm (nếu có), Mô tả (nếu có)
- Định dạng dễ đọc với emoji
- KHÔNG được chỉ nói 'có X lịch' mà phải liệt kê CHI TIẾT tất cả

HÃY GỌI FUNCTION THEO THỨ TỰ HỢP LÝ VÀ LUÔN HIỂN THỊ CHI TIẾT ĐẦY ĐỦ!"""

# Function declarations
FUNCTION_DECLARATIONS = [
    {
        "name": "list_events",
        "description": "Lấy danh sách events từ Google Calendar trong khoảng thời gian. LUÔN GỌI FUNCTION NÀY TRƯỚC KHI ADD/UPDATE/DELETE để kiểm tra lịch hiện tại.",
        "parameters": {
            "type": "object",
            "properties": {
                "time_min": {
                    "type": "string",
                    "description": "Thời gian bắt đầu (ISO 8601 format, ví dụ: 2024-01-15T00:00:00+07:00)"
                },
                "time_max": {
                    "type": "string",
                    "description": "Thời gian kết thúc (ISO 8601 format, ví dụ: 2024-01-15T23:59:59+07:00)"
                },
                "max_results": {
                    "type": "integer",
                    "description": "Số lượng event tối đa (mặc định 10)"
                }
            },
            "required": ["time_min"]
        }
    },
    {
        "name": "add_event",
        "description": "Thêm event mới vào Google Calendar. GỌI list_events TRƯỚC để kiểm tra conflict.",
        "parameters": {
            "type": "object",
            "properties": {
                "summary": {
                    "type": "string",
                    "description": "Tiêu đề event"
                },
                "start_time": {
                    "type": "string",
                    "description": "Thời gian bắt đầu (ISO 8601 format)"
                },
                "end_time": {
                    "type": "string",
                    "description": "Thời gian kết thúc (ISO 8601 format, optional)"
                },
                "description": {
                    "type": "string",
                    "description": "Mô tả chi tiết (optional)"
                },
                "location": {
                    "type": "string",
                    "description": "Địa điểm (optional)"
                }
            },
            "required": ["summary", "start_time"]
        }
    },
    {
        "name": "update_event",
        "description": "Cập nhật thông tin event có sẵn. GỌI list_events TRƯỚC để lấy event_id.",
        "parameters": {
            "type": "object",
            "properties": {
                "event_id": {
                    "type": "string",
                    "description": "ID của event cần update (lấy từ list_events)"
                },
                "summary": {
                    "type": "string",
                    "description": "Tiêu đề mới (optional)"
                },
                "start_time": {
                    "type": "string",
                    "description": "Thời gian bắt đầu mới (ISO 8601, optional)"
                },
                "end_time": {
                    "type": "string",
                    "description": "Thời gian kết thúc mới (ISO 8601, optional)"
                },
                "description": {
                    "type": "string",
                    "description": "Mô tả mới (optional)"
                },
                "location": {
                    "type": "string",
                    "description": "Địa điểm mới (optional)"
                }
            },
            "required": ["event_id"]
        }
    },
    {
        "name": "delete_event",
        "description": "Xóa event khỏi Google Calendar. GỌI list_events TRƯỚC để lấy event_id cần xóa.",
        "parameters": {
            "type": "object",
            "properties": {
                "event_id": {
                    "type": "string",
                    "description": "ID của event cần xóa (lấy từ list_events)"
                }
            },
            "required": ["event_id"]
        }
    },
    {
        "name": "get_current_time",
        "description": "Lấy thời gian hiện tại để tính toán timeMin/timeMax. Sử dụng khi cần xác định hôm nay, ngày mai, etc.",
        "parameters": {
            "type": "object",
            "properties": {
                "format": {
                    "type": "string",
                    "description": "Format mong muốn: iso8601, date, datetime"
                }
            }
        }
    }
]

# Debug mode
DEBUG = os.environ.get('DEBUG', '').lower() in ('true', '1', 'yes')

def debug_print(*args, **kwargs):
    """Print debug messages to stderr"""
    if DEBUG:
        print("[DEBUG]", *args, file=sys.stderr, **kwargs)

def get_current_time_impl(format_type: str = "iso8601") -> Dict[str, Any]:
    """Get current time in specified format"""
    now = datetime.now()
    
    if format_type == "iso8601":
        time_str = now.strftime('%Y-%m-%dT%H:%M:%S+07:00')
    elif format_type == "date":
        time_str = now.strftime('%Y-%m-%d')
    else:
        time_str = now.strftime('%Y-%m-%d %H:%M:%S')
    
    return {
        "time": time_str,
        "timestamp": int(now.timestamp())
    }

def call_calendar_script(command: str, *args) -> Dict[str, Any]:
    """Call calendar.sh script and parse JSON response"""
    calendar_sh = SCRIPT_DIR / "calendar.sh"
    
    if not calendar_sh.exists():
        return {"error": "calendar.sh not found"}
    
    try:
        # Filter out empty strings from args
        cmd_args = [str(calendar_sh), command] + [str(arg) for arg in args if arg]
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
    """Handle function call and return result"""
    debug_print(f"Function: {func_name}")
    debug_print(f"Args: {json.dumps(args, ensure_ascii=False)}")
    
    if func_name == "list_events":
        time_min = args.get("time_min", "")
        time_max = args.get("time_max", "")
        max_results = args.get("max_results", 10)
        result = call_calendar_script("list", time_min, time_max, max_results)
        
    elif func_name == "add_event":
        summary = args.get("summary", "")
        start_time = args.get("start_time", "")
        end_time = args.get("end_time", "")
        description = args.get("description", "")
        location = args.get("location", "")
        result = call_calendar_script("add", summary, start_time, end_time, description, location)
        
    elif func_name == "update_event":
        event_id = args.get("event_id", "")
        summary = args.get("summary", "")
        start_time = args.get("start_time", "")
        end_time = args.get("end_time", "")
        description = args.get("description", "")
        location = args.get("location", "")
        result = call_calendar_script("update", event_id, summary, start_time, end_time, description, location)
        
    elif func_name == "delete_event":
        event_id = args.get("event_id", "")
        result = call_calendar_script("delete", event_id)
        
    elif func_name == "get_current_time":
        format_type = args.get("format", "iso8601")
        result = get_current_time_impl(format_type)
        
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
    # Get user message
    if len(sys.argv) < 2:
        print("❌ Lỗi: Vui lòng cung cấp câu hỏi về lịch!", file=sys.stderr)
        sys.exit(1)
    
    user_message = sys.argv[1]
    debug_print(f"User message: {user_message}")
    
    # Check API key
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        print("❌ Lỗi: Chưa thiết lập GEMINI_API_KEY!", file=sys.stderr)
        sys.exit(1)
    
    # Check authentication
    auth_sh = SCRIPT_DIR / "auth.sh"
    if auth_sh.exists():
        result = subprocess.run(
            [str(auth_sh), "status"],
            capture_output=True,
            check=False
        )
        if result.returncode != 0:
            print("❌ Chưa đăng nhập Google Calendar", file=sys.stderr)
            print("💡 Vui lòng chạy: ./tools/calendar/auth.sh login", file=sys.stderr)
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
            
            # Execute function
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

if __name__ == "__main__":
    main()
