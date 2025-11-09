#!/usr/bin/env python3
"""
backup_manager.py - Manages file backups for rollback functionality
Stores backups in /tmp/moibash_backup_<PID>/ for each session
"""

import os
import sys
import json
import shutil
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional, Any

class BackupManager:
    """Manages file backups for rollback functionality"""
    
    def __init__(self, session_pid: str = None):
        """Initialize backup manager for a session"""
        if session_pid is None:
            session_pid = os.environ.get('MOIBASH_PID', str(os.getpid()))
        
        self.session_pid = session_pid
        self.backup_dir = Path(f"/tmp/moibash_backup_{session_pid}")
        self.manifest_file = self.backup_dir / "manifest.json"
        
        # Create backup directory if it doesn't exist
        self.backup_dir.mkdir(parents=True, exist_ok=True)
        
        # Load or initialize manifest
        self.manifest = self._load_manifest()
    
    def _load_manifest(self) -> Dict:
        """Load manifest from disk or create new one"""
        if self.manifest_file.exists():
            try:
                with open(self.manifest_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception as e:
                print(f"Warning: Could not load manifest: {e}", file=sys.stderr)
                return {"operations": [], "session_pid": self.session_pid}
        else:
            return {"operations": [], "session_pid": self.session_pid}
    
    def _save_manifest(self):
        """Save manifest to disk"""
        try:
            with open(self.manifest_file, 'w', encoding='utf-8') as f:
                json.dump(self.manifest, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"Warning: Could not save manifest: {e}", file=sys.stderr)
    
    def backup_file(self, file_path: str, operation: str, **metadata) -> Optional[str]:
        """
        Create a backup of a file before modification
        
        Args:
            file_path: Path to the file to backup
            operation: Type of operation (update, delete, rename)
            **metadata: Additional metadata to store
            
        Returns:
            Path to backup file or None if backup failed
        """
        try:
            file_path = Path(file_path).resolve()
            
            # Only backup if file exists
            if not file_path.exists():
                return None
            
            # Generate unique backup filename with timestamp
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
            backup_name = f"{timestamp}_{file_path.name}"
            backup_path = self.backup_dir / backup_name
            
            # Copy file to backup location
            if file_path.is_file():
                shutil.copy2(file_path, backup_path)
            elif file_path.is_dir():
                shutil.copytree(file_path, backup_path)
            else:
                return None
            
            # Record operation in manifest
            operation_record = {
                "timestamp": timestamp,
                "operation": operation,
                "original_path": str(file_path),
                "backup_path": str(backup_path),
                "is_directory": file_path.is_dir(),
                **metadata
            }
            
            self.manifest["operations"].append(operation_record)
            self._save_manifest()
            
            return str(backup_path)
            
        except Exception as e:
            print(f"Warning: Could not backup file {file_path}: {e}", file=sys.stderr)
            return None
    
    def get_operations(self) -> List[Dict]:
        """Get list of all operations in this session"""
        return self.manifest.get("operations", [])
    
    def get_operation_count(self) -> int:
        """Get count of operations in this session"""
        return len(self.manifest.get("operations", []))
    
    def rollback_all(self) -> Dict[str, Any]:
        """
        Rollback all operations in reverse order
        
        Returns:
            Dict with success status and details
        """
        operations = self.manifest.get("operations", [])
        if not operations:
            return {
                "success": False,
                "message": "Không có thao tác nào để rollback",
                "restored": 0,
                "failed": 0
            }
        
        restored = 0
        failed = 0
        errors = []
        
        # Process operations in reverse order (newest first)
        for op in reversed(operations):
            try:
                original_path = Path(op["original_path"])
                backup_path = Path(op["backup_path"])
                operation = op["operation"]
                
                if not backup_path.exists():
                    failed += 1
                    errors.append(f"Backup không tồn tại: {backup_path}")
                    continue
                
                # Restore based on operation type
                if operation == "update":
                    # Restore old content
                    if original_path.exists():
                        original_path.unlink()
                    original_path.parent.mkdir(parents=True, exist_ok=True)
                    shutil.copy2(backup_path, original_path)
                    restored += 1
                    
                elif operation == "delete":
                    # Restore deleted file
                    if op.get("is_directory", False):
                        original_path.parent.mkdir(parents=True, exist_ok=True)
                        shutil.copytree(backup_path, original_path)
                    else:
                        shutil.copy2(backup_path, original_path)
                    restored += 1
                    
                elif operation == "rename":
                    # Restore original name
                    new_path = Path(op.get("new_path", ""))
                    if new_path.exists():
                        new_path.unlink() if new_path.is_file() else shutil.rmtree(new_path)
                    if op.get("is_directory", False):
                        shutil.copytree(backup_path, original_path)
                    else:
                        shutil.copy2(backup_path, original_path)
                    restored += 1
                
            except Exception as e:
                failed += 1
                errors.append(f"Lỗi khôi phục {op['original_path']}: {str(e)}")
        
        # Clear manifest after rollback
        self.manifest["operations"] = []
        self._save_manifest()
        
        return {
            "success": restored > 0,
            "message": f"Đã khôi phục {restored} file, {failed} lỗi",
            "restored": restored,
            "failed": failed,
            "errors": errors
        }
    
    def clear_backups(self):
        """Clear all backups and manifest"""
        try:
            if self.backup_dir.exists():
                shutil.rmtree(self.backup_dir)
            self.backup_dir.mkdir(parents=True, exist_ok=True)
            self.manifest = {"operations": [], "session_pid": self.session_pid}
        except Exception as e:
            print(f"Warning: Could not clear backups: {e}", file=sys.stderr)


def get_backup_manager() -> BackupManager:
    """Get or create backup manager for current session"""
    return BackupManager()


if __name__ == "__main__":
    # CLI interface for backup manager
    if len(sys.argv) < 2:
        print("Usage: backup_manager.py <command> [args...]")
        print("Commands:")
        print("  list              - List all operations")
        print("  rollback          - Rollback all operations")
        print("  clear             - Clear all backups")
        sys.exit(1)
    
    command = sys.argv[1]
    manager = get_backup_manager()
    
    if command == "list":
        ops = manager.get_operations()
        if not ops:
            print("Không có thao tác nào được backup")
        else:
            print(f"Tổng số thao tác: {len(ops)}")
            for i, op in enumerate(ops, 1):
                print(f"\n{i}. {op['operation'].upper()} - {op['timestamp']}")
                print(f"   File: {op['original_path']}")
                if op.get('new_path'):
                    print(f"   → {op['new_path']}")
    
    elif command == "rollback":
        result = manager.rollback_all()
        print(json.dumps(result, ensure_ascii=False, indent=2))
    
    elif command == "clear":
        manager.clear_backups()
        print("Đã xóa tất cả backup")
    
    else:
        print(f"Unknown command: {command}")
        sys.exit(1)
