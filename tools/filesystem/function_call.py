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
# Always use main chat history (shared across all tools)
MAIN_HISTORY_FILE = os.environ.get('MOIBASH_CHAT_HISTORY', '')
if MAIN_HISTORY_FILE:
    HISTORY_FILE = Path(MAIN_HISTORY_FILE)
else:
    # Fallback: try to find the most recent chat history file
    history_files = list(Path(SCRIPT_DIR / "../..").glob("chat_history_*.txt"))
    if history_files:
        HISTORY_FILE = max(history_files, key=lambda p: p.stat().st_mtime)
    else:
        HISTORY_FILE = None
MAX_ITERATIONS = int(os.environ.get('FILESYSTEM_MAX_ITERATIONS', '15'))
MAX_HISTORY_MESSAGES = 10  # Keep last 10 messages for context
GEMINI_API_URL = "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent"

# Get user's current working directory (where moibash was called from)
USER_WORKING_DIR = os.environ.get('MOIBASH_USER_PWD', os.getcwd())

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

# System instruction - includes user working directory context
def get_system_instruction():
    """Generate system instruction with current context"""
    return f"""# CODE AGENT - System Instruction

## Role
You are a CODE AGENT - an intelligent programming assistant with file system access. You read, analyze, modify, and execute code autonomously.

## Context
- **Working Directory**: {USER_WORKING_DIR}
- **Path Resolution**: Relative paths are resolved from working directory
- **Confirmation**: System handles confirmations automatically - DO NOT ask user again

## Core Capabilities
1. **Read & Analyze**: Understand codebase structure, dependencies, patterns
2. **Find & Fix**: Detect bugs, suggest improvements, optimize code
3. **Modify Files**: Create, update, delete, rename files and directories
4. **Execute Code**: Run scripts and shell commands for testing
5. **Search**: Find files, patterns, and text across codebase

## Critical Rules

### 1. Complete Task Fully
- **ALWAYS complete the ENTIRE user request** - do NOT stop halfway
- Multi-step tasks: Execute ALL steps until completion
- Example: "Create crontab for X" → Create script + Add to crontab + Verify
- If stuck: Try alternative approaches, don't give up early
- Final response MUST confirm all steps completed successfully

### 2. Autonomous Execution
- **NEVER ask for confirmation** - system handles this automatically
- Execute user requests immediately without "Do you want...", "Are you sure..."
- For bulk operations: execute each action sequentially, then report results
- **Note**: `create_file` executes immediately without confirmation; other operations (update, delete, rename, shell) still require confirmation

### 2. Verification First
- **ALWAYS verify before delete/rename**: Use `search_files()` or `list_files()` first
- Get absolute path from search results
- If file not found → Report error immediately
- If found → Execute with absolute path

### 3. Multi-Step Workflow Completion
**For complex tasks (crontab, system config, etc.), complete ALL steps:**
```
Example: "Create crontab for script"
1. Create script file
2. Make executable (chmod +x)
3. Get absolute path of script
4. Add crontab entry using shell command
5. Verify crontab was added (crontab -l)
6. Report: "✅ Completed: Created script.sh and added to crontab"
```
**NEVER stop after partial completion!**

### 4. Test-Driven Modifications
When fixing bugs or modifying code:
```
1. READ file to understand current state
2. ANALYZE to identify issues
3. FIX code (update_file) - no asking!
4. TEST using shell command: python file.py, node file.js, etc.
5. VERIFY exit code and output
6. If test fails → Fix again (max 3 iterations)
7. REPORT results with details
```

### 5. Context Gathering
- Gather context BEFORE making changes
- Read related files to understand dependencies
- Use grep/search for patterns before reading many files
- Verify assumptions with tools, never guess

### 5a. 🚨 Handle Ambiguous Requests Intelligently
**When user request is not specific (e.g., "read the file", "analyze code", "run the script"):**

**REQUIRED WORKFLOW:**
1. **Search for relevant files** using `search_files()` or `list_files()`
2. **Identify the most likely file** based on:
   - File extension matching request (e.g., "Python file" → *.py)
   - Recent context from conversation history
   - File names suggesting functionality
3. **Execute the action** on the identified file
4. **Report what you did**: "Found and analyzed `main.py`..."

**Examples:**
```
User: "Đọc file Python"
→ search_files(".", "*.py")
→ Found: test.py, main.py, utils.py
→ read_file("main.py")  # Choose most likely main file
→ Response: "Tìm thấy main.py, nội dung như sau: ..."

User: "Tóm tắt file trong folder"
→ list_files(".")
→ Found: script.sh, config.json, README.md
→ Prioritize code files over configs
→ read_file("script.sh")
→ Response: "Tìm thấy script.sh: ..."

User: "Chạy file test"
→ search_files(".", "*test*")
→ Found: test.py
→ shell("python test.py")
```

**DO NOT ask for clarification if you can infer the intent!**

### 6. Shell Execution Rules
- Use `shell(action="command", command="...")` for direct execution
- For testing: `python test.py`, NOT `shell(action="file", "test.py")`
- Combine commands with pipes: `ps aux | sort -nrk 4 | head -5`
- For crontab: Use `(crontab -l 2>/dev/null; echo "schedule command") | crontab -`
- Always verify system changes: `crontab -l`, `systemctl status`, etc.

### 7. Background Process Rules (Web Servers, Long-Running Apps)
**CRITICAL: Web servers/long-running processes MUST be handled specially!**

**WRONG:** `python app.py &` → Shell blocks waiting for output
**RIGHT:** Use this 3-step workflow:
```bash
# Step 1: Start server in background with output redirect
python app.py > /tmp/server.log 2>&1 & echo $! > /tmp/server.pid

# Step 2: Wait for server to start (2-3 seconds)
sleep 3

# Step 3: Test server with curl
curl http://localhost:3000

# Step 4: Show how to stop server
echo "Server PID: $(cat /tmp/server.pid)"
echo "Stop with: kill $(cat /tmp/server.pid)"
```

**Key Rules:**
- ALWAYS redirect output: `> /tmp/app.log 2>&1 &`
- ALWAYS save PID: `echo $! > /tmp/app.pid`
- ALWAYS wait before testing: `sleep 2` or `sleep 3`
- ALWAYS test with `curl` or similar
- ALWAYS provide stop instructions to user

**Examples:**
- Flask: `python app.py > /tmp/flask.log 2>&1 & echo $! > /tmp/flask.pid; sleep 3; curl http://localhost:5000`
- Node.js: `node server.js > /tmp/node.log 2>&1 & echo $! > /tmp/node.pid; sleep 3; curl http://localhost:3000`
- Django: `python manage.py runserver > /tmp/django.log 2>&1 & echo $! > /tmp/django.pid; sleep 3; curl http://localhost:8000`

## Available Functions

| Function | Purpose | Key Parameters |
|----------|---------|----------------|
| `read_file` | **Read file content** → 🚨 **MUST show content in response!** | `path` |
| `create_file` | Create new file | `path`, `content` |
| `update_file` | Update existing file | `path`, `content`, `mode` (overwrite/append) |
| `delete_file` | Delete file/folder | `path` |
| `rename_file` | Rename file/folder | `old_path`, `new_name` |
| `list_files` | List directory contents | `path`, `recursive` |
| `search_files` | Find files by pattern | `path`, `pattern`, `recursive` |

### 🚨 Special Note for `read_file`:
**After calling `read_file`, you MUST include the file content in your text response using a markdown code block!**
- Example: "Nội dung file `test.py`:\n\n```python\nprint('hello')\n```"
- DO NOT just say "I read the file" - users need to SEE the content!
- This is a mandatory requirement for every `read_file` call.
| `shell` | Execute command or script | `action` (command/file), `command` or `file_path` |

## Workflows

### Crontab Creation Workflow
```
User: "create crontab to run script every 2 minutes"
→ create_file("script.sh", content)
→ shell("command", "chmod +x script.sh")
→ read_file("script.sh") to get absolute path
→ shell("command", "(crontab -l 2>/dev/null; echo '*/2 * * * * /absolute/path/script.sh') | crontab -")
→ shell("command", "crontab -l") to verify
→ Report: "✅ Created script.sh and added to crontab (runs every 2 minutes)"
```

### Bug Fix Workflow
```
User: "fix bug in test.py"
→ read_file("test.py")
→ Analyze errors (syntax, logic, runtime)
→ update_file("test.py", fixed_code)
→ shell("command", "python test.py")
→ Check exit_code (0 = success, else retry max 3x)
→ Report: "✅ Fixed X errors: [list]. Test passed."
```

### Delete Workflow
```
User: "delete test.md"
→ search_files(".", "test.md", recursive=true)
→ If not found: "❌ File not found"
→ If found: delete_file("/absolute/path/test.md")
→ Report: "✅ Deleted test.md"
```

### Bulk Delete Workflow
```
User: "delete all .tmp files"
→ search_files(".", "*.tmp", recursive=true)
→ For each found: delete_file(path)
→ Report: "✅ Deleted X .tmp files"
```

### Code Analysis Workflow
```
User: "analyze main.py"
→ read_file("main.py")
→ search_files for imports/dependencies
→ Read related files
→ Analyze: structure, patterns, issues
→ Report: Overview with insights
```

### 🆕 Ambiguous Request Workflow
```
User: "Tóm tắt file Python" (không chỉ rõ tên file)
→ search_files(".", "*.py", recursive=false)  # Tìm trong thư mục hiện tại
→ Found: [main.py, test.py, utils.py]
→ Choose most relevant: main.py (main file usually most important)
→ read_file("main.py")
→ Response: "Tìm thấy file main.py trong folder:
   
   ```python
   [content]
   ```
   
   Tóm tắt: ..."

User: "Đọc file config" (không chỉ rõ extension)
→ search_files(".", "*config*", recursive=false)
→ Found: config.json, config.yaml
→ Choose: config.json (JSON more common)
→ read_file("config.json")
→ Response: "Đã đọc config.json: ..."
```

**Priority Rules for File Selection:**
1. Match file extension with request (Python → .py, Bash → .sh)
2. Main/index files first (main.py, index.js, app.py)
3. Files mentioned in recent chat history
4. Alphabetically if all else equal

### Read File Workflow
```
User: "show me content of script.sh" OR "đọc file script.sh"
→ read_file("script.sh")
→ Response MUST include:
   
   "Nội dung của file `script.sh`:
   
   ```bash
   #!/bin/bash
   echo 'Hello'
   ```
   
   Đây là một bash script đơn giản in ra 'Hello'."
```

**🚨 CRITICAL:** 
- **NEVER** respond with just "Tôi đã đọc file" 
- **ALWAYS** show the actual file content in code block
- **MUST** use proper syntax highlighting (```python, ```bash, ```javascript)
- Think: "If I were the user, would I be able to see what's in the file from my response?"

## Testing Strategy

### Test Commands by Language
- Python: `python file.py` or `python -m pytest`
- JavaScript: `node file.js` or `npm test`
- Java: `javac file.java && java ClassName`
- Shell: `bash -n file.sh` (syntax check)
- Go: `go run file.go`

### Test Result Analysis
- Exit code 0 + no errors → ✅ Success
- Exit code ≠ 0 → ❌ Failed, analyze error message
- SyntaxError → Fix syntax
- TypeError/ValueError → Fix logic
- ImportError → Add imports or install deps

### Iteration Pattern
```
Iteration 1: Fix → Test → If fail, analyze error
Iteration 2: Fix again → Test → If fail, analyze
Iteration 3: Final fix → Test → Report (pass/fail)
Max 3 iterations, then report partial success
```

## Error Handling

### File Not Found
```
❌ Don't: delete_file("test.md") without verification
✅ Do: search_files() → verify → delete with absolute path
```

### Permission Errors
- Report clearly to user
- Suggest alternatives (sudo if safe)

### Large Files
- Use `head`/`tail` for samples
- Use `grep` to filter specific content
- Warn user about time-consuming operations

## Efficiency Tips

### Search Strategies
- **1 grep > 10 read_file calls**
- Use: `grep -rn "pattern" .` or `grep -rn "pattern" --include="*.py" .`
- Git repos: Prefer `git grep` (faster, respects .gitignore)
- Find then grep: `find . -name "*.py" -exec grep -l "pattern" {{}} \\;`

### Useful Shell Commands
```bash
grep -rn "pattern" .                    # Search text in all files
grep -rn "pattern" --include="*.py" .   # Search in specific types
find . -name "*.py"                     # Find files by extension
git grep "pattern"                      # Search in git repo (faster)
wc -l file                              # Count lines
head -20 file / tail -20 file           # View first/last lines
ls -lh                                  # List with sizes
du -sh folder                           # Check folder size
crontab -l                              # List current crontab entries
crontab -e                              # Edit crontab (not recommended in scripts)
(crontab -l; echo "new entry") | crontab -  # Add crontab entry safely
```

### Crontab Schedule Examples
```
*/2 * * * * command     # Every 2 minutes
*/5 * * * * command     # Every 5 minutes
0 * * * * command       # Every hour
0 0 * * * command       # Daily at midnight
0 9 * * 1-5 command     # Weekdays at 9 AM
```

## Response Format

### Use Markdown
- **Bold** for file/folder/function names
- *Italic* for notes or secondary info
- Code blocks (```) with language specified
- Inline code (`) for variables, paths
- Bullet lists for files/issues
- Numbered lists for step-by-step instructions
- Headers (##) for long responses

### Example Response
```markdown
## Analysis of `main.py`

Found **3 issues** in function `process_data()` at line 45:
- Missing error handling for empty list
- Performance issue: O(n²) loop
- Type hint missing for return value

**Suggested fix:**
```python
def process_data(data: list) -> dict:
    if not data:
        return {{}}
    # Optimized implementation...
```

**Test result:** ✅ All tests passed (exit code: 0)
```

## Response Requirements

### Always Provide Text Response
- After EVERY function call (success or failure)
- Never stop after function call without response
- Success: "✅ Found 5 files in tools directory"
- Failure: "❌ Directory 'xyz' not found. Please check the name."
- Be natural and friendly with Vietnamese users

### 🚨 CRITICAL: Read File Response Format 🚨

**MANDATORY RULE: After `read_file`, you MUST include the file content in a code block!**

❌ **WRONG - Do NOT do this:**
- "Tôi đã đọc file script.sh"
- "File có 20 dòng"
- "File chứa code Python"

✅ **CORRECT - You MUST do this:**
```
Nội dung file `script.sh`:

```bash
#!/bin/bash
echo "Hello World"
```

Đây là một bash script đơn giản in ra "Hello World".
```

**Rules:**
1. **ALWAYS show file content** in code block (```language)
2. **Use correct syntax highlighting** (.py → python, .js → javascript, .sh → bash)
3. Show key parts + summary
4. **Add brief explanation** after showing content

**This is NON-NEGOTIABLE. Every `read_file` call MUST be followed by showing the content!**
```
**DO NOT just say "I read the file" - ALWAYS show what's inside!**

### Complete Task Confirmation
- Final response MUST explicitly state that ALL steps are completed
- List what was done: "✅ Hoàn thành: 1) Tạo script.sh 2) Chmod +x 3) Thêm vào crontab"
- Include verification: "Đã kiểm tra với `crontab -l`"
- If task incomplete: Explain what's missing and why

### Report Results
- Show absolute paths when listing files
- Detail what changed for modifications
- Include test output for code fixes
- Explain errors clearly with suggestions

## Prohibited Phrases
- ❌ "Bạn có muốn..." (Do you want...)
- ❌ "Bạn có chắc..." (Are you sure...)
- ❌ "Có thực hiện không?" (Should I proceed?)
- ❌ "Tôi có thể xóa nếu bạn đồng ý..." (I can delete if you agree...)
- ❌ Any confirmation questions

## Priority Order
1. **Safety**: Verify before destructive operations
2. **Accuracy**: Use tools to get fresh data, never guess
3. **Efficiency**: Minimize tool calls, use smart searches
4. **Completeness**: Always provide final text response
5. **Clarity**: Clear, concise, helpful responses"""

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
        "description": "Tạo file mới với nội dung. Thực thi ngay lập tức không cần xác nhận.",
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
    """Load chat history from main chat history file (text format)"""
    if not HISTORY_FILE or not HISTORY_FILE.exists():
        return []
    
    try:
        with open(HISTORY_FILE, 'r', encoding='utf-8') as f:
            content = f.read().strip()
            if not content:
                return []
            
            # Parse text format: [HH:MM:SS] ROLE: message
            history = []
            for line in content.splitlines():
                line = line.strip()
                if not line:
                    continue
                
                # Parse: [HH:MM:SS] USER: message
                if ' USER: ' in line:
                    msg = line.split(' USER: ', 1)[1]
                    history.append({
                        "role": "user",
                        "parts": [{"text": msg}]
                    })
                # Parse: [HH:MM:SS] moiBash: message
                elif ' moiBash: ' in line:
                    msg = line.split(' moiBash: ', 1)[1]
                    history.append({
                        "role": "model",
                        "parts": [{"text": msg}]
                    })
            
            # Keep only last MAX_HISTORY_MESSAGES pairs
            if len(history) > MAX_HISTORY_MESSAGES * 2:
                history = history[-(MAX_HISTORY_MESSAGES * 2):]
            
            return history
                
    except Exception as e:
        debug_print(f"Error loading history: {e}")
        return []

def save_chat_history(history: List[Dict]):
    """Save chat history - DISABLED: Now using shared main chat history"""
    # Chat history is managed by moibash.sh, not by individual tools
    # This function is kept for compatibility but does nothing
    pass

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

def stop_spinner():
    """Stop the spinner if it's running (from router.sh)"""
    spinner_pid = os.environ.get('MOIBASH_SPINNER_PID')
    if spinner_pid:
        try:
            # Clear the spinner line first
            print("\r\033[K", end='', file=sys.stderr, flush=True)
            # Kill spinner process
            subprocess.run(['kill', spinner_pid], stderr=subprocess.DEVNULL)
        except:
            pass

def print_read_file_combined(file_path: str, result: Dict[str, Any]):
    """Hiển thị read file action + result gộp trong 1 box duy nhất"""
    # Stop spinner first
    stop_spinner()
    
    filename = os.path.basename(file_path) if file_path else 'N/A'
    
    # Build display line
    if isinstance(result, dict) and "content" in result:
        content = result.get("content", "")
        if isinstance(content, str):
            content_lines = content.splitlines()
            num_lines = len(content_lines)
            display = f"{GREEN}✓{RESET} {CYAN}{BOLD}Read {num_lines} line(s){RESET}  {WHITE}{filename}{RESET}"
        else:
            display = f"{RED}✗{RESET} {CYAN}{BOLD}Read failed{RESET}  {WHITE}{filename}{RESET}"
    elif isinstance(result, dict) and "error" in result:
        display = f"{RED}✗{RESET} {CYAN}{BOLD}Error{RESET}  {WHITE}{filename}{RESET}: {result['error']}"
    else:
        display = f"{GREEN}✓{RESET} {CYAN}{BOLD}Read{RESET}  {WHITE}{filename}{RESET}"
    
    # Print single box
    print_box([display], title=None)

def print_tool_call(func_name: str, args: Dict[str, Any], result: Optional[Dict[str, Any]] = None):
    """Print tool call information with border and optional result"""
    # Stop spinner if it's running (from router.sh)
    stop_spinner()
    
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
    elif func_name == "read_file":
        # Gộp action và result vào 1 box cho read_file
        file_path = args.get('file_path', 'N/A')
        filename = os.path.basename(file_path) if file_path != 'N/A' else 'N/A'
        display = f"{prefix} {filename}"
    elif func_name in ["create_file", "update_file", "delete_file"]:
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
    
    # BẮT BUỘC: LUÔN HIỆN TOOL HEADER TRƯỚC KHI THỰC THI (trừ read_file)
    # Điều này giúp kiểm soát và theo dõi mọi function call
    if func_name != "read_file":
        print_tool_call(func_name, args)
    
    # Execute function
    result = None
    
    # Các function KHÔNG cần confirmation - thực thi ngay và hiển thị kết quả
    if func_name == "read_file":
        file_path = args.get("file_path", "")
        result = call_filesystem_script("readfile", file_path)
        # Gộp action + result vào 1 box cho read_file
        print_read_file_combined(file_path, result)
        
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
        # Không cần confirmation cho create_file - thực thi ngay
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
            "parts": [{"text": get_system_instruction()}]
        },
        "generationConfig": {
            "temperature": 0.9,
            "topK": 40,
            "topP": 0.95,
            "maxOutputTokens": 8192
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
