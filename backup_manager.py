#!/usr/bin/env python3
"""
Warp Chat Archiver - Backup Manager
Automated backup system with compression and scheduling
"""

import os
import json
import gzip
import shutil
import tarfile
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Dict, Any, Optional
import logging
from dataclasses import dataclass, asdict
import configparser

from database_manager import WarpDatabaseManager


@dataclass
class BackupConfig:
    """Configuration for backup operations"""
    backup_dir: str
    enable_compression: bool = True
    retention_days: int = 30
    max_backups: int = 10
    backup_format: str = 'sqlite'  # 'sqlite', 'json', 'both'
    include_metadata: bool = True
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'BackupConfig':
        return cls(**data)


@dataclass 
class BackupInfo:
    """Information about a backup"""
    filename: str
    filepath: str
    timestamp: str
    size: int
    compressed: bool
    backup_type: str
    conversation_count: int = 0
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'BackupInfo':
        return cls(**data)


class BackupManager:
    """Manages automated backups of Warp conversations"""
    
    def __init__(self, config: Optional[BackupConfig] = None, db_manager: Optional[WarpDatabaseManager] = None):
        self.logger = logging.getLogger(__name__)
        self.config = config or BackupConfig(backup_dir=str(Path.home() / "warp-chat-backups"))
        self.db_manager = db_manager or WarpDatabaseManager(allow_missing=True)
        
        # Ensure backup directory exists
        Path(self.config.backup_dir).mkdir(parents=True, exist_ok=True)
        
        # Backup history file
        self.history_file = Path(self.config.backup_dir) / ".backup_history.json"
    
    def create_full_backup(self) -> Optional[BackupInfo]:
        """Create a full backup of the Warp database"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        try:
            if self.config.backup_format in ['sqlite', 'both']:
                backup_info = self._create_sqlite_backup(timestamp)
                if backup_info:
                    self._save_backup_history(backup_info)
                    return backup_info
            
            if self.config.backup_format in ['json', 'both']:
                backup_info = self._create_json_backup(timestamp)
                if backup_info:
                    self._save_backup_history(backup_info)
                    return backup_info
            
        except Exception as e:
            self.logger.error(f"Failed to create backup: {e}")
        
        return None
    
    def _create_sqlite_backup(self, timestamp: str) -> Optional[BackupInfo]:
        """Create SQLite database backup"""
        filename = f"warp_backup_{timestamp}.sqlite"
        if self.config.enable_compression:
            filename += ".gz"
        
        filepath = Path(self.config.backup_dir) / filename
        
        try:
            # Create temporary uncompressed backup first
            temp_backup = Path(self.config.backup_dir) / f"temp_{timestamp}.sqlite"
            
            # Backup database
            success = self.db_manager.backup_database(str(temp_backup))
            if not success:
                return None
            
            # Compress if enabled
            if self.config.enable_compression:
                with open(temp_backup, 'rb') as f_in:
                    with gzip.open(filepath, 'wb') as f_out:
                        shutil.copyfileobj(f_in, f_out)
                temp_backup.unlink()  # Remove temp file
            else:
                temp_backup.rename(filepath)
            
            # Get backup info
            stats = self.db_manager.get_database_stats()
            
            backup_info = BackupInfo(
                filename=filename,
                filepath=str(filepath),
                timestamp=timestamp,
                size=filepath.stat().st_size,
                compressed=self.config.enable_compression,
                backup_type='sqlite',
                conversation_count=stats.get('total_conversations', 0)
            )
            
            self.logger.info(f"Created SQLite backup: {filename} ({backup_info.size} bytes)")
            return backup_info
            
        except Exception as e:
            self.logger.error(f"Failed to create SQLite backup: {e}")
            # Cleanup temp file if it exists
            temp_backup = Path(self.config.backup_dir) / f"temp_{timestamp}.sqlite"
            if temp_backup.exists():
                temp_backup.unlink()
            return None
    
    def _create_json_backup(self, timestamp: str) -> Optional[BackupInfo]:
        """Create JSON format backup"""
        filename = f"warp_backup_{timestamp}.json"
        if self.config.enable_compression:
            filename += ".gz"
        
        filepath = Path(self.config.backup_dir) / filename
        
        try:
            # Get all conversations
            conversations = self.db_manager.get_all_conversations()
            
            # Prepare export data
            backup_data = {
                'backup_timestamp': datetime.now().isoformat(),
                'backup_type': 'json',
                'warp_db_path': str(self.db_manager.db_path),
                'total_conversations': len(conversations),
                'conversations': []
            }
            
            if self.config.include_metadata:
                backup_data['database_stats'] = self.db_manager.get_database_stats()
            
            # Add conversation data
            for conv in conversations:
                conv_data = {
                    'id': conv.id,
                    'conversation_id': conv.conversation_id,
                    'active_task_id': conv.active_task_id,
                    'last_modified_at': conv.last_modified_at,
                    'message_count': conv.message_count,
                    'summary': conv.get_summary(),
                    'conversation_data': conv.parsed_data
                }
                backup_data['conversations'].append(conv_data)
            
            # Write backup file
            if self.config.enable_compression:
                with gzip.open(filepath, 'wt', encoding='utf-8') as f:
                    json.dump(backup_data, f, indent=2, ensure_ascii=False)
            else:
                with open(filepath, 'w', encoding='utf-8') as f:
                    json.dump(backup_data, f, indent=2, ensure_ascii=False)
            
            backup_info = BackupInfo(
                filename=filename,
                filepath=str(filepath),
                timestamp=timestamp,
                size=filepath.stat().st_size,
                compressed=self.config.enable_compression,
                backup_type='json',
                conversation_count=len(conversations)
            )
            
            self.logger.info(f"Created JSON backup: {filename} ({backup_info.size} bytes)")
            return backup_info
            
        except Exception as e:
            self.logger.error(f"Failed to create JSON backup: {e}")
            return None
    
    def create_incremental_backup(self, since_timestamp: str) -> Optional[BackupInfo]:
        """Create incremental backup since given timestamp"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"warp_incremental_{timestamp}.json"
        
        if self.config.enable_compression:
            filename += ".gz"
        
        filepath = Path(self.config.backup_dir) / filename
        
        try:
            # Get conversations since timestamp
            conversations = []
            all_conversations = self.db_manager.get_all_conversations()
            
            for conv in all_conversations:
                if conv.last_modified_at > since_timestamp:
                    conversations.append(conv)
            
            if not conversations:
                self.logger.info("No new conversations for incremental backup")
                return None
            
            # Prepare incremental backup data
            backup_data = {
                'backup_timestamp': datetime.now().isoformat(),
                'backup_type': 'incremental',
                'since_timestamp': since_timestamp,
                'total_conversations': len(conversations),
                'conversations': []
            }
            
            # Add conversation data
            for conv in conversations:
                conv_data = {
                    'id': conv.id,
                    'conversation_id': conv.conversation_id,
                    'active_task_id': conv.active_task_id,
                    'last_modified_at': conv.last_modified_at,
                    'message_count': conv.message_count,
                    'summary': conv.get_summary(),
                    'conversation_data': conv.parsed_data
                }
                backup_data['conversations'].append(conv_data)
            
            # Write backup file
            if self.config.enable_compression:
                with gzip.open(filepath, 'wt', encoding='utf-8') as f:
                    json.dump(backup_data, f, indent=2, ensure_ascii=False)
            else:
                with open(filepath, 'w', encoding='utf-8') as f:
                    json.dump(backup_data, f, indent=2, ensure_ascii=False)
            
            backup_info = BackupInfo(
                filename=filename,
                filepath=str(filepath),
                timestamp=timestamp,
                size=filepath.stat().st_size,
                compressed=self.config.enable_compression,
                backup_type='incremental',
                conversation_count=len(conversations)
            )
            
            self.logger.info(f"Created incremental backup: {filename} ({len(conversations)} conversations)")
            self._save_backup_history(backup_info)
            return backup_info
            
        except Exception as e:
            self.logger.error(f"Failed to create incremental backup: {e}")
            return None
    
    def create_compressed_archive(self, backup_files: List[str], archive_name: str) -> bool:
        """Create compressed archive from multiple backup files"""
        archive_path = Path(self.config.backup_dir) / f"{archive_name}.tar.gz"
        
        try:
            with tarfile.open(archive_path, 'w:gz') as tar:
                for backup_file in backup_files:
                    backup_path = Path(backup_file)
                    if backup_path.exists():
                        tar.add(backup_path, arcname=backup_path.name)
            
            self.logger.info(f"Created compressed archive: {archive_path}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to create archive: {e}")
            return False
    
    def cleanup_old_backups(self) -> int:
        """Remove old backups according to retention policy"""
        removed_count = 0
        backup_dir = Path(self.config.backup_dir)
        
        try:
            # Get all backup files
            backup_files = []
            for pattern in ["warp_backup_*.sqlite*", "warp_backup_*.json*", "warp_incremental_*.json*"]:
                backup_files.extend(backup_dir.glob(pattern))
            
            # Sort by modification time (newest first)
            backup_files.sort(key=lambda x: x.stat().st_mtime, reverse=True)
            
            current_time = datetime.now()
            retention_cutoff = current_time - timedelta(days=self.config.retention_days)
            
            # Remove files older than retention period or exceeding max count
            for i, backup_file in enumerate(backup_files):
                file_time = datetime.fromtimestamp(backup_file.stat().st_mtime)
                
                # Keep if within retention period and under max count
                if i < self.config.max_backups and file_time >= retention_cutoff:
                    continue
                
                # Remove old backup
                backup_file.unlink()
                removed_count += 1
                self.logger.info(f"Removed old backup: {backup_file.name}")
            
        except Exception as e:
            self.logger.error(f"Failed to cleanup old backups: {e}")
        
        return removed_count
    
    def get_backup_history(self) -> List[BackupInfo]:
        """Get list of all backup history"""
        if not self.history_file.exists():
            return []
        
        try:
            with open(self.history_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                return [BackupInfo.from_dict(item) for item in data.get('backups', [])]
        except Exception as e:
            self.logger.error(f"Failed to read backup history: {e}")
            return []
    
    def _save_backup_history(self, backup_info: BackupInfo):
        """Save backup information to history"""
        history = self.get_backup_history()
        history.append(backup_info)
        
        # Keep only last 100 entries
        history = history[-100:]
        
        try:
            history_data = {
                'last_updated': datetime.now().isoformat(),
                'backups': [backup.to_dict() for backup in history]
            }
            
            with open(self.history_file, 'w', encoding='utf-8') as f:
                json.dump(history_data, f, indent=2, ensure_ascii=False)
                
        except Exception as e:
            self.logger.error(f"Failed to save backup history: {e}")
    
    def verify_backup(self, backup_path: str) -> bool:
        """Verify backup file integrity"""
        backup_path = Path(backup_path)
        
        if not backup_path.exists():
            return False
        
        try:
            if backup_path.suffix == '.gz':
                if backup_path.stem.endswith('.sqlite'):
                    # Compressed SQLite backup
                    with gzip.open(backup_path, 'rb') as f:
                        # Try to read first few bytes
                        header = f.read(16)
                        return header.startswith(b'SQLite format 3')
                elif backup_path.stem.endswith('.json'):
                    # Compressed JSON backup
                    with gzip.open(backup_path, 'rt', encoding='utf-8') as f:
                        data = json.load(f)
                        return 'backup_timestamp' in data and 'conversations' in data
            else:
                if backup_path.suffix == '.sqlite':
                    # Uncompressed SQLite backup
                    with open(backup_path, 'rb') as f:
                        header = f.read(16)
                        return header.startswith(b'SQLite format 3')
                elif backup_path.suffix == '.json':
                    # Uncompressed JSON backup
                    with open(backup_path, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                        return 'backup_timestamp' in data and 'conversations' in data
                        
        except Exception as e:
            self.logger.error(f"Failed to verify backup {backup_path}: {e}")
        
        return False
    
    def get_backup_stats(self) -> Dict[str, Any]:
        """Get statistics about backups"""
        backup_dir = Path(self.config.backup_dir)
        
        stats = {
            'backup_directory': str(backup_dir),
            'total_backups': 0,
            'total_size': 0,
            'oldest_backup': None,
            'newest_backup': None,
            'backup_types': {}
        }
        
        try:
            backup_files = []
            for pattern in ["warp_backup_*.sqlite*", "warp_backup_*.json*", "warp_incremental_*.json*"]:
                backup_files.extend(backup_dir.glob(pattern))
            
            if not backup_files:
                return stats
            
            # Sort by modification time
            backup_files.sort(key=lambda x: x.stat().st_mtime)
            
            stats['total_backups'] = len(backup_files)
            stats['oldest_backup'] = backup_files[0].name
            stats['newest_backup'] = backup_files[-1].name
            
            # Calculate total size and count by type
            for backup_file in backup_files:
                file_size = backup_file.stat().st_size
                stats['total_size'] += file_size
                
                # Determine backup type
                if 'incremental' in backup_file.name:
                    backup_type = 'incremental'
                elif backup_file.suffix in ['.sqlite', '.gz'] and 'sqlite' in backup_file.name:
                    backup_type = 'sqlite'
                else:
                    backup_type = 'json'
                
                stats['backup_types'][backup_type] = stats['backup_types'].get(backup_type, 0) + 1
                
        except Exception as e:
            self.logger.error(f"Failed to get backup stats: {e}")
        
        return stats


class BackupScheduler:
    """Handles scheduling of automated backups"""
    
    def __init__(self, backup_manager: BackupManager):
        self.backup_manager = backup_manager
        self.logger = logging.getLogger(__name__)
    
    def create_cron_job(self, schedule: str = "0 2 * * *") -> bool:
        """Create a cron job for automated backups (Linux/macOS)"""
        try:
            import subprocess
            
            script_path = Path(__file__).parent / "run_backup.py"
            
            # Create backup runner script
            self._create_backup_runner_script(script_path)
            
            # Add cron job
            cron_command = f"{schedule} /usr/bin/python3 {script_path}"
            
            # Use crontab to add the job
            result = subprocess.run(
                ["crontab", "-l"], 
                capture_output=True, 
                text=True, 
                check=False
            )
            
            current_crontab = result.stdout if result.returncode == 0 else ""
            
            # Check if job already exists
            if str(script_path) in current_crontab:
                self.logger.info("Cron job already exists")
                return True
            
            # Add new job
            new_crontab = current_crontab + f"\n{cron_command}\n"
            
            result = subprocess.run(
                ["crontab", "-"],
                input=new_crontab,
                text=True,
                check=True
            )
            
            self.logger.info(f"Created cron job: {cron_command}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to create cron job: {e}")
            return False
    
    def _create_backup_runner_script(self, script_path: Path):
        """Create a standalone script for running backups"""
        script_content = f'''#!/usr/bin/env python3
"""
Automated Warp Chat Backup Runner
This script is called by cron to perform scheduled backups
"""

import sys
import logging
from pathlib import Path

# Add the archiver directory to Python path
sys.path.append(str(Path(__file__).parent))

from backup_manager import BackupManager, BackupConfig

def main():
    # Configure logging
    log_file = Path.home() / ".warp-chat-archiver.log"
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_file),
            logging.StreamHandler()
        ]
    )
    
    logger = logging.getLogger(__name__)
    
    try:
        # Load configuration
        config = BackupConfig(backup_dir=str(Path.home() / "warp-chat-backups"))
        
        # Create backup manager
        backup_manager = BackupManager(config)
        
        # Create backup
        backup_info = backup_manager.create_full_backup()
        if backup_info:
            logger.info(f"Backup created successfully: {{backup_info.filename}}")
            
            # Cleanup old backups
            removed_count = backup_manager.cleanup_old_backups()
            if removed_count > 0:
                logger.info(f"Cleaned up {{removed_count}} old backups")
        else:
            logger.error("Failed to create backup")
            
    except Exception as e:
        logger.error(f"Backup script failed: {{e}}")
        sys.exit(1)

if __name__ == "__main__":
    main()
'''
        
        with open(script_path, 'w') as f:
            f.write(script_content)
        
        # Make script executable
        script_path.chmod(0o755)


if __name__ == "__main__":
    # Test backup manager
    logging.basicConfig(level=logging.INFO)
    
    # Test configuration
    config = BackupConfig(
        backup_dir="/tmp/warp_backup_test",
        enable_compression=True,
        retention_days=7,
        max_backups=5
    )
    
    backup_manager = BackupManager(config)
    
    # Create test backup
    backup_info = backup_manager.create_full_backup()
    if backup_info:
        print(f"Test backup created: {backup_info.filename}")
        
        # Verify backup
        is_valid = backup_manager.verify_backup(backup_info.filepath)
        print(f"Backup verification: {'PASSED' if is_valid else 'FAILED'}")
        
        # Get stats
        stats = backup_manager.get_backup_stats()
        print(f"Backup stats: {stats}")
    else:
        print("Failed to create test backup")