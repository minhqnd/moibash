# Migration Guide: v1.0.0 → v1.1.0

## 📋 Overview

Version 1.1.0 simplifies the moibash installation and maintenance with unified scripts and automatic update checking.

## 🎯 Key Changes

### Simplified Script Structure

**Before (v1.0.0):**
```
moibash/
├── install.sh          # Local installation
├── install_remote.sh   # Remote installation
├── system_check.sh     # System requirements check
├── update.sh          # Update script
├── uninstall.sh       # Uninstall script
└── moibash.sh         # Main script
```

**After (v1.1.0):**
```
moibash/
├── install.sh         # Unified install/uninstall (local + remote)
└── moibash.sh         # Main script (with auto-update)
```

## 🔄 Migration Steps

### For Existing Users

If you already have moibash v1.0.0 installed:

```bash
# Simply update to v1.1.0
moibash --update
```

The update will:
- ✅ Pull latest changes
- ✅ Remove old scripts automatically
- ✅ Restart moibash with new version

### For New Installations

```bash
# Remote install (recommended)
curl -fsSL https://raw.githubusercontent.com/minhqnd/moibash/main/install.sh | bash

# OR local install
git clone https://github.com/minhqnd/moibash.git
cd moibash
./install.sh
```

## 📝 What Changed

### 1. Installation (`install.sh`)

**Before:**
```bash
# Two separate scripts
./install.sh              # For local
curl ... install_remote.sh | bash  # For remote
```

**After:**
```bash
# One unified script
./install.sh              # Works for both local and remote
curl ... install.sh | bash
```

**New Features:**
- Auto-detects local vs remote mode
- Built-in Python 3.6+ requirement check
- Built-in pip3 check
- Integrated uninstall: `./install.sh --uninstall`

### 2. System Check

**Before:**
```bash
./system_check.sh  # Separate script
```

**After:**
```bash
# Built into install.sh
./install.sh  # Automatically checks system
```

### 3. Updates (`moibash --update`)

**Before:**
```bash
# Called external update.sh script
moibash --update
```

**After:**
```bash
# Built into moibash.sh
moibash --update
```

**New Features:**
- Auto-check for updates (once per day)
- Shows notification when update available
- Auto-stash local changes
- Auto-restart after update

### 4. Uninstall

**Before:**
```bash
./uninstall.sh
```

**After:**
```bash
./install.sh --uninstall
```

## 🆕 New Features

### Auto-Update Notification

Moibash now checks for updates automatically (once per day):

```
⚠️  New version available! Run moibash --update to update.
```

No more manual checking!

### Python Requirement

v1.1.0 requires **Python 3.6+**:

```bash
# Installation script will check automatically
python3 --version  # Must be 3.6 or higher
```

If Python is not installed or too old, installation will fail with clear instructions.

## ⚠️ Breaking Changes

### None! 

All changes are backward compatible. Existing users just need to update.

## 🐛 Known Issues

None reported yet.

## 💬 Questions?

- Open an issue: [GitHub Issues](https://github.com/minhqnd/moibash/issues)
- Check documentation: [README.md](README.md)

## 📚 Related Documentation

- [CHANGELOG.md](CHANGELOG.md) - Detailed changelog
- [REQUIREMENTS.md](REQUIREMENTS.md) - System requirements
- [INSTALL.md](INSTALL.md) - Installation guide
- [README.md](README.md) - Main documentation

---

**Version**: 1.1.0  
**Last Updated**: November 7, 2025
