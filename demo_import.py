#!/usr/bin/env python3
"""
Import Functionality Demo
Demonstrates the import capabilities of the Warp Chat Archiver
"""

from import_manager import ImportManager
from database_manager import WarpDatabaseManager

def main():
    print("🔄 Warp Chat Archiver - Import Demo")
    print("="*50)
    
    # Initialize managers
    db_manager = WarpDatabaseManager()
    import_manager = ImportManager(db_manager)
    
    # Get initial conversation count
    initial_conversations = db_manager.get_all_conversations()
    print(f"📊 Current conversations in database: {len(initial_conversations)}")
    
    # Test available export files
    test_files = [
        "test_export.json",
        "test_export.csv"
    ]
    
    print(f"\n🔍 Testing import validation:")
    
    for file_path in test_files:
        try:
            is_valid, message, count = import_manager.validate_import_file(file_path)
            
            if is_valid:
                print(f"  ✅ {file_path}: {message}")
                
                # Demo: Show what would be imported (dry run)
                print(f"     📋 Preview: Would import {count} conversations")
                
                # You could uncomment these lines to actually perform imports:
                # print(f"     🔄 Performing import...")
                # result = import_manager.import_from_json(file_path, overwrite_existing=False)
                # if result.success:
                #     print(f"     ✅ Import successful: {result.imported_count} imported, {result.skipped_count} skipped")
                # else:
                #     print(f"     ❌ Import failed: {result.errors[0] if result.errors else 'Unknown error'}")
                
            else:
                print(f"  ❌ {file_path}: {message}")
                
        except FileNotFoundError:
            print(f"  ⚠️  {file_path}: File not found (run export first)")
        except Exception as e:
            print(f"  ❌ {file_path}: Error - {e}")
    
    print(f"\n🎯 Import Features Available:")
    print(f"  📁 Supported formats:")
    print(f"     • JSON exports (.json, .json.gz)")
    print(f"     • SQLite backups (.sqlite, .sqlite.gz)")
    print(f"     • CSV exports (.csv)")
    print(f"     • Compressed files (.gz)")
    
    print(f"\n  🔧 Import operations:")
    print(f"     • Single file import")
    print(f"     • Batch import (multiple files)")
    print(f"     • Database merge (from other Warp installations)")
    print(f"     • Backup restore")
    
    print(f"\n  ⚙️  Conflict resolution:")
    print(f"     • Skip existing conversations")
    print(f"     • Update existing conversations")
    print(f"     • Overwrite existing conversations")
    
    print(f"\n  🛡️  Safety features:")
    print(f"     • File validation before import")
    print(f"     • Import preview with conflict analysis")
    print(f"     • Detailed import reports")
    print(f"     • Error handling and rollback")
    
    print(f"\n🚀 Ready to use!")
    print(f"   Start the GUI: python launch.py")
    print(f"   Then go to the 'Import' tab to use these features.")

if __name__ == "__main__":
    main()