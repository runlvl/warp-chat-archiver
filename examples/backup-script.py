#!/usr/bin/env python3
"""
Standalone backup script for Warp Chat Archiver
Can be used in cron jobs or automated systems
"""

import sys
import os
import argparse
from pathlib import Path

# Add the parent directory to the path to import our modules
sys.path.insert(0, str(Path(__file__).parent.parent))

from backup_manager import BackupManager
from database_manager import DatabaseManager


def main():
    parser = argparse.ArgumentParser(
        description="Standalone backup script for Warp conversations"
    )
    parser.add_argument(
        "--backup-dir",
        default="~/warp-chat-backups",
        help="Backup directory (default: ~/warp-chat-backups)"
    )
    parser.add_argument(
        "--compress",
        action="store_true",
        help="Compress backup files"
    )
    parser.add_argument(
        "--incremental",
        action="store_true",
        help="Create incremental backup (only new conversations)"
    )
    parser.add_argument(
        "--retain-days",
        type=int,
        default=30,
        help="Number of days to retain backups (default: 30)"
    )
    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Verbose output"
    )
    
    args = parser.parse_args()
    
    # Initialize managers
    try:
        db_manager = DatabaseManager()
        backup_manager = BackupManager(
            backup_directory=os.path.expanduser(args.backup_dir)
        )
        
        if args.verbose:
            print(f"📊 Found {len(db_manager.get_conversations())} conversations")
            print(f"💾 Backup directory: {args.backup_dir}")
        
        # Create backup
        backup_type = "incremental" if args.incremental else "full"
        backup_file = backup_manager.create_backup(
            backup_type=backup_type,
            compress=args.compress
        )
        
        if backup_file:
            print(f"✅ Backup created: {backup_file}")
            
            # Clean old backups
            if args.retain_days > 0:
                cleaned = backup_manager.cleanup_old_backups(args.retain_days)
                if cleaned and args.verbose:
                    print(f"🧹 Cleaned {len(cleaned)} old backups")
        else:
            print("❌ Backup failed")
            sys.exit(1)
            
    except Exception as e:
        print(f"❌ Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()