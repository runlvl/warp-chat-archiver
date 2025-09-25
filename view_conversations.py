#!/usr/bin/env python3
"""
Quick Conversation Content Viewer
View Warp conversation contents in terminal
"""

import sys
from database_manager import WarpDatabaseManager

def main():
    try:
        db_manager = WarpDatabaseManager()
        conversations = db_manager.get_all_conversations()
        
        print(f"🗣️  Found {len(conversations)} conversations\n")
        
        for i, conv in enumerate(conversations[:5], 1):  # Show first 5
            print(f"{'='*80}")
            print(f"CONVERSATION {i}/{len(conversations)}")
            print(f"{'='*80}")
            print(f"ID: {conv.conversation_id}")
            print(f"Date: {conv.last_modified_at}")
            print(f"Summary: {conv.get_summary()}")
            print(f"\n📋 CONTENT:")
            print(f"{'-'*80}")
            
            content = conv.get_readable_content()
            print(content)
            
            print(f"\n{'='*80}\n")
            
            if i < 5 and len(conversations) > 1:
                input("Press Enter to see next conversation...")
                print()
        
        if len(conversations) > 5:
            print(f"... and {len(conversations) - 5} more conversations.")
            print("Use the GUI application to see all conversations.")
            
    except Exception as e:
        print(f"❌ Error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()