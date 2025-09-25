#!/usr/bin/env python3
"""
Warp Chat Archiver - Export Manager
Handles exporting conversations to various formats
"""

import json
import html
import csv
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any, Optional
import logging
from database_manager import ChatConversation, WarpDatabaseManager


class ExportManager:
    """Manages export operations for Warp conversations"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
    
    def export_to_json(self, conversations: List[ChatConversation], output_path: str) -> bool:
        """Export conversations to JSON format"""
        try:
            output_path = Path(output_path)
            output_path.parent.mkdir(parents=True, exist_ok=True)
            
            export_data = {
                'export_timestamp': datetime.now().isoformat(),
                'total_conversations': len(conversations),
                'conversations': []
            }
            
            for conv in conversations:
                conv_data = {
                    'id': conv.id,
                    'conversation_id': conv.conversation_id,
                    'active_task_id': conv.active_task_id,
                    'last_modified_at': conv.last_modified_at,
                    'message_count': conv.message_count,
                    'summary': conv.get_summary(),
                    'conversation_data': conv.parsed_data or json.loads(conv.conversation_data) if conv.conversation_data else {}
                }
                export_data['conversations'].append(conv_data)
            
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(export_data, f, indent=2, ensure_ascii=False)
            
            self.logger.info(f"Exported {len(conversations)} conversations to JSON: {output_path}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to export to JSON: {e}")
            return False
    
    def export_to_markdown(self, conversations: List[ChatConversation], output_path: str) -> bool:
        """Export conversations to Markdown format"""
        try:
            output_path = Path(output_path)
            output_path.parent.mkdir(parents=True, exist_ok=True)
            
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write("# Warp Chat Archive\n\n")
                f.write(f"**Export Date:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                f.write(f"**Total Conversations:** {len(conversations)}\n\n")
                f.write("---\n\n")
                
                for i, conv in enumerate(conversations, 1):
                    f.write(f"## Conversation {i}\n\n")
                    f.write(f"**ID:** `{conv.conversation_id}`\n")
                    f.write(f"**Date:** {conv.last_modified_at}\n")
                    f.write(f"**Summary:** {conv.get_summary()}\n")
                    f.write(f"**Message Count:** {conv.message_count}\n\n")
                    
                    if conv.active_task_id:
                        f.write(f"**Active Task:** `{conv.active_task_id}`\n\n")
                    
                    # Format conversation data
                    if conv.parsed_data:
                        f.write("### Content\n\n")
                        self._write_conversation_markdown(f, conv.parsed_data)
                    
                    f.write("\n---\n\n")
            
            self.logger.info(f"Exported {len(conversations)} conversations to Markdown: {output_path}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to export to Markdown: {e}")
            return False
    
    def _write_conversation_markdown(self, f, data: Dict[str, Any]):
        """Write conversation data in Markdown format"""
        if 'server_conversation_token' in data:
            f.write(f"**Server Token:** `{data['server_conversation_token']}`\n\n")
        
        if 'todo_lists' in data:
            for idx, todo_list in enumerate(data['todo_lists'], 1):
                f.write(f"#### Todo List {idx}\n\n")
                
                # Completed items
                completed = todo_list.get('completed_items', [])
                if completed:
                    f.write("**Completed Tasks:**\n\n")
                    for item in completed:
                        title = item.get('title', 'No title')
                        description = item.get('description', 'No description')
                        f.write(f"- ✅ **{title}**\n")
                        if description:
                            f.write(f"  - {description}\n")
                        f.write("\n")
                
                # Pending items
                pending = todo_list.get('pending_items', [])
                if pending:
                    f.write("**Pending Tasks:**\n\n")
                    for item in pending:
                        title = item.get('title', 'No title')
                        description = item.get('description', 'No description')
                        f.write(f"- ⏳ **{title}**\n")
                        if description:
                            f.write(f"  - {description}\n")
                        f.write("\n")
    
    def export_to_html(self, conversations: List[ChatConversation], output_path: str) -> bool:
        """Export conversations to HTML format"""
        try:
            output_path = Path(output_path)
            output_path.parent.mkdir(parents=True, exist_ok=True)
            
            with open(output_path, 'w', encoding='utf-8') as f:
                # Write HTML header
                f.write(self._get_html_header())
                
                f.write(f"<h1>Warp Chat Archive</h1>\n")
                f.write(f"<div class='export-info'>\n")
                f.write(f"<p><strong>Export Date:</strong> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>\n")
                f.write(f"<p><strong>Total Conversations:</strong> {len(conversations)}</p>\n")
                f.write(f"</div>\n\n")
                
                # Table of contents
                f.write("<h2>Table of Contents</h2>\n")
                f.write("<ul class='toc'>\n")
                for i, conv in enumerate(conversations, 1):
                    date_str = conv.last_modified_at.split()[0] if ' ' in conv.last_modified_at else conv.last_modified_at
                    f.write(f"<li><a href='#conv_{i}'>Conversation {i} - {date_str}</a></li>\n")
                f.write("</ul>\n\n")
                
                # Conversations
                for i, conv in enumerate(conversations, 1):
                    f.write(f"<div class='conversation' id='conv_{i}'>\n")
                    f.write(f"<h3>Conversation {i}</h3>\n")
                    f.write(f"<div class='conversation-meta'>\n")
                    f.write(f"<p><strong>ID:</strong> <code>{html.escape(conv.conversation_id)}</code></p>\n")
                    f.write(f"<p><strong>Date:</strong> {html.escape(conv.last_modified_at)}</p>\n")
                    f.write(f"<p><strong>Summary:</strong> {html.escape(conv.get_summary())}</p>\n")
                    f.write(f"<p><strong>Message Count:</strong> {conv.message_count}</p>\n")
                    
                    if conv.active_task_id:
                        f.write(f"<p><strong>Active Task:</strong> <code>{html.escape(conv.active_task_id)}</code></p>\n")
                    
                    f.write(f"</div>\n")
                    
                    # Format conversation data
                    if conv.parsed_data:
                        f.write("<div class='conversation-content'>\n")
                        self._write_conversation_html(f, conv.parsed_data)
                        f.write("</div>\n")
                    
                    f.write("</div>\n\n")
                
                f.write(self._get_html_footer())
            
            self.logger.info(f"Exported {len(conversations)} conversations to HTML: {output_path}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to export to HTML: {e}")
            return False
    
    def _write_conversation_html(self, f, data: Dict[str, Any]):
        """Write conversation data in HTML format"""
        if 'server_conversation_token' in data:
            f.write(f"<p><strong>Server Token:</strong> <code>{html.escape(data['server_conversation_token'])}</code></p>\n")
        
        if 'todo_lists' in data:
            for idx, todo_list in enumerate(data['todo_lists'], 1):
                f.write(f"<h4>Todo List {idx}</h4>\n")
                
                # Completed items
                completed = todo_list.get('completed_items', [])
                if completed:
                    f.write("<h5>Completed Tasks</h5>\n")
                    f.write("<ul class='completed-tasks'>\n")
                    for item in completed:
                        title = html.escape(item.get('title', 'No title'))
                        description = html.escape(item.get('description', ''))
                        f.write(f"<li class='completed'>\n")
                        f.write(f"<strong>✅ {title}</strong>\n")
                        if description:
                            f.write(f"<p class='description'>{description}</p>\n")
                        f.write(f"</li>\n")
                    f.write("</ul>\n")
                
                # Pending items
                pending = todo_list.get('pending_items', [])
                if pending:
                    f.write("<h5>Pending Tasks</h5>\n")
                    f.write("<ul class='pending-tasks'>\n")
                    for item in pending:
                        title = html.escape(item.get('title', 'No title'))
                        description = html.escape(item.get('description', ''))
                        f.write(f"<li class='pending'>\n")
                        f.write(f"<strong>⏳ {title}</strong>\n")
                        if description:
                            f.write(f"<p class='description'>{description}</p>\n")
                        f.write(f"</li>\n")
                    f.write("</ul>\n")
    
    def export_to_csv(self, conversations: List[ChatConversation], output_path: str) -> bool:
        """Export conversations to CSV format"""
        try:
            output_path = Path(output_path)
            output_path.parent.mkdir(parents=True, exist_ok=True)
            
            with open(output_path, 'w', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                
                # Write header
                writer.writerow([
                    'ID', 'Conversation ID', 'Active Task ID', 'Last Modified',
                    'Message Count', 'Summary', 'Data Size', 'Raw Data'
                ])
                
                # Write data
                for conv in conversations:
                    writer.writerow([
                        conv.id,
                        conv.conversation_id,
                        conv.active_task_id or '',
                        conv.last_modified_at,
                        conv.message_count,
                        conv.get_summary(),
                        len(conv.conversation_data),
                        conv.conversation_data
                    ])
            
            self.logger.info(f"Exported {len(conversations)} conversations to CSV: {output_path}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to export to CSV: {e}")
            return False
    
    def export_individual_conversations(self, conversations: List[ChatConversation], 
                                      output_dir: str, format: str = 'json') -> bool:
        """Export each conversation as individual files"""
        try:
            output_dir = Path(output_dir)
            output_dir.mkdir(parents=True, exist_ok=True)
            
            success_count = 0
            
            for conv in conversations:
                # Create filename with date and ID
                date_part = conv.last_modified_at.split()[0].replace('-', '')
                filename = f"{date_part}_{conv.conversation_id[:8]}.{format}"
                file_path = output_dir / filename
                
                if format == 'json':
                    success = self.export_to_json([conv], str(file_path))
                elif format == 'md':
                    success = self.export_to_markdown([conv], str(file_path))
                elif format == 'html':
                    success = self.export_to_html([conv], str(file_path))
                elif format == 'csv':
                    success = self.export_to_csv([conv], str(file_path))
                else:
                    self.logger.error(f"Unsupported format: {format}")
                    continue
                
                if success:
                    success_count += 1
            
            self.logger.info(f"Exported {success_count}/{len(conversations)} individual conversations")
            return success_count == len(conversations)
            
        except Exception as e:
            self.logger.error(f"Failed to export individual conversations: {e}")
            return False
    
    def _get_html_header(self) -> str:
        """Get HTML document header with CSS"""
        return '''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Warp Chat Archive</title>
    <style>
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            line-height: 1.6;
            max-width: 1200px;
            margin: 0 auto;
            padding: 20px;
            background-color: #f5f5f5;
        }
        .export-info {
            background: #e3f2fd;
            padding: 15px;
            border-radius: 8px;
            margin-bottom: 20px;
        }
        .toc {
            background: white;
            padding: 20px;
            border-radius: 8px;
            margin-bottom: 20px;
        }
        .toc li {
            margin-bottom: 5px;
        }
        .conversation {
            background: white;
            margin-bottom: 20px;
            padding: 20px;
            border-radius: 8px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }
        .conversation-meta {
            background: #f8f9fa;
            padding: 15px;
            border-radius: 6px;
            margin-bottom: 15px;
        }
        .conversation-content {
            border-left: 3px solid #007acc;
            padding-left: 15px;
        }
        .completed-tasks li.completed {
            color: #28a745;
            margin-bottom: 10px;
        }
        .pending-tasks li.pending {
            color: #ffc107;
            margin-bottom: 10px;
        }
        .description {
            color: #666;
            font-size: 0.9em;
            margin-left: 20px;
        }
        code {
            background: #f1f3f4;
            padding: 2px 6px;
            border-radius: 3px;
            font-family: 'Courier New', monospace;
        }
        h1, h2, h3, h4, h5 {
            color: #333;
        }
    </style>
</head>
<body>
'''
    
    def _get_html_footer(self) -> str:
        """Get HTML document footer"""
        return '''
</body>
</html>'''


if __name__ == "__main__":
    # Test the export manager
    logging.basicConfig(level=logging.INFO)
    
    try:
        db_manager = WarpDatabaseManager()
        conversations = db_manager.get_all_conversations()[:3]  # Test with first 3
        
        export_manager = ExportManager()
        
        # Test different export formats
        export_manager.export_to_json(conversations, "test_export.json")
        export_manager.export_to_markdown(conversations, "test_export.md")
        export_manager.export_to_html(conversations, "test_export.html")
        export_manager.export_to_csv(conversations, "test_export.csv")
        
        print("Export tests completed successfully!")
        
    except Exception as e:
        print(f"Export test failed: {e}")