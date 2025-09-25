#!/usr/bin/env python3
"""
Warp Chat Archiver - Import Manager
Handles importing conversations from various formats and sources
"""

import json
import gzip
import sqlite3
import csv
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass, field
import logging
from datetime import datetime
from security_utils import validate_import_path, SecurityError
from database_manager import WarpDatabaseManager

from database_manager import WarpDatabaseManager, ChatConversation


@dataclass
class ImportResult:
    """Result of an import operation"""
    success: bool
    imported_count: int = 0
    skipped_count: int = 0
    error_count: int = 0
    errors: List[str] = field(default_factory=list)
    
    def add_error(self, error: str):
        self.errors.append(error)
        self.error_count += 1


class ImportManager:
    """Manages importing conversations from various sources"""
    
    def __init__(self, db_manager: Optional[WarpDatabaseManager] = None):
        self.db_manager = db_manager or WarpDatabaseManager()
        self.logger = logging.getLogger(__name__)
    
    def import_from_json(self, file_path: str, overwrite_existing: bool = False) -> ImportResult:
        """Import conversations from JSON export file"""
        result = ImportResult(success=False)
        
        try:
            # Validate import file path for security
            try:
                validated_path = validate_import_path(file_path)
                file_path = str(validated_path)  # Use validated path
            except SecurityError as e:
                result.add_error(f"Import path validation failed: {e}")
                self.logger.error(f"Import path validation failed: {e}")
                return result
            file_path = Path(file_path)
            
            # Handle compressed files
            if file_path.suffix == '.gz':
                with gzip.open(file_path, 'rt', encoding='utf-8') as f:
                    data = json.load(f)
            else:
                with open(file_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
            
            # Validate JSON structure
            if not isinstance(data, dict) or 'conversations' not in data:
                result.add_error("Invalid JSON structure: missing 'conversations' key")
                return result
            
            conversations = data['conversations']
            if not isinstance(conversations, list):
                result.add_error("Invalid JSON structure: 'conversations' must be a list")
                return result
            
            self.logger.info(f"Found {len(conversations)} conversations in JSON file")
            
            # Import each conversation
            for conv_data in conversations:
                try:
                    success = self._import_conversation_data(conv_data, overwrite_existing)
                    if success:
                        result.imported_count += 1
                    else:
                        result.skipped_count += 1
                except Exception as e:
                    result.add_error(f"Failed to import conversation {conv_data.get('conversation_id', 'unknown')}: {e}")
            
            result.success = True
            self.logger.info(f"Import completed: {result.imported_count} imported, {result.skipped_count} skipped, {result.error_count} errors")
            
        except Exception as e:
            result.add_error(f"Failed to process JSON file: {e}")
            self.logger.error(f"JSON import failed: {e}")
        
        return result
    
    def import_from_backup(self, backup_path: str, overwrite_existing: bool = False) -> ImportResult:
        """Import conversations from backup file (SQLite or JSON)"""
        result = ImportResult(success=False)
        backup_path = Path(backup_path)
        
        try:
            # Determine backup type
            if backup_path.suffix == '.gz':
                # Compressed file - check the stem
                if backup_path.stem.endswith('.sqlite'):
                    return self._import_from_sqlite_backup(str(backup_path), overwrite_existing)
                elif backup_path.stem.endswith('.json'):
                    return self.import_from_json(str(backup_path), overwrite_existing)
            else:
                if backup_path.suffix == '.sqlite':
                    return self._import_from_sqlite_backup(str(backup_path), overwrite_existing)
                elif backup_path.suffix == '.json':
                    return self.import_from_json(str(backup_path), overwrite_existing)
            
            result.add_error(f"Unsupported backup file format: {backup_path}")
            
        except Exception as e:
            result.add_error(f"Failed to import backup: {e}")
            self.logger.error(f"Backup import failed: {e}")
        
        return result
    
    def _import_from_sqlite_backup(self, backup_path: str, overwrite_existing: bool) -> ImportResult:
        """Import from SQLite backup file"""
        result = ImportResult(success=False)
        backup_path = Path(backup_path)
        
        try:
            # Handle compressed SQLite backup
            if backup_path.suffix == '.gz':
                # Extract to temporary file
                temp_path = backup_path.parent / f"temp_import_{datetime.now().strftime('%Y%m%d_%H%M%S')}.sqlite"
                
                with gzip.open(backup_path, 'rb') as f_in:
                    with open(temp_path, 'wb') as f_out:
                        f_out.write(f_in.read())
                
                try:
                    result = self._import_from_sqlite_file(str(temp_path), overwrite_existing)
                finally:
                    # Clean up temp file
                    if temp_path.exists():
                        temp_path.unlink()
            else:
                result = self._import_from_sqlite_file(str(backup_path), overwrite_existing)
            
        except Exception as e:
            result.add_error(f"Failed to process SQLite backup: {e}")
            self.logger.error(f"SQLite backup import failed: {e}")
        
        return result
    
    def _import_from_sqlite_file(self, sqlite_path: str, overwrite_existing: bool) -> ImportResult:
        """Import conversations from SQLite database file"""
        result = ImportResult(success=False)
        
        try:
            # Connect to source database
            source_conn = sqlite3.connect(sqlite_path)
            source_conn.row_factory = sqlite3.Row
            
            # Get conversations from source
            cursor = source_conn.execute("""
                SELECT id, conversation_id, active_task_id, conversation_data, last_modified_at
                FROM agent_conversations
                ORDER BY last_modified_at DESC
            """)
            
            conversations = cursor.fetchall()
            source_conn.close()
            
            self.logger.info(f"Found {len(conversations)} conversations in SQLite backup")
            
            # Import each conversation
            for row in conversations:
                try:
                    conv_data = {
                        'id': row['id'],
                        'conversation_id': row['conversation_id'],
                        'active_task_id': row['active_task_id'],
                        'last_modified_at': row['last_modified_at'],
                        'conversation_data': json.loads(row['conversation_data']) if row['conversation_data'] else {}
                    }
                    
                    success = self._import_conversation_data(conv_data, overwrite_existing)
                    if success:
                        result.imported_count += 1
                    else:
                        result.skipped_count += 1
                        
                except Exception as e:
                    result.add_error(f"Failed to import conversation {row['conversation_id']}: {e}")
            
            result.success = True
            self.logger.info(f"SQLite import completed: {result.imported_count} imported, {result.skipped_count} skipped")
            
        except Exception as e:
            result.add_error(f"Failed to read SQLite file: {e}")
            self.logger.error(f"SQLite file import failed: {e}")
        
        return result
    
    def _import_conversation_data(self, conv_data: Dict[str, Any], overwrite_existing: bool) -> bool:
        """Import a single conversation into the database"""
        try:
            conversation_id = conv_data.get('conversation_id')
            if not conversation_id:
                raise ValueError("Missing conversation_id")
            
            # Check if conversation already exists
            existing_conv = self.db_manager.get_conversation_by_id(conversation_id)
            
            if existing_conv and not overwrite_existing:
                self.logger.debug(f"Skipping existing conversation: {conversation_id}")
                return False
            
            # Prepare conversation data
            active_task_id = conv_data.get('active_task_id')
            last_modified_at = conv_data.get('last_modified_at', datetime.now().isoformat())
            
            # Handle conversation_data - could be already parsed or raw JSON string
            conversation_data = conv_data.get('conversation_data', {})
            if isinstance(conversation_data, str):
                conversation_data_str = conversation_data
            else:
                conversation_data_str = json.dumps(conversation_data, ensure_ascii=False)
            
            # Insert or update in database
            with self.db_manager.get_connection() as conn:
                if existing_conv and overwrite_existing:
                    # Update existing
                    conn.execute("""
                        UPDATE agent_conversations 
                        SET active_task_id = ?, conversation_data = ?, last_modified_at = ?
                        WHERE conversation_id = ?
                    """, (active_task_id, conversation_data_str, last_modified_at, conversation_id))
                    self.logger.debug(f"Updated conversation: {conversation_id}")
                else:
                    # Insert new
                    conn.execute("""
                        INSERT OR IGNORE INTO agent_conversations 
                        (conversation_id, active_task_id, conversation_data, last_modified_at)
                        VALUES (?, ?, ?, ?)
                    """, (conversation_id, active_task_id, conversation_data_str, last_modified_at))
                    self.logger.debug(f"Inserted conversation: {conversation_id}")
                
                conn.commit()
            
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to import conversation data: {e}")
            raise
    
    def import_from_csv(self, file_path: str, overwrite_existing: bool = False) -> ImportResult:
        """Import conversations from CSV export file"""
        result = ImportResult(success=False)
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                
                for row in reader:
                    try:
                        # Extract data from CSV row
                        conv_data = {
                            'conversation_id': row.get('Conversation ID'),
                            'active_task_id': row.get('Active Task ID') if row.get('Active Task ID') else None,
                            'last_modified_at': row.get('Last Modified'),
                            'conversation_data': row.get('Raw Data', '{}')
                        }
                        
                        # Parse raw data if it's JSON string
                        try:
                            conv_data['conversation_data'] = json.loads(conv_data['conversation_data'])
                        except (json.JSONDecodeError, TypeError) as e:
                            # Keep as string if not valid JSON
                            self.logger.debug(f"CSV data not valid JSON, keeping as string: {e}")
                        
                        success = self._import_conversation_data(conv_data, overwrite_existing)
                        if success:
                            result.imported_count += 1
                        else:
                            result.skipped_count += 1
                            
                    except Exception as e:
                        result.add_error(f"Failed to import CSV row: {e}")
            
            result.success = True
            self.logger.info(f"CSV import completed: {result.imported_count} imported, {result.skipped_count} skipped")
            
        except Exception as e:
            result.add_error(f"Failed to process CSV file: {e}")
            self.logger.error(f"CSV import failed: {e}")
        
        return result
    
    def merge_databases(self, source_db_path: str, overwrite_existing: bool = False) -> ImportResult:
        """Merge conversations from another Warp database"""
        result = ImportResult(success=False)
        
        try:
            # Create temporary database manager for source
            source_manager = WarpDatabaseManager(source_db_path)
            source_conversations = source_manager.get_all_conversations()
            
            self.logger.info(f"Found {len(source_conversations)} conversations in source database")
            
            # Import each conversation
            for conv in source_conversations:
                try:
                    conv_data = {
                        'id': conv.id,
                        'conversation_id': conv.conversation_id,
                        'active_task_id': conv.active_task_id,
                        'last_modified_at': conv.last_modified_at,
                        'conversation_data': conv.parsed_data or json.loads(conv.conversation_data)
                    }
                    
                    success = self._import_conversation_data(conv_data, overwrite_existing)
                    if success:
                        result.imported_count += 1
                    else:
                        result.skipped_count += 1
                        
                except Exception as e:
                    result.add_error(f"Failed to import conversation {conv.conversation_id}: {e}")
            
            result.success = True
            self.logger.info(f"Database merge completed: {result.imported_count} imported, {result.skipped_count} skipped")
            
        except Exception as e:
            result.add_error(f"Failed to merge databases: {e}")
            self.logger.error(f"Database merge failed: {e}")
        
        return result
    
    def validate_import_file(self, file_path: str) -> Tuple[bool, str, int]:
        """Validate an import file and return info"""
        try:
            file_path = Path(file_path)
            
            if not file_path.exists():
                return False, "File does not exist", 0
            
            # Determine file type and validate
            if file_path.suffix == '.json' or (file_path.suffix == '.gz' and file_path.stem.endswith('.json')):
                return self._validate_json_file(str(file_path))
            elif file_path.suffix == '.sqlite' or (file_path.suffix == '.gz' and file_path.stem.endswith('.sqlite')):
                return self._validate_sqlite_file(str(file_path))
            elif file_path.suffix == '.csv':
                return self._validate_csv_file(str(file_path))
            else:
                return False, f"Unsupported file format: {file_path.suffix}", 0
                
        except Exception as e:
            return False, f"Validation error: {e}", 0
    
    def _validate_json_file(self, file_path: str) -> Tuple[bool, str, int]:
        """Validate JSON import file"""
        try:
            file_path = Path(file_path)
            
            if file_path.suffix == '.gz':
                with gzip.open(file_path, 'rt', encoding='utf-8') as f:
                    data = json.load(f)
            else:
                with open(file_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
            
            if not isinstance(data, dict):
                return False, "Invalid JSON: root must be an object", 0
            
            if 'conversations' not in data:
                return False, "Invalid JSON: missing 'conversations' key", 0
            
            conversations = data['conversations']
            if not isinstance(conversations, list):
                return False, "Invalid JSON: 'conversations' must be a list", 0
            
            # Check for required fields in conversations
            for i, conv in enumerate(conversations[:5]):  # Check first 5
                if not isinstance(conv, dict):
                    return False, f"Invalid conversation {i}: must be an object", 0
                if 'conversation_id' not in conv:
                    return False, f"Invalid conversation {i}: missing 'conversation_id'", 0
            
            return True, f"Valid JSON export with {len(conversations)} conversations", len(conversations)
            
        except json.JSONDecodeError as e:
            return False, f"Invalid JSON syntax: {e}", 0
        except Exception as e:
            return False, f"JSON validation error: {e}", 0
    
    def _validate_sqlite_file(self, file_path: str) -> Tuple[bool, str, int]:
        """Validate SQLite import file"""
        try:
            file_path = Path(file_path)
            temp_path = None
            
            # Handle compressed file
            if file_path.suffix == '.gz':
                temp_path = file_path.parent / f"temp_validate_{datetime.now().strftime('%Y%m%d_%H%M%S')}.sqlite"
                with gzip.open(file_path, 'rb') as f_in:
                    with open(temp_path, 'wb') as f_out:
                        f_out.write(f_in.read())
                db_path = str(temp_path)
            else:
                db_path = str(file_path)
            
            try:
                # Test database connection and structure
                conn = sqlite3.connect(db_path)
                cursor = conn.cursor()
                
                # Check for agent_conversations table
                cursor.execute("""
                    SELECT name FROM sqlite_master 
                    WHERE type='table' AND name='agent_conversations'
                """)
                
                if not cursor.fetchone():
                    return False, "Invalid SQLite: missing 'agent_conversations' table", 0
                
                # Count conversations
                cursor.execute("SELECT COUNT(*) FROM agent_conversations")
                count = cursor.fetchone()[0]
                
                conn.close()
                
                return True, f"Valid SQLite database with {count} conversations", count
                
            finally:
                if temp_path and temp_path.exists():
                    temp_path.unlink()
            
        except sqlite3.Error as e:
            return False, f"SQLite error: {e}", 0
        except Exception as e:
            return False, f"SQLite validation error: {e}", 0
    
    def _validate_csv_file(self, file_path: str) -> Tuple[bool, str, int]:
        """Validate CSV import file"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                
                # Check required columns
                required_columns = ['Conversation ID', 'Last Modified', 'Raw Data']
                if not all(col in reader.fieldnames for col in required_columns):
                    missing = [col for col in required_columns if col not in reader.fieldnames]
                    return False, f"Missing required columns: {missing}", 0
                
                # Count rows
                count = sum(1 for row in reader)
                
                return True, f"Valid CSV with {count} conversations", count
                
        except Exception as e:
            return False, f"CSV validation error: {e}", 0


if __name__ == "__main__":
    # Test import functionality
    logging.basicConfig(level=logging.INFO)
    
    import_manager = ImportManager()
    
    # Test file validation
    print("Testing import functionality...")
    
    # You can test with actual files here
    # result = import_manager.validate_import_file("test_export.json")
    # print(f"Validation result: {result}")
    
    print("Import manager ready!")