# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.0.0] - 2025-11-07

### Added
- 🎯 Main chat interface với markdown rendering
- 🔀 Intent classification và routing system
- 📁 Filesystem agent với function calling
- 📅 Google Calendar integration
- 🌤️ Weather agent
- 🎨 Image generation agent
- 🔍 Google search agent
- 🛡️ Confirmation system cho dangerous operations
- 📦 Installation script với symlink support
- 🔄 Auto-update từ GitHub
- 🗑️ Uninstall script
- 📚 Comprehensive documentation
  - README.md - Main docs
  - INSTALL.md - Installation guide
  - QUICKSTART.md - Quick start guide
  - CONTRIBUTING.md - Contribution guidelines
- 🤖 GitHub Actions CI/CD
- 🎨 Beautiful terminal UI với colors và formatting
- 🐚 Support cho bash và zsh
- 💻 Cross-platform: macOS và Linux

### Features Detail

#### Chat Interface
- Natural language processing
- Markdown rendering với syntax highlighting
- Command history
- Special commands (/help, /clear, /exit)
- Session management

#### Intent Classification
- Intelligent routing based on user intent
- Support cho 6 intent types:
  - chat: General conversation
  - filesystem: File operations
  - calendar: Calendar management
  - weather: Weather queries
  - image_create: Image generation
  - google_search: Web search

#### Filesystem Agent
- Create, read, update, delete files/folders
- Search files
- Execute scripts
- Safe operations với confirmation
- Session state management

#### Installation System
- One-command installation
- Symlink vào /usr/local/bin
- Tự động cấp quyền thực thi
- Cross-directory execution support
- Version checking
- Help system

#### Update System
- Auto-fetch từ GitHub
- Stash local changes
- Show commit diff
- Restore local changes after update
- Smart conflict handling

### Documentation
- Complete README với examples
- Detailed installation guide
- Quick start guide (30-second setup)
- Contributing guidelines
- Code standards
- Testing guide

### Infrastructure
- GitHub Actions workflow
- .env.example template
- Project structure documentation
- Error handling và logging

## [Unreleased]

### Planned Features
- [ ] Voice input support
- [ ] Multi-language support (English, etc.)
- [ ] Plugin system
- [ ] Docker agent
- [ ] Database agent
- [ ] Git agent
- [ ] Conversation history persistence
- [ ] User preferences
- [ ] API rate limiting
- [ ] Caching system
- [ ] Better error messages
- [ ] Unit tests
- [ ] Integration tests
- [ ] Performance monitoring
- [ ] Usage analytics (opt-in)

### Known Issues
- Symlink requires manual path resolution on some macOS versions
- Python scripts cần Python 3.6+
- Large file operations có thể timeout với Gemini API
- Rate limiting chưa được implement

## Version History

### Version Numbering
- **MAJOR** version: Breaking changes
- **MINOR** version: New features (backward compatible)
- **PATCH** version: Bug fixes và improvements

### Upgrade Guide

#### To 1.0.0
First release - no upgrade needed.

Future versions sẽ có upgrade instructions ở đây.

## Links

- [GitHub Repository](https://github.com/minhqnd/moibash)
- [Documentation](README.md)
- [Installation Guide](INSTALL.md)
- [Contributing](CONTRIBUTING.md)

---

**Note**: Changelog này được maintain thủ công. Mỗi release sẽ được document đầy đủ.
