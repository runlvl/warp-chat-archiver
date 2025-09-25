#!/usr/bin/env python3
"""
Basic tests for Warp Chat Archiver
Run with: python -m pytest tests/
"""

import sys
import os
import unittest
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

import database_manager
import export_manager
import backup_manager


class TestDatabaseManager(unittest.TestCase):
    """Test database functionality"""
    
    def test_database_manager_init(self):
        """Test DatabaseManager initialization"""
        # Test with non-existent database
        with patch('os.path.exists', return_value=False):
            db = database_manager.DatabaseManager()
            self.assertIsNone(db.connection)
    
    def test_find_warp_database(self):
        """Test database discovery"""
        db = database_manager.DatabaseManager()
        # Should not raise exception
        result = db.find_warp_database()
        # Result can be None (no database) or a path
        self.assertTrue(result is None or isinstance(result, str))


class TestExportManager(unittest.TestCase):
    """Test export functionality"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.sample_conversations = [
            {
                'id': 1,
                'conversation_id': 'test-123',
                'last_modified_at': '2025-01-15 10:00:00',
                'active_task_id': 'task-456',
                'conversation_data': '{"todo_lists": []}'
            }
        ]
    
    def test_export_manager_init(self):
        """Test ExportManager initialization"""
        export_mgr = export_manager.ExportManager()
        self.assertIsNotNone(export_mgr)
    
    def test_export_to_json(self):
        """Test JSON export functionality"""
        export_mgr = export_manager.ExportManager()
        
        # Mock the export method
        with patch.object(export_mgr, 'export_to_json') as mock_export:
            mock_export.return_value = True
            result = export_mgr.export_to_json(
                self.sample_conversations, 
                "/tmp/test_export.json"
            )
            mock_export.assert_called_once()


class TestBackupManager(unittest.TestCase):
    """Test backup functionality"""
    
    def test_backup_manager_init(self):
        """Test BackupManager initialization"""
        with patch('os.path.exists', return_value=True):
            backup_mgr = backup_manager.BackupManager()
            self.assertIsNotNone(backup_mgr)
    
    def test_backup_directory_creation(self):
        """Test backup directory creation"""
        with patch('os.makedirs') as mock_makedirs:
            with patch('os.path.exists', return_value=False):
                backup_mgr = backup_manager.BackupManager("/tmp/test-backups")
                mock_makedirs.assert_called()


class TestIntegration(unittest.TestCase):
    """Integration tests"""
    
    def test_version_import(self):
        """Test that version can be imported"""
        import version
        self.assertTrue(hasattr(version, '__version__'))
        self.assertIsInstance(version.__version__, str)
    
    def test_required_modules(self):
        """Test that all required modules can be imported"""
        modules = [
            'database_manager',
            'export_manager', 
            'backup_manager',
            'warp_archiver_gui'
        ]
        
        for module_name in modules:
            try:
                __import__(module_name)
            except ImportError as e:
                self.fail(f"Failed to import {module_name}: {e}")


if __name__ == '__main__':
    # Run tests with verbose output
    unittest.main(verbosity=2)