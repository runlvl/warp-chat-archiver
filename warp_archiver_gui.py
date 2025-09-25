#!/usr/bin/env python3
"""
Warp Chat Archiver - GUI Application
User-friendly interface for managing Warp chat archives
"""

import tkinter as tk
from tkinter import ttk, messagebox, filedialog, scrolledtext, font
import threading
import json
import os
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Dict, Any, Optional
import logging

from database_manager import WarpDatabaseManager, ChatConversation
from export_manager import ExportManager
from backup_manager import BackupManager, BackupConfig, BackupInfo
from import_manager import ImportManager, ImportResult


class WarpArchiverGUI:
    """Main GUI application for Warp Chat Archiver"""
    
    def __init__(self, root):
        self.root = root
        self.root.title("Warp Chat Archiver")
        self.root.geometry("1200x800")
        
        # Configure logging
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger(__name__)
        
        # Initialize managers
        try:
            self.db_manager = WarpDatabaseManager()
            self.export_manager = ExportManager()
            self.import_manager = ImportManager(self.db_manager)
            
            # Default backup config
            self.backup_config = BackupConfig(
                backup_dir=str(Path.home() / "warp-chat-backups"),
                enable_compression=True,
                retention_days=30,
                max_backups=10
            )
            self.backup_manager = BackupManager(self.backup_config)
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to initialize: {e}")
            self.root.destroy()
            return
        
        # State variables
        self.conversations: List[ChatConversation] = []
        self.filtered_conversations: List[ChatConversation] = []
        self.selected_conversations: List[ChatConversation] = []
        
        # Create GUI
        self.create_widgets()
        self.load_conversations()
        
        # Load configuration
        self.load_config()
    
    def create_widgets(self):
        """Create the main GUI widgets"""
        
        # Create notebook for tabs
        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Create tabs
        self.create_conversations_tab()
        self.create_export_tab()
        self.create_import_tab()
        self.create_backup_tab()
        self.create_settings_tab()
        self.create_statistics_tab()
        
        # Status bar
        self.status_bar = ttk.Frame(self.root)
        self.status_bar.pack(fill=tk.X, padx=10, pady=(0, 10))
        
        self.status_label = ttk.Label(self.status_bar, text="Ready")
        self.status_label.pack(side=tk.LEFT)
        
        self.progress_bar = ttk.Progressbar(self.status_bar, mode='indeterminate')
        self.progress_bar.pack(side=tk.RIGHT, padx=(10, 0))
    
    def create_conversations_tab(self):
        """Create the conversations management tab"""
        frame = ttk.Frame(self.notebook)
        self.notebook.add(frame, text="Conversations")
        
        # Search frame
        search_frame = ttk.Frame(frame)
        search_frame.pack(fill=tk.X, padx=10, pady=10)
        
        ttk.Label(search_frame, text="Search:").pack(side=tk.LEFT)
        
        self.search_var = tk.StringVar()
        self.search_var.trace('w', self.on_search_changed)
        search_entry = ttk.Entry(search_frame, textvariable=self.search_var, width=30)
        search_entry.pack(side=tk.LEFT, padx=(10, 0))
        
        ttk.Button(search_frame, text="Refresh", command=self.refresh_conversations).pack(side=tk.RIGHT)
        ttk.Button(search_frame, text="Clear Search", command=self.clear_search).pack(side=tk.RIGHT, padx=(0, 10))
        
        # Date filter frame
        filter_frame = ttk.Frame(frame)
        filter_frame.pack(fill=tk.X, padx=10, pady=(0, 10))
        
        ttk.Label(filter_frame, text="Date Range:").pack(side=tk.LEFT)
        
        self.start_date_var = tk.StringVar(value=(datetime.now() - timedelta(days=30)).strftime("%Y-%m-%d"))
        ttk.Entry(filter_frame, textvariable=self.start_date_var, width=12).pack(side=tk.LEFT, padx=(10, 5))
        
        ttk.Label(filter_frame, text="to").pack(side=tk.LEFT)
        
        self.end_date_var = tk.StringVar(value=datetime.now().strftime("%Y-%m-%d"))
        ttk.Entry(filter_frame, textvariable=self.end_date_var, width=12).pack(side=tk.LEFT, padx=(5, 10))
        
        ttk.Button(filter_frame, text="Apply Filter", command=self.apply_date_filter).pack(side=tk.LEFT)
        ttk.Button(filter_frame, text="Show All", command=self.show_all_conversations).pack(side=tk.LEFT, padx=(10, 0))
        
        # Create main content frame with paned window for split view
        main_content_frame = ttk.Frame(frame)
        main_content_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=(0, 10))
        
        # Create paned window for conversations list and preview
        self.main_paned = ttk.PanedWindow(main_content_frame, orient=tk.HORIZONTAL)
        self.main_paned.pack(fill=tk.BOTH, expand=True)
        
        # Conversations list frame (left side)
        list_frame = ttk.Frame(self.main_paned)
        self.main_paned.add(list_frame, weight=2)
        
        # Content preview frame (right side)
        preview_frame = ttk.LabelFrame(self.main_paned, text="Content Preview")
        self.main_paned.add(preview_frame, weight=1)
        
        # Content preview text widget
        self.content_preview = scrolledtext.ScrolledText(
            preview_frame, 
            height=20, 
            wrap=tk.WORD,
            state=tk.DISABLED,
            font=('Consolas', 10) if 'Consolas' in tk.font.families() else ('Courier', 10)
        )
        self.content_preview.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Treeview for conversations
        columns = ("Date", "ID", "Summary", "Messages")
        self.conversations_tree = ttk.Treeview(list_frame, columns=columns, show="headings", height=15)
        
        # Configure columns
        self.conversations_tree.heading("Date", text="Date")
        self.conversations_tree.heading("ID", text="Conversation ID")
        self.conversations_tree.heading("Summary", text="Summary")
        self.conversations_tree.heading("Messages", text="Messages")
        
        self.conversations_tree.column("Date", width=150)
        self.conversations_tree.column("ID", width=250)
        self.conversations_tree.column("Summary", width=300)
        self.conversations_tree.column("Messages", width=100)
        
        # Scrollbars
        v_scrollbar = ttk.Scrollbar(list_frame, orient=tk.VERTICAL, command=self.conversations_tree.yview)
        h_scrollbar = ttk.Scrollbar(list_frame, orient=tk.HORIZONTAL, command=self.conversations_tree.xview)
        
        self.conversations_tree.configure(yscrollcommand=v_scrollbar.set, xscrollcommand=h_scrollbar.set)
        
        # Pack treeview and scrollbars
        self.conversations_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        v_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        h_scrollbar.pack(side=tk.BOTTOM, fill=tk.X)
        
        # Bind selection event
        self.conversations_tree.bind("<<TreeviewSelect>>", self.on_conversation_select)
        self.conversations_tree.bind("<Double-1>", self.view_conversation_details)
        
        # Selection info frame
        selection_frame = ttk.Frame(frame)
        selection_frame.pack(fill=tk.X, padx=10, pady=(0, 10))
        
        self.selection_label = ttk.Label(selection_frame, text="No conversations selected")
        self.selection_label.pack(side=tk.LEFT)
        
        # Action buttons
        button_frame = ttk.Frame(frame)
        button_frame.pack(fill=tk.X, padx=10)
        
        ttk.Button(button_frame, text="Select All", command=self.select_all_conversations).pack(side=tk.LEFT)
        ttk.Button(button_frame, text="Clear Selection", command=self.clear_selection).pack(side=tk.LEFT, padx=(10, 0))
        ttk.Button(button_frame, text="View Details", command=self.view_conversation_details).pack(side=tk.LEFT, padx=(10, 0))
        ttk.Button(button_frame, text="Quick Export", command=self.quick_export_selected).pack(side=tk.RIGHT)
    
    def create_export_tab(self):
        """Create the export tab"""
        frame = ttk.Frame(self.notebook)
        self.notebook.add(frame, text="Export")
        
        # Export options frame
        options_frame = ttk.LabelFrame(frame, text="Export Options")
        options_frame.pack(fill=tk.X, padx=10, pady=10)
        
        # Format selection
        format_frame = ttk.Frame(options_frame)
        format_frame.pack(fill=tk.X, padx=10, pady=10)
        
        ttk.Label(format_frame, text="Export Format:").pack(side=tk.LEFT)
        
        self.export_format_var = tk.StringVar(value="json")
        formats = [("JSON", "json"), ("Markdown", "md"), ("HTML", "html"), ("CSV", "csv")]
        
        for text, value in formats:
            ttk.Radiobutton(format_frame, text=text, variable=self.export_format_var, value=value).pack(side=tk.LEFT, padx=(20, 0))
        
        # Export mode selection
        mode_frame = ttk.Frame(options_frame)
        mode_frame.pack(fill=tk.X, padx=10, pady=10)
        
        ttk.Label(mode_frame, text="Export Mode:").pack(side=tk.LEFT)
        
        self.export_mode_var = tk.StringVar(value="single")
        modes = [("Single File", "single"), ("Individual Files", "individual")]
        
        for text, value in modes:
            ttk.Radiobutton(mode_frame, text=text, variable=self.export_mode_var, value=value).pack(side=tk.LEFT, padx=(20, 0))
        
        # Date range for export
        date_frame = ttk.Frame(options_frame)
        date_frame.pack(fill=tk.X, padx=10, pady=10)
        
        self.export_all_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(date_frame, text="Export All Conversations", variable=self.export_all_var, 
                       command=self.toggle_export_date_range).pack(side=tk.LEFT)
        
        self.export_date_frame = ttk.Frame(date_frame)
        self.export_date_frame.pack(side=tk.RIGHT)
        
        ttk.Label(self.export_date_frame, text="From:").pack(side=tk.LEFT)
        self.export_start_date_var = tk.StringVar(value=(datetime.now() - timedelta(days=30)).strftime("%Y-%m-%d"))
        ttk.Entry(self.export_date_frame, textvariable=self.export_start_date_var, width=12, state=tk.DISABLED).pack(side=tk.LEFT, padx=(5, 10))
        
        ttk.Label(self.export_date_frame, text="To:").pack(side=tk.LEFT)
        self.export_end_date_var = tk.StringVar(value=datetime.now().strftime("%Y-%m-%d"))
        ttk.Entry(self.export_date_frame, textvariable=self.export_end_date_var, width=12, state=tk.DISABLED).pack(side=tk.LEFT, padx=(5, 0))
        
        # Output path
        path_frame = ttk.Frame(options_frame)
        path_frame.pack(fill=tk.X, padx=10, pady=10)
        
        ttk.Label(path_frame, text="Output Path:").pack(side=tk.LEFT)
        
        self.export_path_var = tk.StringVar(value=str(Path.home() / "warp_exports"))
        ttk.Entry(path_frame, textvariable=self.export_path_var, width=50).pack(side=tk.LEFT, padx=(10, 5))
        ttk.Button(path_frame, text="Browse", command=self.browse_export_path).pack(side=tk.LEFT)
        
        # Export buttons
        export_button_frame = ttk.Frame(frame)
        export_button_frame.pack(fill=tk.X, padx=10, pady=10)
        
        ttk.Button(export_button_frame, text="Export Selected", command=self.export_selected).pack(side=tk.LEFT)
        ttk.Button(export_button_frame, text="Export All", command=self.export_all).pack(side=tk.LEFT, padx=(10, 0))
        ttk.Button(export_button_frame, text="Export by Date Range", command=self.export_by_date_range).pack(side=tk.LEFT, padx=(10, 0))
        
        # Export log
        log_frame = ttk.LabelFrame(frame, text="Export Log")
        log_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        self.export_log = scrolledtext.ScrolledText(log_frame, height=10, state=tk.DISABLED)
        self.export_log.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
    
    def create_import_tab(self):
        """Create the import tab"""
        frame = ttk.Frame(self.notebook)
        self.notebook.add(frame, text="Import")
        
        # Import source selection frame
        source_frame = ttk.LabelFrame(frame, text="Import Source")
        source_frame.pack(fill=tk.X, padx=10, pady=10)
        
        # File selection frame
        file_frame = ttk.Frame(source_frame)
        file_frame.pack(fill=tk.X, padx=10, pady=10)
        
        ttk.Label(file_frame, text="Import File:").pack(side=tk.LEFT)
        
        self.import_file_var = tk.StringVar()
        ttk.Entry(file_frame, textvariable=self.import_file_var, width=60).pack(side=tk.LEFT, padx=(10, 5))
        ttk.Button(file_frame, text="Browse", command=self.browse_import_file).pack(side=tk.LEFT)
        ttk.Button(file_frame, text="Validate", command=self.validate_import_file).pack(side=tk.LEFT, padx=(5, 0))
        
        # Import options frame
        options_frame = ttk.LabelFrame(frame, text="Import Options")
        options_frame.pack(fill=tk.X, padx=10, pady=10)
        
        # Import type detection (auto-filled after validation)
        type_frame = ttk.Frame(options_frame)
        type_frame.pack(fill=tk.X, padx=10, pady=5)
        
        ttk.Label(type_frame, text="Detected Type:").pack(side=tk.LEFT)
        self.import_type_label = ttk.Label(type_frame, text="No file selected", foreground="gray")
        self.import_type_label.pack(side=tk.LEFT, padx=(10, 0))
        
        # Import settings
        settings_frame = ttk.Frame(options_frame)
        settings_frame.pack(fill=tk.X, padx=10, pady=5)
        
        self.overwrite_existing_var = tk.BooleanVar(value=False)
        ttk.Checkbutton(settings_frame, text="Overwrite existing conversations", 
                       variable=self.overwrite_existing_var).pack(side=tk.LEFT)
        
        ttk.Label(settings_frame, text="Conflicts:").pack(side=tk.LEFT, padx=(20, 5))
        self.conflict_resolution_var = tk.StringVar(value="skip")
        conflict_options = [("Skip existing", "skip"), ("Update existing", "update"), ("Always import", "overwrite")]
        
        for text, value in conflict_options:
            ttk.Radiobutton(settings_frame, text=text, variable=self.conflict_resolution_var, value=value).pack(side=tk.LEFT, padx=(10, 0))
        
        # Import actions frame
        actions_frame = ttk.Frame(options_frame)
        actions_frame.pack(fill=tk.X, padx=10, pady=10)
        
        ttk.Button(actions_frame, text="Preview Import", command=self.preview_import).pack(side=tk.LEFT)
        ttk.Button(actions_frame, text="Import Conversations", command=self.perform_import).pack(side=tk.LEFT, padx=(10, 0))
        
        # Special import operations
        special_frame = ttk.LabelFrame(frame, text="Special Import Operations")
        special_frame.pack(fill=tk.X, padx=10, pady=10)
        
        special_buttons_frame = ttk.Frame(special_frame)
        special_buttons_frame.pack(fill=tk.X, padx=10, pady=10)
        
        ttk.Button(special_buttons_frame, text="Merge from Database", command=self.merge_from_database).pack(side=tk.LEFT)
        ttk.Button(special_buttons_frame, text="Import from Backup", command=self.import_from_backup).pack(side=tk.LEFT, padx=(10, 0))
        ttk.Button(special_buttons_frame, text="Batch Import", command=self.batch_import).pack(side=tk.LEFT, padx=(10, 0))
        
        # Import preview/status frame
        preview_frame = ttk.LabelFrame(frame, text="Import Preview & Status")
        preview_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        self.import_preview = scrolledtext.ScrolledText(preview_frame, height=12, state=tk.DISABLED)
        self.import_preview.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
    
    def create_backup_tab(self):
        """Create the backup management tab"""
        frame = ttk.Frame(self.notebook)
        self.notebook.add(frame, text="Backup")
        
        # Backup configuration frame
        config_frame = ttk.LabelFrame(frame, text="Backup Configuration")
        config_frame.pack(fill=tk.X, padx=10, pady=10)
        
        # Backup directory
        dir_frame = ttk.Frame(config_frame)
        dir_frame.pack(fill=tk.X, padx=10, pady=5)
        
        ttk.Label(dir_frame, text="Backup Directory:").pack(side=tk.LEFT)
        self.backup_dir_var = tk.StringVar(value=self.backup_config.backup_dir)
        ttk.Entry(dir_frame, textvariable=self.backup_dir_var, width=50).pack(side=tk.LEFT, padx=(10, 5))
        ttk.Button(dir_frame, text="Browse", command=self.browse_backup_dir).pack(side=tk.LEFT)
        
        # Backup options
        options_frame = ttk.Frame(config_frame)
        options_frame.pack(fill=tk.X, padx=10, pady=5)
        
        self.backup_compression_var = tk.BooleanVar(value=self.backup_config.enable_compression)
        ttk.Checkbutton(options_frame, text="Enable Compression", variable=self.backup_compression_var).pack(side=tk.LEFT)
        
        ttk.Label(options_frame, text="Retention Days:").pack(side=tk.LEFT, padx=(20, 5))
        self.retention_days_var = tk.IntVar(value=self.backup_config.retention_days)
        ttk.Entry(options_frame, textvariable=self.retention_days_var, width=10).pack(side=tk.LEFT)
        
        ttk.Label(options_frame, text="Max Backups:").pack(side=tk.LEFT, padx=(20, 5))
        self.max_backups_var = tk.IntVar(value=self.backup_config.max_backups)
        ttk.Entry(options_frame, textvariable=self.max_backups_var, width=10).pack(side=tk.LEFT)
        
        # Backup format
        format_frame = ttk.Frame(config_frame)
        format_frame.pack(fill=tk.X, padx=10, pady=5)
        
        ttk.Label(format_frame, text="Backup Format:").pack(side=tk.LEFT)
        
        self.backup_format_var = tk.StringVar(value=self.backup_config.backup_format)
        backup_formats = [("SQLite", "sqlite"), ("JSON", "json"), ("Both", "both")]
        
        for text, value in backup_formats:
            ttk.Radiobutton(format_frame, text=text, variable=self.backup_format_var, value=value).pack(side=tk.LEFT, padx=(20, 0))
        
        # Manual backup controls
        manual_frame = ttk.LabelFrame(frame, text="Manual Backup")
        manual_frame.pack(fill=tk.X, padx=10, pady=10)
        
        manual_buttons_frame = ttk.Frame(manual_frame)
        manual_buttons_frame.pack(fill=tk.X, padx=10, pady=10)
        
        ttk.Button(manual_buttons_frame, text="Create Full Backup", command=self.create_full_backup).pack(side=tk.LEFT)
        ttk.Button(manual_buttons_frame, text="Create Incremental Backup", command=self.create_incremental_backup).pack(side=tk.LEFT, padx=(10, 0))
        ttk.Button(manual_buttons_frame, text="Cleanup Old Backups", command=self.cleanup_backups).pack(side=tk.LEFT, padx=(10, 0))
        
        ttk.Button(manual_buttons_frame, text="Apply Settings", command=self.apply_backup_settings).pack(side=tk.RIGHT)
        
        # Backup history
        history_frame = ttk.LabelFrame(frame, text="Backup History")
        history_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # History treeview
        history_columns = ("Date", "Filename", "Type", "Size", "Conversations")
        self.backup_tree = ttk.Treeview(history_frame, columns=history_columns, show="headings", height=8)
        
        for col in history_columns:
            self.backup_tree.heading(col, text=col)
            self.backup_tree.column(col, width=120)
        
        backup_scrollbar = ttk.Scrollbar(history_frame, orient=tk.VERTICAL, command=self.backup_tree.yview)
        self.backup_tree.configure(yscrollcommand=backup_scrollbar.set)
        
        self.backup_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(10, 5), pady=10)
        backup_scrollbar.pack(side=tk.RIGHT, fill=tk.Y, pady=10)
        
        # Backup actions
        backup_actions_frame = ttk.Frame(history_frame)
        backup_actions_frame.pack(fill=tk.X, padx=10, pady=(0, 10))
        
        ttk.Button(backup_actions_frame, text="Refresh History", command=self.refresh_backup_history).pack(side=tk.LEFT)
        ttk.Button(backup_actions_frame, text="Verify Backup", command=self.verify_selected_backup).pack(side=tk.LEFT, padx=(10, 0))
        ttk.Button(backup_actions_frame, text="Open Backup Folder", command=self.open_backup_folder).pack(side=tk.RIGHT)
        
        # Load backup history
        self.refresh_backup_history()
    
    def create_settings_tab(self):
        """Create the settings tab"""
        frame = ttk.Frame(self.notebook)
        self.notebook.add(frame, text="Settings")
        
        # Database settings
        db_frame = ttk.LabelFrame(frame, text="Database Settings")
        db_frame.pack(fill=tk.X, padx=10, pady=10)
        
        # Database path
        db_path_frame = ttk.Frame(db_frame)
        db_path_frame.pack(fill=tk.X, padx=10, pady=10)
        
        ttk.Label(db_path_frame, text="Warp Database Path:").pack(side=tk.LEFT)
        self.db_path_var = tk.StringVar(value=str(self.db_manager.db_path))
        ttk.Entry(db_path_frame, textvariable=self.db_path_var, width=60, state=tk.DISABLED).pack(side=tk.LEFT, padx=(10, 5))
        ttk.Button(db_path_frame, text="Test Connection", command=self.test_database_connection).pack(side=tk.LEFT)
        
        # Logging settings
        log_frame = ttk.LabelFrame(frame, text="Logging Settings")
        log_frame.pack(fill=tk.X, padx=10, pady=10)
        
        log_level_frame = ttk.Frame(log_frame)
        log_level_frame.pack(fill=tk.X, padx=10, pady=10)
        
        ttk.Label(log_level_frame, text="Log Level:").pack(side=tk.LEFT)
        
        self.log_level_var = tk.StringVar(value="INFO")
        log_levels = ["DEBUG", "INFO", "WARNING", "ERROR"]
        
        ttk.Combobox(log_level_frame, textvariable=self.log_level_var, values=log_levels, state="readonly", width=10).pack(side=tk.LEFT, padx=(10, 0))
        
        # Performance settings
        perf_frame = ttk.LabelFrame(frame, text="Performance Settings")
        perf_frame.pack(fill=tk.X, padx=10, pady=10)
        
        perf_options_frame = ttk.Frame(perf_frame)
        perf_options_frame.pack(fill=tk.X, padx=10, pady=10)
        
        self.auto_refresh_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(perf_options_frame, text="Auto-refresh conversations", variable=self.auto_refresh_var).pack(side=tk.LEFT)
        
        ttk.Label(perf_options_frame, text="Refresh Interval (seconds):").pack(side=tk.LEFT, padx=(20, 5))
        self.refresh_interval_var = tk.IntVar(value=30)
        ttk.Entry(perf_options_frame, textvariable=self.refresh_interval_var, width=10).pack(side=tk.LEFT)
        
        # Configuration management
        config_mgmt_frame = ttk.LabelFrame(frame, text="Configuration Management")
        config_mgmt_frame.pack(fill=tk.X, padx=10, pady=10)
        
        config_buttons_frame = ttk.Frame(config_mgmt_frame)
        config_buttons_frame.pack(fill=tk.X, padx=10, pady=10)
        
        ttk.Button(config_buttons_frame, text="Save Configuration", command=self.save_config).pack(side=tk.LEFT)
        ttk.Button(config_buttons_frame, text="Load Configuration", command=self.load_config).pack(side=tk.LEFT, padx=(10, 0))
        ttk.Button(config_buttons_frame, text="Reset to Defaults", command=self.reset_to_defaults).pack(side=tk.LEFT, padx=(10, 0))
        
        # Application info
        info_frame = ttk.LabelFrame(frame, text="Application Information")
        info_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        info_text = scrolledtext.ScrolledText(info_frame, height=8, state=tk.DISABLED)
        info_text.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Add application info
        info_content = f"""Warp Chat Archiver v1.0
        
Database Path: {self.db_manager.db_path}
Backup Directory: {self.backup_config.backup_dir}

Features:
- Browse and search conversations
- Export to multiple formats (JSON, Markdown, HTML, CSV)
- Automated backups with compression
- Backup scheduling and retention policies
- Configuration management

For support and updates, visit the project repository.
"""
        
        info_text.config(state=tk.NORMAL)
        info_text.insert(tk.END, info_content)
        info_text.config(state=tk.DISABLED)
    
    def create_statistics_tab(self):
        """Create the statistics tab"""
        frame = ttk.Frame(self.notebook)
        self.notebook.add(frame, text="Statistics")
        
        # Database statistics
        db_stats_frame = ttk.LabelFrame(frame, text="Database Statistics")
        db_stats_frame.pack(fill=tk.X, padx=10, pady=10)
        
        # Get database stats
        stats = self.db_manager.get_database_stats()
        
        stats_grid_frame = ttk.Frame(db_stats_frame)
        stats_grid_frame.pack(fill=tk.X, padx=10, pady=10)
        
        # Create statistics display
        stats_info = [
            ("Total Conversations:", str(stats.get('total_conversations', 0))),
            ("Database Size:", f"{stats.get('database_size', 0) / (1024*1024):.1f} MB"),
            ("Total Data Size:", f"{stats.get('total_data_size', 0) / (1024*1024):.1f} MB"),
            ("Oldest Conversation:", str(stats.get('oldest_conversation', 'N/A'))),
            ("Newest Conversation:", str(stats.get('newest_conversation', 'N/A')))
        ]
        
        for i, (label, value) in enumerate(stats_info):
            ttk.Label(stats_grid_frame, text=label, font=("TkDefaultFont", 10, "bold")).grid(row=i, column=0, sticky=tk.W, padx=5, pady=2)
            ttk.Label(stats_grid_frame, text=value).grid(row=i, column=1, sticky=tk.W, padx=20, pady=2)
        
        # Backup statistics
        backup_stats_frame = ttk.LabelFrame(frame, text="Backup Statistics")
        backup_stats_frame.pack(fill=tk.X, padx=10, pady=10)
        
        backup_stats = self.backup_manager.get_backup_stats()
        
        backup_grid_frame = ttk.Frame(backup_stats_frame)
        backup_grid_frame.pack(fill=tk.X, padx=10, pady=10)
        
        backup_info = [
            ("Total Backups:", str(backup_stats.get('total_backups', 0))),
            ("Total Backup Size:", f"{backup_stats.get('total_size', 0) / (1024*1024):.1f} MB"),
            ("Oldest Backup:", str(backup_stats.get('oldest_backup', 'N/A'))),
            ("Newest Backup:", str(backup_stats.get('newest_backup', 'N/A')))
        ]
        
        for i, (label, value) in enumerate(backup_info):
            ttk.Label(backup_grid_frame, text=label, font=("TkDefaultFont", 10, "bold")).grid(row=i, column=0, sticky=tk.W, padx=5, pady=2)
            ttk.Label(backup_grid_frame, text=value).grid(row=i, column=1, sticky=tk.W, padx=20, pady=2)
        
        # Backup types breakdown
        if backup_stats.get('backup_types'):
            types_frame = ttk.Frame(backup_stats_frame)
            types_frame.pack(fill=tk.X, padx=10, pady=(10, 10))
            
            ttk.Label(types_frame, text="Backup Types:", font=("TkDefaultFont", 10, "bold")).pack(anchor=tk.W)
            
            for backup_type, count in backup_stats['backup_types'].items():
                ttk.Label(types_frame, text=f"  {backup_type.title()}: {count}").pack(anchor=tk.W, padx=20)
        
        # Activity statistics (placeholder for future implementation)
        activity_frame = ttk.LabelFrame(frame, text="Activity Statistics")
        activity_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        activity_text = scrolledtext.ScrolledText(activity_frame, height=10, state=tk.DISABLED)
        activity_text.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Add activity info (placeholder)
        activity_content = """Activity Statistics:

This section will show:
- Conversations per day/week/month
- Most active time periods
- Average conversation length
- Popular topics/keywords
- Export and backup frequency

(Feature coming in future updates)
"""
        
        activity_text.config(state=tk.NORMAL)
        activity_text.insert(tk.END, activity_content)
        activity_text.config(state=tk.DISABLED)
        
        # Refresh button
        refresh_frame = ttk.Frame(frame)
        refresh_frame.pack(fill=tk.X, padx=10, pady=10)
        
        ttk.Button(refresh_frame, text="Refresh Statistics", command=self.refresh_statistics).pack(side=tk.RIGHT)
    
    def load_conversations(self):
        """Load conversations from database"""
        def load_task():
            self.progress_bar.start()
            self.update_status("Loading conversations...")
            
            try:
                conversations = self.db_manager.get_all_conversations()
                
                # Update UI in main thread
                self.root.after(0, lambda: self.update_conversations_list(conversations))
                
            except Exception as e:
                self.root.after(0, lambda: messagebox.showerror("Error", f"Failed to load conversations: {e}"))
            finally:
                self.root.after(0, lambda: [self.progress_bar.stop(), self.update_status("Ready")])
        
        # Run in background thread
        threading.Thread(target=load_task, daemon=True).start()
    
    def update_conversations_list(self, conversations: List[ChatConversation]):
        """Update the conversations treeview"""
        self.conversations = conversations
        self.filtered_conversations = conversations.copy()
        
        # Clear existing items
        for item in self.conversations_tree.get_children():
            self.conversations_tree.delete(item)
        
        # Add conversations
        for conv in conversations:
            date_str = conv.last_modified_at.split('T')[0] if 'T' in conv.last_modified_at else conv.last_modified_at.split()[0]
            
            self.conversations_tree.insert("", tk.END, values=(
                date_str,
                conv.conversation_id[:40] + "..." if len(conv.conversation_id) > 40 else conv.conversation_id,
                conv.get_summary()[:50] + "..." if len(conv.get_summary()) > 50 else conv.get_summary(),
                str(conv.message_count)
            ), tags=(conv.conversation_id,))
        
        self.update_selection_info()
    
    def on_search_changed(self, *args):
        """Handle search text changes"""
        search_term = self.search_var.get().lower()
        
        if not search_term:
            self.filtered_conversations = self.conversations.copy()
        else:
            self.filtered_conversations = [
                conv for conv in self.conversations
                if (search_term in conv.conversation_id.lower() or
                    search_term in conv.get_summary().lower() or
                    (conv.parsed_data and search_term in str(conv.parsed_data).lower()))
            ]
        
        self.update_filtered_list()
    
    def update_filtered_list(self):
        """Update treeview with filtered results"""
        # Clear existing items
        for item in self.conversations_tree.get_children():
            self.conversations_tree.delete(item)
        
        # Add filtered conversations
        for conv in self.filtered_conversations:
            date_str = conv.last_modified_at.split('T')[0] if 'T' in conv.last_modified_at else conv.last_modified_at.split()[0]
            
            self.conversations_tree.insert("", tk.END, values=(
                date_str,
                conv.conversation_id[:40] + "..." if len(conv.conversation_id) > 40 else conv.conversation_id,
                conv.get_summary()[:50] + "..." if len(conv.get_summary()) > 50 else conv.get_summary(),
                str(conv.message_count)
            ), tags=(conv.conversation_id,))
        
        self.update_selection_info()
    
    def on_conversation_select(self, event):
        """Handle conversation selection"""
        selected_items = self.conversations_tree.selection()
        
        self.selected_conversations = []
        for item in selected_items:
            tags = self.conversations_tree.item(item)['tags']
            if tags:
                conv_id = tags[0]
                # Find conversation by ID
                for conv in self.filtered_conversations:
                    if conv.conversation_id == conv_id:
                        self.selected_conversations.append(conv)
                        break
        
        self.update_selection_info()
    
    def update_selection_info(self):
        """Update selection information label"""
        if not self.selected_conversations:
            self.selection_label.config(text=f"No conversations selected ({len(self.filtered_conversations)} total)")
            self.update_content_preview(None)
        else:
            self.selection_label.config(text=f"{len(self.selected_conversations)} conversations selected ({len(self.filtered_conversations)} total)")
            # Show preview of first selected conversation
            if self.selected_conversations:
                self.update_content_preview(self.selected_conversations[0])
    
    def update_content_preview(self, conversation):
        """Update the content preview pane"""
        self.content_preview.config(state=tk.NORMAL)
        self.content_preview.delete(1.0, tk.END)
        
        if conversation is None:
            self.content_preview.insert(tk.END, "Select a conversation to see its content...")
        else:
            # Show conversation info header
            header = f"Conversation: {conversation.conversation_id[:20]}...\n"
            header += f"Date: {conversation.last_modified_at}\n"
            header += f"Summary: {conversation.get_summary()}\n"
            header += "="*60 + "\n\n"
            
            self.content_preview.insert(tk.END, header)
            
            # Show readable content
            content = conversation.get_readable_content()
            self.content_preview.insert(tk.END, content)
        
        self.content_preview.config(state=tk.DISABLED)
    
    # Import functionality methods
    def browse_import_file(self):
        """Browse for import file"""
        file_path = filedialog.askopenfilename(
            title="Select Import File",
            filetypes=[
                ("All supported", "*.json *.sqlite *.csv *.gz"),
                ("JSON files", "*.json"),
                ("SQLite databases", "*.sqlite"),
                ("CSV files", "*.csv"),
                ("Compressed files", "*.gz"),
                ("All files", "*.*")
            ]
        )
        
        if file_path:
            self.import_file_var.set(file_path)
            # Auto-validate when file is selected
            self.validate_import_file()
    
    def validate_import_file(self):
        """Validate the selected import file"""
        file_path = self.import_file_var.get().strip()
        if not file_path:
            messagebox.showwarning("Warning", "Please select a file to validate.")
            return
        
        def validate_task():
            self.progress_bar.start()
            self.update_status("Validating import file...")
            
            try:
                is_valid, message, count = self.import_manager.validate_import_file(file_path)
                
                if is_valid:
                    file_type = "Unknown"
                    if ".json" in file_path:
                        file_type = "JSON Export"
                    elif ".sqlite" in file_path:
                        file_type = "SQLite Database"
                    elif ".csv" in file_path:
                        file_type = "CSV Export"
                    
                    self.root.after(0, lambda: [
                        self.import_type_label.config(text=f"{file_type} ({count} conversations)", foreground="green"),
                        self.log_import_action(f"✅ Validation successful: {message}"),
                        messagebox.showinfo("Validation Successful", f"{message}\n\nFile is ready for import.")
                    ])
                else:
                    self.root.after(0, lambda: [
                        self.import_type_label.config(text="Invalid file", foreground="red"),
                        self.log_import_action(f"❌ Validation failed: {message}"),
                        messagebox.showerror("Validation Failed", f"File validation failed:\n{message}")
                    ])
                    
            except Exception as e:
                self.root.after(0, lambda: [
                    messagebox.showerror("Error", f"Validation error: {e}"),
                    self.log_import_action(f"❌ Validation error: {e}")
                ])
            finally:
                self.root.after(0, lambda: [self.progress_bar.stop(), self.update_status("Ready")])
        
        threading.Thread(target=validate_task, daemon=True).start()
    
    def preview_import(self):
        """Preview what would be imported"""
        file_path = self.import_file_var.get().strip()
        if not file_path:
            messagebox.showwarning("Warning", "Please select a file to preview.")
            return
        
        def preview_task():
            self.progress_bar.start()
            self.update_status("Analyzing import file...")
            
            try:
                # Validate first
                is_valid, message, count = self.import_manager.validate_import_file(file_path)
                
                if not is_valid:
                    self.root.after(0, lambda: messagebox.showerror("Error", f"Invalid file: {message}"))
                    return
                
                # Generate preview info
                preview_text = f"IMPORT PREVIEW\n{'='*50}\n\n"
                preview_text += f"File: {Path(file_path).name}\n"
                preview_text += f"Type: {message}\n"
                preview_text += f"Conversations to import: {count}\n\n"
                
                overwrite = self.overwrite_existing_var.get()
                conflict_mode = self.conflict_resolution_var.get()
                
                preview_text += f"Import Settings:\n"
                preview_text += f"  - Overwrite existing: {'Yes' if overwrite else 'No'}\n"
                preview_text += f"  - Conflict resolution: {conflict_mode.title()}\n\n"
                
                # Check for potential conflicts
                existing_conversations = self.db_manager.get_all_conversations()
                existing_ids = {conv.conversation_id for conv in existing_conversations}
                
                conflicts = 0
                if file_path.endswith('.json') or (file_path.endswith('.gz') and '.json' in file_path):
                    # Quick check for JSON files
                    try:
                        import json
                        import gzip
                        
                        if file_path.endswith('.gz'):
                            with gzip.open(file_path, 'rt') as f:
                                data = json.load(f)
                        else:
                            with open(file_path, 'r') as f:
                                data = json.load(f)
                        
                        for conv in data.get('conversations', []):
                            if conv.get('conversation_id') in existing_ids:
                                conflicts += 1
                    except:
                        pass
                
                preview_text += f"Potential Conflicts:\n"
                preview_text += f"  - Existing conversations that would be affected: {conflicts}\n"
                preview_text += f"  - New conversations: {count - conflicts}\n\n"
                
                if conflicts > 0:
                    if conflict_mode == "skip":
                        preview_text += f"⚠️  {conflicts} conversations will be SKIPPED (already exist)\n"
                    elif conflict_mode == "update":
                        preview_text += f"🔄 {conflicts} conversations will be UPDATED\n"
                    else:
                        preview_text += f"⚠️  {conflicts} conversations will be OVERWRITTEN\n"
                
                preview_text += f"\n📊 Expected Result:\n"
                if conflict_mode == "skip":
                    preview_text += f"  - Imported: {count - conflicts}\n"
                    preview_text += f"  - Skipped: {conflicts}\n"
                else:
                    preview_text += f"  - Imported: {count}\n"
                    preview_text += f"  - Updated: {conflicts}\n"
                
                self.root.after(0, lambda: [
                    self.update_import_preview(preview_text),
                    self.log_import_action(f"📋 Preview generated: {count} conversations, {conflicts} conflicts")
                ])
                
            except Exception as e:
                self.root.after(0, lambda: [
                    messagebox.showerror("Error", f"Preview failed: {e}"),
                    self.log_import_action(f"❌ Preview error: {e}")
                ])
            finally:
                self.root.after(0, lambda: [self.progress_bar.stop(), self.update_status("Ready")])
        
        threading.Thread(target=preview_task, daemon=True).start()
    
    def perform_import(self):
        """Perform the actual import operation"""
        file_path = self.import_file_var.get().strip()
        if not file_path:
            messagebox.showwarning("Warning", "Please select a file to import.")
            return
        
        # Confirm import
        result = messagebox.askyesno(
            "Confirm Import", 
            f"Are you sure you want to import conversations from:\n{Path(file_path).name}\n\nThis operation cannot be undone."
        )
        
        if not result:
            return
        
        def import_task():
            self.progress_bar.start()
            self.update_status("Importing conversations...")
            
            try:
                overwrite_existing = self.conflict_resolution_var.get() in ["update", "overwrite"]
                
                # Determine import method based on file type
                if file_path.endswith('.json') or (file_path.endswith('.gz') and '.json' in file_path):
                    result = self.import_manager.import_from_json(file_path, overwrite_existing)
                elif file_path.endswith('.sqlite') or (file_path.endswith('.gz') and '.sqlite' in file_path):
                    result = self.import_manager.import_from_backup(file_path, overwrite_existing)
                elif file_path.endswith('.csv'):
                    result = self.import_manager.import_from_csv(file_path, overwrite_existing)
                else:
                    # Try auto-detection
                    result = self.import_manager.import_from_backup(file_path, overwrite_existing)
                
                # Show results
                if result.success:
                    summary = f"Import completed successfully!\n\n"
                    summary += f"📊 Import Summary:\n"
                    summary += f"  • Imported: {result.imported_count} conversations\n"
                    summary += f"  • Skipped: {result.skipped_count} conversations\n"
                    summary += f"  • Errors: {result.error_count} conversations\n"
                    
                    if result.error_count > 0:
                        summary += f"\n⚠️ Errors:\n"
                        for error in result.errors[:5]:  # Show first 5 errors
                            summary += f"  • {error}\n"
                        if len(result.errors) > 5:
                            summary += f"  • ... and {len(result.errors) - 5} more errors\n"
                    
                    self.root.after(0, lambda: [
                        messagebox.showinfo("Import Successful", summary),
                        self.log_import_action(f"✅ Import completed: {result.imported_count} imported, {result.skipped_count} skipped, {result.error_count} errors"),
                        self.update_import_preview(summary),
                        self.refresh_conversations()  # Refresh the conversations list
                    ])
                else:
                    error_msg = f"Import failed!\n\n"
                    if result.errors:
                        error_msg += "Errors:\n"
                        for error in result.errors[:3]:
                            error_msg += f"• {error}\n"
                    
                    self.root.after(0, lambda: [
                        messagebox.showerror("Import Failed", error_msg),
                        self.log_import_action(f"❌ Import failed: {result.errors[0] if result.errors else 'Unknown error'}")
                    ])
                    
            except Exception as e:
                self.root.after(0, lambda: [
                    messagebox.showerror("Error", f"Import error: {e}"),
                    self.log_import_action(f"❌ Import error: {e}")
                ])
            finally:
                self.root.after(0, lambda: [self.progress_bar.stop(), self.update_status("Ready")])
        
        threading.Thread(target=import_task, daemon=True).start()
    
    def merge_from_database(self):
        """Merge conversations from another Warp database"""
        db_path = filedialog.askopenfilename(
            title="Select Warp Database to Merge",
            filetypes=[
                ("SQLite databases", "*.sqlite"),
                ("All files", "*.*")
            ]
        )
        
        if not db_path:
            return
        
        # Confirm merge
        result = messagebox.askyesno(
            "Confirm Database Merge",
            f"Merge conversations from:\n{Path(db_path).name}\n\nThis will add conversations to your current database."
        )
        
        if not result:
            return
        
        def merge_task():
            self.progress_bar.start()
            self.update_status("Merging databases...")
            
            try:
                overwrite_existing = self.conflict_resolution_var.get() in ["update", "overwrite"]
                result = self.import_manager.merge_databases(db_path, overwrite_existing)
                
                if result.success:
                    summary = f"Database merge completed!\n\n"
                    summary += f"📊 Merge Summary:\n"
                    summary += f"  • Merged: {result.imported_count} conversations\n"
                    summary += f"  • Skipped: {result.skipped_count} conversations\n"
                    summary += f"  • Errors: {result.error_count} conversations\n"
                    
                    self.root.after(0, lambda: [
                        messagebox.showinfo("Merge Successful", summary),
                        self.log_import_action(f"🔄 Database merge: {result.imported_count} merged from {Path(db_path).name}"),
                        self.refresh_conversations()
                    ])
                else:
                    self.root.after(0, lambda: [
                        messagebox.showerror("Merge Failed", f"Database merge failed:\n{result.errors[0] if result.errors else 'Unknown error'}"),
                        self.log_import_action(f"❌ Database merge failed: {result.errors[0] if result.errors else 'Unknown error'}")
                    ])
                    
            except Exception as e:
                self.root.after(0, lambda: [
                    messagebox.showerror("Error", f"Merge error: {e}"),
                    self.log_import_action(f"❌ Merge error: {e}")
                ])
            finally:
                self.root.after(0, lambda: [self.progress_bar.stop(), self.update_status("Ready")])
        
        threading.Thread(target=merge_task, daemon=True).start()
    
    def import_from_backup(self):
        """Import conversations from backup file"""
        backup_path = filedialog.askopenfilename(
            title="Select Backup File",
            filetypes=[
                ("All backup files", "*.sqlite *.json *.gz"),
                ("SQLite backups", "*.sqlite *.sqlite.gz"),
                ("JSON backups", "*.json *.json.gz"),
                ("Compressed files", "*.gz"),
                ("All files", "*.*")
            ]
        )
        
        if backup_path:
            self.import_file_var.set(backup_path)
            self.validate_import_file()
    
    def batch_import(self):
        """Import multiple files at once"""
        files = filedialog.askopenfilenames(
            title="Select Files for Batch Import",
            filetypes=[
                ("All supported", "*.json *.sqlite *.csv *.gz"),
                ("JSON files", "*.json"),
                ("SQLite databases", "*.sqlite"),
                ("CSV files", "*.csv"),
                ("Compressed files", "*.gz")
            ]
        )
        
        if not files:
            return
        
        # Confirm batch import
        result = messagebox.askyesno(
            "Confirm Batch Import",
            f"Import {len(files)} files?\n\nThis operation may take some time."
        )
        
        if not result:
            return
        
        def batch_task():
            self.progress_bar.start()
            self.update_status(f"Batch importing {len(files)} files...")
            
            total_imported = 0
            total_skipped = 0
            total_errors = 0
            failed_files = []
            
            try:
                overwrite_existing = self.conflict_resolution_var.get() in ["update", "overwrite"]
                
                for i, file_path in enumerate(files, 1):
                    self.root.after(0, lambda i=i: self.update_status(f"Processing file {i}/{len(files)}: {Path(file_path).name}"))
                    
                    try:
                        # Determine import method
                        if file_path.endswith('.json') or (file_path.endswith('.gz') and '.json' in file_path):
                            result = self.import_manager.import_from_json(file_path, overwrite_existing)
                        elif file_path.endswith('.sqlite') or (file_path.endswith('.gz') and '.sqlite' in file_path):
                            result = self.import_manager.import_from_backup(file_path, overwrite_existing)
                        elif file_path.endswith('.csv'):
                            result = self.import_manager.import_from_csv(file_path, overwrite_existing)
                        else:
                            result = self.import_manager.import_from_backup(file_path, overwrite_existing)
                        
                        if result.success:
                            total_imported += result.imported_count
                            total_skipped += result.skipped_count
                            total_errors += result.error_count
                        else:
                            failed_files.append(Path(file_path).name)
                            
                    except Exception as e:
                        failed_files.append(f"{Path(file_path).name}: {e}")
                        total_errors += 1
                
                # Show batch results
                summary = f"Batch import completed!\n\n"
                summary += f"📊 Batch Summary:\n"
                summary += f"  • Files processed: {len(files)}\n"
                summary += f"  • Total imported: {total_imported} conversations\n"
                summary += f"  • Total skipped: {total_skipped} conversations\n"
                summary += f"  • Total errors: {total_errors}\n"
                
                if failed_files:
                    summary += f"\n⚠️ Failed files:\n"
                    for failed in failed_files[:5]:
                        summary += f"  • {failed}\n"
                    if len(failed_files) > 5:
                        summary += f"  • ... and {len(failed_files) - 5} more\n"
                
                self.root.after(0, lambda: [
                    messagebox.showinfo("Batch Import Complete", summary),
                    self.log_import_action(f"📦 Batch import: {total_imported} imported from {len(files)} files"),
                    self.update_import_preview(summary),
                    self.refresh_conversations()
                ])
                
            except Exception as e:
                self.root.after(0, lambda: [
                    messagebox.showerror("Error", f"Batch import error: {e}"),
                    self.log_import_action(f"❌ Batch import error: {e}")
                ])
            finally:
                self.root.after(0, lambda: [self.progress_bar.stop(), self.update_status("Ready")])
        
        threading.Thread(target=batch_task, daemon=True).start()
    
    def update_import_preview(self, text: str):
        """Update the import preview text area"""
        self.import_preview.config(state=tk.NORMAL)
        self.import_preview.delete(1.0, tk.END)
        self.import_preview.insert(tk.END, text)
        self.import_preview.config(state=tk.DISABLED)
    
    def log_import_action(self, message: str):
        """Log import action to the preview area"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_entry = f"[{timestamp}] {message}\n"
        
        self.import_preview.config(state=tk.NORMAL)
        self.import_preview.insert(tk.END, log_entry)
        self.import_preview.see(tk.END)
        self.import_preview.config(state=tk.DISABLED)
    
    def clear_search(self):
        """Clear search field"""
        self.search_var.set("")
    
    def refresh_conversations(self):
        """Refresh conversations list"""
        self.load_conversations()
    
    def apply_date_filter(self):
        """Apply date range filter"""
        try:
            start_date = self.start_date_var.get()
            end_date = self.end_date_var.get()
            
            self.update_status(f"Filtering by date range: {start_date} to {end_date}")
            
            def filter_task():
                try:
                    filtered = self.db_manager.get_conversations_by_date_range(start_date, end_date)
                    self.root.after(0, lambda: self.update_conversations_list(filtered))
                except Exception as e:
                    self.root.after(0, lambda: messagebox.showerror("Error", f"Failed to filter by date: {e}"))
                finally:
                    self.root.after(0, lambda: self.update_status("Ready"))
            
            threading.Thread(target=filter_task, daemon=True).start()
            
        except Exception as e:
            messagebox.showerror("Error", f"Invalid date range: {e}")
    
    def show_all_conversations(self):
        """Show all conversations"""
        self.load_conversations()
    
    def select_all_conversations(self):
        """Select all visible conversations"""
        for item in self.conversations_tree.get_children():
            self.conversations_tree.selection_add(item)
        
        self.on_conversation_select(None)
    
    def clear_selection(self):
        """Clear conversation selection"""
        self.conversations_tree.selection_remove(self.conversations_tree.selection())
        self.selected_conversations = []
        self.update_selection_info()
    
    def view_conversation_details(self, event=None):
        """View detailed information about selected conversation"""
        if not self.selected_conversations:
            messagebox.showwarning("Warning", "Please select a conversation to view details.")
            return
        
        conv = self.selected_conversations[0]  # Show first selected conversation
        
        # Create details window
        details_window = tk.Toplevel(self.root)
        details_window.title(f"Conversation Details - {conv.conversation_id[:20]}...")
        details_window.geometry("800x600")
        
        # Details notebook
        details_notebook = ttk.Notebook(details_window)
        details_notebook.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Metadata tab
        meta_frame = ttk.Frame(details_notebook)
        details_notebook.add(meta_frame, text="Metadata")
        
        meta_text = scrolledtext.ScrolledText(meta_frame, height=20)
        meta_text.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        meta_content = f"""Conversation ID: {conv.conversation_id}
Active Task ID: {conv.active_task_id or 'None'}
Last Modified: {conv.last_modified_at}
Message Count: {conv.message_count}
Summary: {conv.get_summary()}
Data Size: {len(conv.conversation_data)} characters

Raw Data:
{'-'*50}
{conv.conversation_data[:2000]}{'...' if len(conv.conversation_data) > 2000 else ''}
"""
        
        meta_text.insert(tk.END, meta_content)
        meta_text.config(state=tk.DISABLED)
        
        # Readable content tab
        content_frame = ttk.Frame(details_notebook)
        details_notebook.add(content_frame, text="Conversation Content")
        
        content_text = scrolledtext.ScrolledText(content_frame, height=20, wrap=tk.WORD)
        content_text.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Insert readable content
        readable_content = conv.get_readable_content()
        content_text.insert(tk.END, readable_content)
        content_text.config(state=tk.DISABLED)
        
        # Parsed data tab (raw JSON)
        if conv.parsed_data:
            data_frame = ttk.Frame(details_notebook)
            details_notebook.add(data_frame, text="Raw JSON Data")
            
            data_text = scrolledtext.ScrolledText(data_frame, height=20)
            data_text.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
            
            data_text.insert(tk.END, json.dumps(conv.parsed_data, indent=2, ensure_ascii=False))
            data_text.config(state=tk.DISABLED)
        
        # Actions frame
        actions_frame = ttk.Frame(details_window)
        actions_frame.pack(fill=tk.X, padx=10, pady=(0, 10))
        
        ttk.Button(actions_frame, text="Export This Conversation", 
                  command=lambda: self.export_single_conversation(conv)).pack(side=tk.LEFT)
        ttk.Button(actions_frame, text="Close", command=details_window.destroy).pack(side=tk.RIGHT)
    
    def export_single_conversation(self, conv: ChatConversation):
        """Export a single conversation"""
        file_path = filedialog.asksaveasfilename(
            title="Export Conversation",
            defaultextension=".json",
            filetypes=[
                ("JSON files", "*.json"),
                ("Markdown files", "*.md"),
                ("HTML files", "*.html"),
                ("CSV files", "*.csv")
            ]
        )
        
        if not file_path:
            return
        
        def export_task():
            self.progress_bar.start()
            self.update_status("Exporting conversation...")
            
            try:
                # Determine format from extension
                ext = Path(file_path).suffix.lower()
                
                success = False
                if ext == ".json":
                    success = self.export_manager.export_to_json([conv], file_path)
                elif ext == ".md":
                    success = self.export_manager.export_to_markdown([conv], file_path)
                elif ext == ".html":
                    success = self.export_manager.export_to_html([conv], file_path)
                elif ext == ".csv":
                    success = self.export_manager.export_to_csv([conv], file_path)
                
                if success:
                    self.root.after(0, lambda: messagebox.showinfo("Success", f"Conversation exported to:\n{file_path}"))
                else:
                    self.root.after(0, lambda: messagebox.showerror("Error", "Failed to export conversation"))
                    
            except Exception as e:
                self.root.after(0, lambda: messagebox.showerror("Error", f"Export failed: {e}"))
            finally:
                self.root.after(0, lambda: [self.progress_bar.stop(), self.update_status("Ready")])
        
        threading.Thread(target=export_task, daemon=True).start()
    
    def quick_export_selected(self):
        """Quick export selected conversations to JSON"""
        if not self.selected_conversations:
            messagebox.showwarning("Warning", "Please select conversations to export.")
            return
        
        file_path = filedialog.asksaveasfilename(
            title="Quick Export Selected Conversations",
            defaultextension=".json",
            filetypes=[("JSON files", "*.json")]
        )
        
        if not file_path:
            return
        
        def export_task():
            self.progress_bar.start()
            self.update_status(f"Exporting {len(self.selected_conversations)} conversations...")
            
            try:
                success = self.export_manager.export_to_json(self.selected_conversations, file_path)
                
                if success:
                    self.root.after(0, lambda: messagebox.showinfo("Success", f"Exported {len(self.selected_conversations)} conversations to:\n{file_path}"))
                else:
                    self.root.after(0, lambda: messagebox.showerror("Error", "Failed to export conversations"))
                    
            except Exception as e:
                self.root.after(0, lambda: messagebox.showerror("Error", f"Export failed: {e}"))
            finally:
                self.root.after(0, lambda: [self.progress_bar.stop(), self.update_status("Ready")])
        
        threading.Thread(target=export_task, daemon=True).start()
    
    def toggle_export_date_range(self):
        """Toggle export date range controls"""
        if self.export_all_var.get():
            for child in self.export_date_frame.winfo_children():
                if isinstance(child, ttk.Entry):
                    child.config(state=tk.DISABLED)
        else:
            for child in self.export_date_frame.winfo_children():
                if isinstance(child, ttk.Entry):
                    child.config(state=tk.NORMAL)
    
    def browse_export_path(self):
        """Browse for export path"""
        if self.export_mode_var.get() == "single":
            # File dialog for single file
            file_path = filedialog.asksaveasfilename(
                title="Export File",
                defaultextension=f".{self.export_format_var.get()}",
                filetypes=[(f"{self.export_format_var.get().upper()} files", f"*.{self.export_format_var.get()}")]
            )
            if file_path:
                self.export_path_var.set(file_path)
        else:
            # Directory dialog for individual files
            dir_path = filedialog.askdirectory(title="Export Directory")
            if dir_path:
                self.export_path_var.set(dir_path)
    
    def export_selected(self):
        """Export selected conversations"""
        if not self.selected_conversations:
            messagebox.showwarning("Warning", "Please select conversations to export.")
            return
        
        self._perform_export(self.selected_conversations)
    
    def export_all(self):
        """Export all conversations"""
        if not self.conversations:
            messagebox.showwarning("Warning", "No conversations to export.")
            return
        
        self._perform_export(self.conversations)
    
    def export_by_date_range(self):
        """Export conversations by date range"""
        if self.export_all_var.get():
            conversations = self.conversations
        else:
            try:
                start_date = self.export_start_date_var.get()
                end_date = self.export_end_date_var.get()
                conversations = self.db_manager.get_conversations_by_date_range(start_date, end_date)
            except Exception as e:
                messagebox.showerror("Error", f"Invalid date range: {e}")
                return
        
        if not conversations:
            messagebox.showwarning("Warning", "No conversations found in the specified date range.")
            return
        
        self._perform_export(conversations)
    
    def _perform_export(self, conversations: List[ChatConversation]):
        """Perform the actual export operation"""
        output_path = self.export_path_var.get().strip()
        if not output_path:
            messagebox.showerror("Error", "Please specify an output path.")
            return
        
        export_format = self.export_format_var.get()
        export_mode = self.export_mode_var.get()
        
        def export_task():
            self.progress_bar.start()
            self.update_status(f"Exporting {len(conversations)} conversations...")
            
            try:
                success = False
                
                if export_mode == "single":
                    # Single file export
                    if export_format == "json":
                        success = self.export_manager.export_to_json(conversations, output_path)
                    elif export_format == "md":
                        success = self.export_manager.export_to_markdown(conversations, output_path)
                    elif export_format == "html":
                        success = self.export_manager.export_to_html(conversations, output_path)
                    elif export_format == "csv":
                        success = self.export_manager.export_to_csv(conversations, output_path)
                else:
                    # Individual files export
                    success = self.export_manager.export_individual_conversations(
                        conversations, output_path, export_format
                    )
                
                if success:
                    self.root.after(0, lambda: [
                        messagebox.showinfo("Success", f"Export completed successfully!\n\nExported {len(conversations)} conversations to:\n{output_path}"),
                        self.log_export_action(f"Exported {len(conversations)} conversations to {output_path}")
                    ])
                else:
                    self.root.after(0, lambda: messagebox.showerror("Error", "Export operation failed"))
                    
            except Exception as e:
                self.root.after(0, lambda: messagebox.showerror("Error", f"Export failed: {e}"))
            finally:
                self.root.after(0, lambda: [self.progress_bar.stop(), self.update_status("Ready")])
        
        threading.Thread(target=export_task, daemon=True).start()
    
    def log_export_action(self, message: str):
        """Log export action to the export log"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_entry = f"[{timestamp}] {message}\n"
        
        self.export_log.config(state=tk.NORMAL)
        self.export_log.insert(tk.END, log_entry)
        self.export_log.see(tk.END)
        self.export_log.config(state=tk.DISABLED)
    
    def browse_backup_dir(self):
        """Browse for backup directory"""
        dir_path = filedialog.askdirectory(title="Select Backup Directory", 
                                          initialdir=self.backup_dir_var.get())
        if dir_path:
            self.backup_dir_var.set(dir_path)
    
    def apply_backup_settings(self):
        """Apply backup configuration settings"""
        try:
            self.backup_config.backup_dir = self.backup_dir_var.get()
            self.backup_config.enable_compression = self.backup_compression_var.get()
            self.backup_config.retention_days = self.retention_days_var.get()
            self.backup_config.max_backups = self.max_backups_var.get()
            self.backup_config.backup_format = self.backup_format_var.get()
            
            # Recreate backup manager with new config
            self.backup_manager = BackupManager(self.backup_config)
            
            messagebox.showinfo("Success", "Backup settings applied successfully!")
            self.save_config()
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to apply backup settings: {e}")
    
    def create_full_backup(self):
        """Create a full backup"""
        def backup_task():
            self.progress_bar.start()
            self.update_status("Creating full backup...")
            
            try:
                backup_info = self.backup_manager.create_full_backup()
                
                if backup_info:
                    self.root.after(0, lambda: [
                        messagebox.showinfo("Success", f"Full backup created successfully!\n\nFilename: {backup_info.filename}\nSize: {backup_info.size / (1024*1024):.1f} MB\nConversations: {backup_info.conversation_count}"),
                        self.refresh_backup_history()
                    ])
                else:
                    self.root.after(0, lambda: messagebox.showerror("Error", "Failed to create backup"))
                    
            except Exception as e:
                self.root.after(0, lambda: messagebox.showerror("Error", f"Backup failed: {e}"))
            finally:
                self.root.after(0, lambda: [self.progress_bar.stop(), self.update_status("Ready")])
        
        threading.Thread(target=backup_task, daemon=True).start()
    
    def create_incremental_backup(self):
        """Create an incremental backup"""
        # Get the timestamp of the last backup
        history = self.backup_manager.get_backup_history()
        
        if not history:
            messagebox.showwarning("Warning", "No previous backups found. Creating full backup instead.")
            self.create_full_backup()
            return
        
        last_backup = max(history, key=lambda x: x.timestamp)
        since_timestamp = last_backup.timestamp
        
        def backup_task():
            self.progress_bar.start()
            self.update_status("Creating incremental backup...")
            
            try:
                backup_info = self.backup_manager.create_incremental_backup(since_timestamp)
                
                if backup_info:
                    self.root.after(0, lambda: [
                        messagebox.showinfo("Success", f"Incremental backup created successfully!\n\nFilename: {backup_info.filename}\nSize: {backup_info.size / (1024*1024):.1f} MB\nNew Conversations: {backup_info.conversation_count}"),
                        self.refresh_backup_history()
                    ])
                else:
                    self.root.after(0, lambda: messagebox.showinfo("Info", "No new conversations found for incremental backup"))
                    
            except Exception as e:
                self.root.after(0, lambda: messagebox.showerror("Error", f"Incremental backup failed: {e}"))
            finally:
                self.root.after(0, lambda: [self.progress_bar.stop(), self.update_status("Ready")])
        
        threading.Thread(target=backup_task, daemon=True).start()
    
    def cleanup_backups(self):
        """Cleanup old backups"""
        def cleanup_task():
            self.progress_bar.start()
            self.update_status("Cleaning up old backups...")
            
            try:
                removed_count = self.backup_manager.cleanup_old_backups()
                
                self.root.after(0, lambda: [
                    messagebox.showinfo("Success", f"Cleanup completed!\n\nRemoved {removed_count} old backup files."),
                    self.refresh_backup_history()
                ])
                
            except Exception as e:
                self.root.after(0, lambda: messagebox.showerror("Error", f"Cleanup failed: {e}"))
            finally:
                self.root.after(0, lambda: [self.progress_bar.stop(), self.update_status("Ready")])
        
        threading.Thread(target=cleanup_task, daemon=True).start()
    
    def refresh_backup_history(self):
        """Refresh backup history display"""
        # Clear existing items
        for item in self.backup_tree.get_children():
            self.backup_tree.delete(item)
        
        # Load backup history
        history = self.backup_manager.get_backup_history()
        
        # Sort by timestamp (newest first)
        history.sort(key=lambda x: x.timestamp, reverse=True)
        
        # Add to tree
        for backup in history:
            timestamp_str = backup.timestamp.replace('_', ' ')
            size_mb = f"{backup.size / (1024*1024):.1f} MB"
            
            self.backup_tree.insert("", tk.END, values=(
                timestamp_str,
                backup.filename,
                backup.backup_type.title(),
                size_mb,
                str(backup.conversation_count)
            ))
    
    def verify_selected_backup(self):
        """Verify selected backup"""
        selected_items = self.backup_tree.selection()
        
        if not selected_items:
            messagebox.showwarning("Warning", "Please select a backup to verify.")
            return
        
        # Get selected backup info
        item = selected_items[0]
        values = self.backup_tree.item(item)['values']
        filename = values[1]
        
        backup_path = Path(self.backup_config.backup_dir) / filename
        
        def verify_task():
            self.progress_bar.start()
            self.update_status("Verifying backup...")
            
            try:
                is_valid = self.backup_manager.verify_backup(str(backup_path))
                
                if is_valid:
                    self.root.after(0, lambda: messagebox.showinfo("Success", f"Backup verification passed!\n\n{filename} is valid."))
                else:
                    self.root.after(0, lambda: messagebox.showerror("Error", f"Backup verification failed!\n\n{filename} may be corrupted."))
                    
            except Exception as e:
                self.root.after(0, lambda: messagebox.showerror("Error", f"Verification failed: {e}"))
            finally:
                self.root.after(0, lambda: [self.progress_bar.stop(), self.update_status("Ready")])
        
        threading.Thread(target=verify_task, daemon=True).start()
    
    def open_backup_folder(self):
        """Open backup folder in file manager"""
        import subprocess
        import platform
        
        try:
            backup_dir = Path(self.backup_config.backup_dir)
            
            if platform.system() == "Linux":
                subprocess.run(["xdg-open", str(backup_dir)], check=True)
            elif platform.system() == "Darwin":  # macOS
                subprocess.run(["open", str(backup_dir)], check=True)
            elif platform.system() == "Windows":
                subprocess.run(["explorer", str(backup_dir)], check=True)
            else:
                messagebox.showinfo("Info", f"Backup folder:\n{backup_dir}")
                
        except Exception as e:
            messagebox.showerror("Error", f"Failed to open backup folder: {e}")
    
    def test_database_connection(self):
        """Test database connection"""
        try:
            stats = self.db_manager.get_database_stats()
            messagebox.showinfo("Success", f"Database connection successful!\n\nFound {stats.get('total_conversations', 0)} conversations.")
        except Exception as e:
            messagebox.showerror("Error", f"Database connection failed: {e}")
    
    def save_config(self):
        """Save application configuration"""
        config_path = Path.home() / ".warp-chat-archiver-config.json"
        
        try:
            config_data = {
                'backup_config': self.backup_config.to_dict(),
                'ui_settings': {
                    'export_format': self.export_format_var.get(),
                    'export_mode': self.export_mode_var.get(),
                    'export_path': self.export_path_var.get(),
                    'log_level': self.log_level_var.get(),
                    'auto_refresh': self.auto_refresh_var.get(),
                    'refresh_interval': self.refresh_interval_var.get()
                }
            }
            
            with open(config_path, 'w', encoding='utf-8') as f:
                json.dump(config_data, f, indent=2, ensure_ascii=False)
            
            messagebox.showinfo("Success", f"Configuration saved to:\n{config_path}")
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to save configuration: {e}")
    
    def load_config(self):
        """Load application configuration"""
        config_path = Path.home() / ".warp-chat-archiver-config.json"
        
        if not config_path.exists():
            return
        
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                config_data = json.load(f)
            
            # Load backup config
            if 'backup_config' in config_data:
                backup_config_dict = config_data['backup_config']
                self.backup_config = BackupConfig.from_dict(backup_config_dict)
                self.backup_manager = BackupManager(self.backup_config)
                
                # Update UI
                self.backup_dir_var.set(self.backup_config.backup_dir)
                self.backup_compression_var.set(self.backup_config.enable_compression)
                self.retention_days_var.set(self.backup_config.retention_days)
                self.max_backups_var.set(self.backup_config.max_backups)
                self.backup_format_var.set(self.backup_config.backup_format)
            
            # Load UI settings
            if 'ui_settings' in config_data:
                ui_settings = config_data['ui_settings']
                
                self.export_format_var.set(ui_settings.get('export_format', 'json'))
                self.export_mode_var.set(ui_settings.get('export_mode', 'single'))
                self.export_path_var.set(ui_settings.get('export_path', str(Path.home() / "warp_exports")))
                self.log_level_var.set(ui_settings.get('log_level', 'INFO'))
                self.auto_refresh_var.set(ui_settings.get('auto_refresh', True))
                self.refresh_interval_var.set(ui_settings.get('refresh_interval', 30))
            
        except Exception as e:
            self.logger.error(f"Failed to load configuration: {e}")
    
    def reset_to_defaults(self):
        """Reset configuration to defaults"""
        result = messagebox.askyesno("Confirm Reset", "Are you sure you want to reset all settings to defaults?")
        
        if result:
            # Reset backup config
            self.backup_config = BackupConfig(backup_dir=str(Path.home() / "warp-chat-backups"))
            self.backup_manager = BackupManager(self.backup_config)
            
            # Reset UI variables
            self.backup_dir_var.set(self.backup_config.backup_dir)
            self.backup_compression_var.set(True)
            self.retention_days_var.set(30)
            self.max_backups_var.set(10)
            self.backup_format_var.set('sqlite')
            
            self.export_format_var.set('json')
            self.export_mode_var.set('single')
            self.export_path_var.set(str(Path.home() / "warp_exports"))
            self.log_level_var.set('INFO')
            self.auto_refresh_var.set(True)
            self.refresh_interval_var.set(30)
            
            messagebox.showinfo("Success", "Settings reset to defaults.")
    
    def refresh_statistics(self):
        """Refresh statistics display"""
        # This would recreate the statistics tab
        # For now, just show a message
        messagebox.showinfo("Info", "Statistics refreshed.\n\nNote: To see updated statistics, restart the application.")
    
    def update_status(self, message: str):
        """Update status bar message"""
        self.status_label.config(text=message)
        self.root.update_idletasks()
    
    def run(self):
        """Run the application"""
        self.root.mainloop()


def main():
    """Main entry point"""
    root = tk.Tk()
    app = WarpArchiverGUI(root)
    app.run()


if __name__ == "__main__":
    main()