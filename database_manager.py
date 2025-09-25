#!/usr/bin/env python3
"""
Warp Chat Archiver - Database Manager
Core module for interacting with Warp's SQLite database
"""

import sqlite3
import json
import os
import logging
from datetime import datetime, timezone
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass
from pathlib import Path

@dataclass
class ChatConversation:
    """Represents a single Warp chat conversation"""
    id: int
    conversation_id: str
    active_task_id: Optional[str]
    conversation_data: str
    last_modified_at: str
    parsed_data: Optional[Dict[str, Any]] = None
    message_count: int = 0
    
    def __post_init__(self):
        """Parse conversation data and extract metadata"""
        try:
            self.parsed_data = json.loads(self.conversation_data)
            # Count messages/interactions in the conversation
            if isinstance(self.parsed_data, dict):
                self.message_count = self._count_messages()
        except json.JSONDecodeError:
            self.parsed_data = None
            self.message_count = 0
    
    def _count_messages(self) -> int:
        """Count the number of messages in the conversation"""
        count = 0
        if self.parsed_data and 'todo_lists' in self.parsed_data:
            for todo_list in self.parsed_data['todo_lists']:
                if 'completed_items' in todo_list:
                    count += len(todo_list['completed_items'])
                if 'pending_items' in todo_list:
                    count += len(todo_list['pending_items'])
        return count
    
    def get_summary(self) -> str:
        """Get a summary of the conversation"""
        if not self.parsed_data:
            return "No data available"
        
        summary_parts = []
        if self.message_count > 0:
            summary_parts.append(f"{self.message_count} items")
        
        # Try to extract task information
        if 'todo_lists' in self.parsed_data:
            for todo_list in self.parsed_data['todo_lists']:
                completed = len(todo_list.get('completed_items', []))
                pending = len(todo_list.get('pending_items', []))
                if completed > 0:
                    summary_parts.append(f"{completed} completed")
                if pending > 0:
                    summary_parts.append(f"{pending} pending")
        
        return ", ".join(summary_parts) if summary_parts else "Empty conversation"
    
    def get_readable_content(self) -> str:
        """Get human-readable conversation content"""
        if not self.parsed_data:
            return "No conversation content available."
        
        content_parts = []
        
        # Add server token info
        if 'server_conversation_token' in self.parsed_data:
            content_parts.append(f"Session Token: {self.parsed_data['server_conversation_token']}\n")
        
        # Process todo lists (main conversation content)
        if 'todo_lists' in self.parsed_data:
            for idx, todo_list in enumerate(self.parsed_data['todo_lists'], 1):
                content_parts.append(f"=== Task Session {idx} ===")
                
                # Completed tasks
                completed_items = todo_list.get('completed_items', [])
                if completed_items:
                    content_parts.append("\n✅ COMPLETED TASKS:")
                    for item in completed_items:
                        title = item.get('title', 'Untitled task')
                        description = item.get('description', '')
                        content_parts.append(f"\n• {title}")
                        if description:
                            # Format description with proper line breaks
                            desc_lines = description.split('. ')
                            for line in desc_lines:
                                if line.strip():
                                    content_parts.append(f"  → {line.strip()}{'.' if not line.endswith('.') else ''}")
                
                # Pending tasks
                pending_items = todo_list.get('pending_items', [])
                if pending_items:
                    content_parts.append("\n⏳ PENDING TASKS:")
                    for item in pending_items:
                        title = item.get('title', 'Untitled task')
                        description = item.get('description', '')
                        content_parts.append(f"\n• {title}")
                        if description:
                            desc_lines = description.split('. ')
                            for line in desc_lines:
                                if line.strip():
                                    content_parts.append(f"  → {line.strip()}{'.' if not line.endswith('.') else ''}")
                
                content_parts.append("\n" + "="*50)
        
        # If no todo lists, show raw data structure
        if not content_parts or len(content_parts) <= 2:
            content_parts.append("\n📋 RAW CONVERSATION DATA:")
            content_parts.append(str(self.parsed_data))
        
        return "\n".join(content_parts)


class WarpDatabaseManager:
    """Manages connections and operations with Warp's SQLite database"""
    
    DEFAULT_DB_PATH = Path.home() / ".local/state/warp-terminal/warp.sqlite"
    
    def __init__(self, db_path: Optional[str] = None, allow_missing: bool = False):
        self.db_path = Path(db_path) if db_path else self.DEFAULT_DB_PATH
        self.logger = logging.getLogger(__name__)
        self.allow_missing = allow_missing
        
        # Verify database exists (unless allow_missing is True)
        if not allow_missing and not self.db_path.exists():
            raise FileNotFoundError(f"Warp database not found at {self.db_path}")
        
        # Set database availability flag
        self.database_available = self.db_path.exists()
    
    def get_connection(self) -> sqlite3.Connection:
        """Get a connection to the Warp database"""
        if not self.database_available:
            raise FileNotFoundError(f"Warp database not available at {self.db_path}")
        
        try:
            conn = sqlite3.connect(str(self.db_path))
            conn.row_factory = sqlite3.Row  # Enable column access by name
            return conn
        except sqlite3.Error as e:
            self.logger.error(f"Failed to connect to database: {e}")
            raise
    
    def get_all_conversations(self) -> List[ChatConversation]:
        """Retrieve all conversations from the database"""
        if not self.database_available:
            self.logger.warning("Database not available, returning empty conversation list")
            return []
        
        query = """
        SELECT id, conversation_id, active_task_id, conversation_data, last_modified_at
        FROM agent_conversations
        ORDER BY last_modified_at DESC
        """
        
        try:
            with self.get_connection() as conn:
                cursor = conn.execute(query)
                rows = cursor.fetchall()
                
                conversations = []
                for row in rows:
                    conv = ChatConversation(
                        id=row['id'],
                        conversation_id=row['conversation_id'],
                        active_task_id=row['active_task_id'],
                        conversation_data=row['conversation_data'],
                        last_modified_at=row['last_modified_at']
                    )
                    conversations.append(conv)
                
                self.logger.info(f"Retrieved {len(conversations)} conversations")
                return conversations
                
        except sqlite3.Error as e:
            self.logger.error(f"Failed to retrieve conversations: {e}")
            return []
        query = """
        SELECT id, conversation_id, active_task_id, conversation_data, last_modified_at
        FROM agent_conversations
        WHERE conversation_id = ?
        """
        
        try:
            with self.get_connection() as conn:
                cursor = conn.execute(query, (conversation_id,))
                row = cursor.fetchone()
                
                if row:
                    return ChatConversation(
                        id=row['id'],
                        conversation_id=row['conversation_id'],
                        active_task_id=row['active_task_id'],
                        conversation_data=row['conversation_data'],
                        last_modified_at=row['last_modified_at']
                    )
                return None
                
        except sqlite3.Error as e:
            self.logger.error(f"Failed to retrieve conversation {conversation_id}: {e}")
            return None
    
    def search_conversations(self, query: str) -> List[ChatConversation]:
        """Search conversations by content"""
        sql_query = """
        SELECT id, conversation_id, active_task_id, conversation_data, last_modified_at
        FROM agent_conversations
        WHERE conversation_data LIKE ? OR conversation_id LIKE ?
        ORDER BY last_modified_at DESC
        """
        
        search_pattern = f"%{query}%"
        
        try:
            with self.get_connection() as conn:
                cursor = conn.execute(sql_query, (search_pattern, search_pattern))
                rows = cursor.fetchall()
                
                conversations = []
                for row in rows:
                    conv = ChatConversation(
                        id=row['id'],
                        conversation_id=row['conversation_id'],
                        active_task_id=row['active_task_id'],
                        conversation_data=row['conversation_data'],
                        last_modified_at=row['last_modified_at']
                    )
                    conversations.append(conv)
                
                self.logger.info(f"Found {len(conversations)} conversations matching '{query}'")
                return conversations
                
        except sqlite3.Error as e:
            self.logger.error(f"Failed to search conversations: {e}")
            return []
    
    def get_conversations_by_date_range(self, start_date: str, end_date: str) -> List[ChatConversation]:
        """Retrieve conversations within a date range"""
        query = """
        SELECT id, conversation_id, active_task_id, conversation_data, last_modified_at
        FROM agent_conversations
        WHERE date(last_modified_at) BETWEEN ? AND ?
        ORDER BY last_modified_at DESC
        """
        
        try:
            with self.get_connection() as conn:
                cursor = conn.execute(query, (start_date, end_date))
                rows = cursor.fetchall()
                
                conversations = []
                for row in rows:
                    conv = ChatConversation(
                        id=row['id'],
                        conversation_id=row['conversation_id'],
                        active_task_id=row['active_task_id'],
                        conversation_data=row['conversation_data'],
                        last_modified_at=row['last_modified_at']
                    )
                    conversations.append(conv)
                
                self.logger.info(f"Found {len(conversations)} conversations between {start_date} and {end_date}")
                return conversations
                
        except sqlite3.Error as e:
            self.logger.error(f"Failed to retrieve conversations by date range: {e}")
            return []
    
    def get_database_stats(self) -> Dict[str, Any]:
        """Get statistics about the database"""
        stats = {
            'total_conversations': 0,
            'database_size': 0,
            'oldest_conversation': None,
            'newest_conversation': None,
            'total_data_size': 0
        }
        
        try:
            # Get database file size
            stats['database_size'] = self.db_path.stat().st_size
            
            with self.get_connection() as conn:
                # Total conversations
                cursor = conn.execute("SELECT COUNT(*) FROM agent_conversations")
                stats['total_conversations'] = cursor.fetchone()[0]
                
                # Date range
                cursor = conn.execute("""
                SELECT 
                    MIN(last_modified_at) as oldest,
                    MAX(last_modified_at) as newest,
                    SUM(LENGTH(conversation_data)) as total_data_size
                FROM agent_conversations
                """)
                row = cursor.fetchone()
                if row:
                    stats['oldest_conversation'] = row[0]
                    stats['newest_conversation'] = row[1]
                    stats['total_data_size'] = row[2] or 0
                
        except sqlite3.Error as e:
            self.logger.error(f"Failed to get database stats: {e}")
        
        return stats
    
    def backup_database(self, backup_path: str) -> bool:
        """Create a backup of the database"""
        try:
            backup_path = Path(backup_path)
            backup_path.parent.mkdir(parents=True, exist_ok=True)
            
            with self.get_connection() as source:
                with sqlite3.connect(str(backup_path)) as backup:
                    source.backup(backup)
            
            self.logger.info(f"Database backed up to {backup_path}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to backup database: {e}")
            return False


if __name__ == "__main__":
    # Test the database manager
    logging.basicConfig(level=logging.INFO)
    
    try:
        db_manager = WarpDatabaseManager()
        conversations = db_manager.get_all_conversations()
        
        print(f"Found {len(conversations)} conversations")
        for conv in conversations[:5]:  # Show first 5
            print(f"- {conv.conversation_id}: {conv.get_summary()} ({conv.last_modified_at})")
            
        stats = db_manager.get_database_stats()
        print(f"\nDatabase stats: {stats}")
        
    except Exception as e:
        print(f"Error: {e}")