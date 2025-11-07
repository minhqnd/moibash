# 🤝 Contributing to Moibash

Cảm ơn bạn đã quan tâm đến việc đóng góp cho Moibash! 🎉

## 📋 Nội dung

- [Code of Conduct](#code-of-conduct)
- [Cách đóng góp](#cách-đóng-góp)
- [Development Setup](#development-setup)
- [Quy trình Pull Request](#quy-trình-pull-request)
- [Coding Standards](#coding-standards)
- [Testing](#testing)
- [Documentation](#documentation)

## Code of Conduct

Dự án này tuân thủ [Contributor Covenant Code of Conduct](https://www.contributor-covenant.org/). Bằng việc tham gia, bạn cam kết tôn trọng code of conduct này.

## Cách đóng góp

Có nhiều cách để đóng góp cho Moibash:

### 🐛 Báo cáo Bug

1. Kiểm tra [Issues](https://github.com/minhqnd/moibash/issues) xem bug đã được báo cáo chưa
2. Nếu chưa, tạo issue mới với:
   - Mô tả rõ ràng về bug
   - Các bước để reproduce
   - Expected behavior vs actual behavior
   - Screenshots nếu có
   - Environment info (OS, shell, version)

### 💡 Đề xuất tính năng

1. Kiểm tra [Issues](https://github.com/minhqnd/moibash/issues) xem đã có đề xuất tương tự chưa
2. Tạo issue với label "enhancement":
   - Mô tả tính năng chi tiết
   - Use cases
   - Mockups nếu có
   - Ý tưởng implementation

### 📝 Cải thiện Documentation

- Fix typos, grammar
- Thêm examples
- Cải thiện clarity
- Dịch sang ngôn ngữ khác

### 🔧 Code Contribution

1. Fork repository
2. Create feature branch
3. Make changes
4. Submit Pull Request

## Development Setup

### Prerequisites

```bash
# Git
git --version

# Bash/Zsh
bash --version  # hoặc zsh --version

# Python 3
python3 --version

# curl
curl --version
```

### Setup Local Development

```bash
# Fork và clone
git clone https://github.com/YOUR_USERNAME/moibash.git
cd moibash

# Add upstream remote
git remote add upstream https://github.com/minhqnd/moibash.git

# Create .env
cp .env.example .env
# Thêm API keys

# Make scripts executable
chmod +x *.sh tools/**/*.sh

# Test
./moibash.sh --version
```

### Branch Strategy

- `main` - Stable releases
- `develop` - Development branch
- `feature/*` - New features
- `bugfix/*` - Bug fixes
- `hotfix/*` - Urgent fixes

## Quy trình Pull Request

### 1. Chuẩn bị

```bash
# Sync với upstream
git checkout develop
git pull upstream develop

# Create feature branch
git checkout -b feature/your-feature-name
```

### 2. Development

```bash
# Make changes
# ... code ...

# Test thoroughly
./test_all.sh  # nếu có

# Commit changes
git add .
git commit -m "feat: add your feature"
```

### 3. Commit Message Convention

Sử dụng [Conventional Commits](https://www.conventionalcommits.org/):

```
<type>(<scope>): <subject>

<body>

<footer>
```

**Types:**
- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation
- `style`: Formatting, missing semi colons, etc
- `refactor`: Code restructuring
- `test`: Adding tests
- `chore`: Maintenance

**Examples:**
```
feat(filesystem): add recursive delete function
fix(router): handle empty user input
docs(readme): update installation guide
refactor(chat): improve markdown parser
```

### 4. Submit PR

```bash
# Push to your fork
git push origin feature/your-feature-name

# Go to GitHub and create Pull Request
# Chọn base branch: develop (không phải main)
```

### PR Template

```markdown
## Description
Brief description of changes

## Type of Change
- [ ] Bug fix
- [ ] New feature
- [ ] Breaking change
- [ ] Documentation update

## How Has This Been Tested?
Describe testing process

## Checklist
- [ ] Code follows style guidelines
- [ ] Self-review completed
- [ ] Comments added for complex code
- [ ] Documentation updated
- [ ] No new warnings
- [ ] Tests added/updated
- [ ] All tests pass
```

## Coding Standards

### Bash Scripts

```bash
#!/bin/bash

# Always use strict mode
set -e  # Exit on error
set -u  # Error on undefined variables
set -o pipefail  # Pipe failures

# Use meaningful variable names
USER_INPUT="$1"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Functions should have comments
# Function: process_data
# Description: Processes user input
# Args: $1 - User input string
# Returns: Processed string
process_data() {
    local input="$1"
    # ... processing ...
    echo "$result"
}

# Use local variables in functions
my_function() {
    local temp_var="value"
    # ...
}

# Check command success
if command -v git &> /dev/null; then
    echo "Git found"
else
    echo "Git not found"
    exit 1
fi

# Quote variables
echo "$VARIABLE"  # Good
echo $VARIABLE    # Bad

# Use [[ ]] for tests
if [[ "$VAR" == "value" ]]; then
    # ...
fi
```

### Python Scripts

```python
#!/usr/bin/env python3
"""
Module docstring describing purpose
"""

import sys
import json

def function_name(param1: str, param2: int) -> dict:
    """
    Function description
    
    Args:
        param1: Description
        param2: Description
        
    Returns:
        Description of return value
    """
    # Implementation
    return result

# Follow PEP 8
# Use type hints
# Add docstrings
```

### File Organization

```
moibash/
├── moibash.sh          # Main entry point
├── router.sh           # Router logic
├── install.sh          # Installation script
├── uninstall.sh        # Uninstallation script
├── update.sh           # Update script
├── .env.example        # Environment template
├── README.md           # Main documentation
├── INSTALL.md          # Installation guide
├── QUICKSTART.md       # Quick start guide
├── CONTRIBUTING.md     # This file
├── docs/               # Additional documentation
│   └── tool_name/      # Tool-specific docs
├── tools/              # Tool implementations
│   └── tool_name/      # Each tool in own directory
│       ├── README.md   # Tool documentation
│       ├── tool.sh     # Main tool script
│       └── function_call.sh  # Gemini integration
└── .github/            # GitHub configurations
    └── workflows/      # CI/CD workflows
```

## Testing

### Manual Testing

```bash
# Test installation
./install.sh

# Test from different directory
cd /tmp
moibash --version
moibash --help

# Test main functionality
moibash
# ... interact ...
/exit

# Test update
moibash --update

# Test uninstall
cd /path/to/moibash
./uninstall.sh
```

### Automated Testing

```bash
# Run all tests
./test_all.sh

# Test specific component
./tools/filesystem/test.sh
```

### Before Submitting

- [ ] Tested on Linux (Ubuntu/Debian)
- [ ] Tested on macOS
- [ ] Tested with bash
- [ ] Tested with zsh
- [ ] No breaking changes to existing features
- [ ] Documentation updated

## Documentation

### Code Comments

```bash
# Good: Explains WHY
# Using temporary file because large data doesn't fit in memory
temp_file=$(mktemp)

# Bad: Explains WHAT (obvious from code)
# Create temporary file
temp_file=$(mktemp)
```

### README Updates

Khi thêm feature mới, cập nhật:
- README.md - Main documentation
- INSTALL.md - Nếu ảnh hưởng đến installation
- Tool-specific README - Documentation cho tool

### Examples

Luôn cung cấp examples:
```bash
# Example usage
./tools/new_tool/tool.sh "input"
```

## Release Process

### Version Numbering

Sử dụng [Semantic Versioning](https://semver.org/):
- MAJOR.MINOR.PATCH (e.g., 1.2.3)
- MAJOR: Breaking changes
- MINOR: New features (backward compatible)
- PATCH: Bug fixes

### Creating Release

1. Update version in `moibash.sh`
2. Update CHANGELOG.md
3. Create git tag
4. Push tag to GitHub
5. Create GitHub Release

```bash
# Update version
VERSION="1.1.0"

# Update CHANGELOG
git add CHANGELOG.md
git commit -m "chore: prepare release $VERSION"

# Create tag
git tag -a "v$VERSION" -m "Release version $VERSION"

# Push
git push origin develop
git push origin "v$VERSION"
```

## Getting Help

### Resources

- 📖 [README.md](README.md) - Main documentation
- 🚀 [QUICKSTART.md](QUICKSTART.md) - Quick start guide
- 🔧 [INSTALL.md](INSTALL.md) - Installation guide
- 💬 [Discussions](https://github.com/minhqnd/moibash/discussions) - Q&A
- 🐛 [Issues](https://github.com/minhqnd/moibash/issues) - Bug reports

### Contact

- GitHub: [@minhqnd](https://github.com/minhqnd)
- Email: (thêm email nếu muốn)

## Recognition

Contributors sẽ được:
- Liệt kê trong README.md
- Credit trong release notes
- Shoutout trên social media

## License

Bằng việc contribute, bạn đồng ý rằng contributions của bạn sẽ được license dưới MIT License giống như project.

---

**Thank you for contributing to Moibash! 🙏**

Happy coding! 🚀
