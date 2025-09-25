# 🚀 Warp Chat Archiver

[![Python 3.7+](https://img.shields.io/badge/python-3.7+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![GUI Framework](https://img.shields.io/badge/GUI-tkinter-green.svg)](https://docs.python.org/3/library/tkinter.html)
[![Platform](https://img.shields.io/badge/platform-Linux%20%7C%20macOS%20%7C%20Windows-lightgrey.svg)](#compatibility)

A professional desktop application for archiving, managing, and exporting your [Warp Terminal](https://www.warp.dev/) chat conversations. Built with Python and featuring a modern GUI interface with comprehensive backup and export capabilities.

<div align="center">
  <img src="assets/warp-chat-archiver.svg" alt="Warp Chat Archiver Logo" width="200"/>
</div>

## Features

### 🗂️ **Conversation Management**
- Browse all your Warp chat conversations in a clean, searchable interface
- Real-time search through conversation content and metadata
- Date-based filtering and sorting
- Detailed conversation viewer with parsed data display

### 📤 **Export Capabilities**
- **Multiple Formats**: JSON, Markdown, HTML, CSV
- **Export Modes**: Single file or individual files per conversation
- **Selective Export**: Export selected conversations or date ranges
- **Batch Operations**: Export all conversations at once

### 💾 **Automated Backups**
- **Full Backups**: Complete database snapshots
- **Incremental Backups**: Only new conversations since last backup
- **Compression**: Optional gzip compression to save space
- **Retention Policies**: Automatic cleanup of old backups
- **Backup Verification**: Integrity checking for backup files

### ⚙️ **Advanced Features**
- **Scheduling**: Automatic backup scheduling (Linux/macOS cron integration)
- **Configuration Management**: Save and restore application settings
- **Statistics Dashboard**: Database and backup analytics
- **Error Handling**: Robust error recovery and logging

## Installation

### Prerequisites
- Python 3.8 or higher
- Warp Terminal installed and used (with existing chat history)

### Quick Install

1. **Clone or download** the Warp Chat Archiver:
   ```bash
   git clone <repository-url> warp-chat-archiver
   cd warp-chat-archiver
   ```

2. **No additional dependencies required!** The application uses only Python standard library modules.

3. **Run the application**:
   ```bash
   python warp_archiver_gui.py
   ```

### Alternative: Standalone Executable
For non-technical users, pre-built standalone executables are available in the [Releases](releases/) section.

## Usage

### Starting the Application

```bash
cd warp-chat-archiver
python warp_archiver_gui.py
```

The application will automatically detect your Warp database at:
```
~/.local/state/warp-terminal/warp.sqlite
```

### Main Interface

The application features a tabbed interface with five main sections:

#### 1. **Conversations Tab**
- **Search**: Real-time search through all conversations
- **Date Filtering**: Filter conversations by date range
- **Selection**: Select individual or multiple conversations
- **Details**: Double-click any conversation to view detailed information

#### 2. **Export Tab**
- **Format Selection**: Choose from JSON, Markdown, HTML, or CSV
- **Export Mode**: Single file or individual files per conversation
- **Date Range**: Export all conversations or specific date ranges
- **Batch Export**: Export selected conversations or all at once

#### 3. **Backup Tab**
- **Manual Backups**: Create full or incremental backups on demand
- **Configuration**: Set backup directory, retention policies, and compression
- **History**: View all previous backups with verification status
- **Cleanup**: Remove old backups according to retention settings

#### 4. **Settings Tab**
- **Database**: Configure database connection and test connectivity
- **Logging**: Adjust log levels and performance settings
- **Configuration**: Save, load, or reset application settings

#### 5. **Statistics Tab**
- **Database Stats**: Total conversations, file sizes, date ranges
- **Backup Analytics**: Backup counts, sizes, and types
- **Activity Metrics**: Usage patterns and trends (future feature)

### Command Line Usage

For advanced users, individual components can be used from the command line:

```bash
# Test database connection
python database_manager.py

# Create a backup
python backup_manager.py

# Export conversations
python export_manager.py
```

## Configuration

### Application Settings
Settings are automatically saved to `~/.warp-chat-archiver-config.json` and include:

- Backup directory and retention policies
- Export format preferences and output paths
- UI settings and performance options
- Logging configuration

### Backup Configuration
- **Directory**: Where backups are stored (default: `~/warp-chat-backups`)
- **Compression**: Enable gzip compression (recommended)
- **Retention**: Keep backups for specified number of days
- **Max Backups**: Maximum number of backup files to retain
- **Format**: SQLite, JSON, or both

### Automated Scheduling (Linux/macOS)
The application can set up automatic daily backups via cron:

1. Go to **Backup Tab**
2. Click **Setup Scheduling** (feature available in backup manager)
3. Choose backup frequency (daily, weekly, etc.)

Manual cron setup:
```bash
# Edit crontab
crontab -e

# Add daily backup at 2 AM
0 2 * * * /usr/bin/python3 /path/to/warp-chat-archiver/run_backup.py
```

## File Structure

```
warp-chat-archiver/
├── warp_archiver_gui.py      # Main GUI application
├── database_manager.py       # Database connection and operations
├── export_manager.py         # Export functionality
├── backup_manager.py         # Backup and scheduling
├── requirements.txt          # Python dependencies (none!)
├── README.md                 # This file
└── examples/                 # Example configurations and scripts
    ├── config.json           # Sample configuration
    └── backup_script.py      # Standalone backup script
```

## Export Formats

### JSON Format
Structured data with full conversation metadata:
```json
{
  "export_timestamp": "2025-01-15T10:30:00",
  "total_conversations": 42,
  "conversations": [
    {
      "id": 1,
      "conversation_id": "abc123...",
      "last_modified_at": "2025-01-15 09:15:23",
      "message_count": 15,
      "summary": "System optimization tasks",
      "conversation_data": { ... }
    }
  ]
}
```

### Markdown Format
Human-readable format perfect for documentation:
```markdown
# Warp Chat Archive

**Export Date:** 2025-01-15 10:30:00
**Total Conversations:** 42

## Conversation 1
**ID:** abc123...
**Date:** 2025-01-15 09:15:23
**Summary:** System optimization tasks
```

### HTML Format
Web-friendly format with styling and navigation:
- Table of contents with clickable links
- Styled conversation display
- Responsive design for mobile viewing

### CSV Format
Spreadsheet-compatible format for analysis:
```csv
ID,Conversation ID,Active Task ID,Last Modified,Message Count,Summary,Data Size,Raw Data
1,abc123...,task456,2025-01-15 09:15:23,15,"System optimization",2048,"{'todo_lists': [...]}"
```

## Backup Types

### SQLite Backup
- Complete database file backup
- Preserves all data and structure
- Can be restored to any Warp installation
- Compression reduces size by ~60-80%

### JSON Backup
- Human-readable format
- Includes parsed conversation data
- Platform-independent
- Easy to process with other tools

### Incremental Backup
- Only backs up new conversations
- Significantly smaller file sizes
- Faster backup process
- Requires previous full backup as reference

## Troubleshooting

### Common Issues

**"Warp database not found"**
- Ensure Warp Terminal is installed and has been used
- Check that the database path is correct in Settings
- Verify file permissions for the database

**"Failed to create backup"**
- Check disk space in backup directory
- Verify write permissions to backup location
- Ensure database is not locked by Warp

**"Export operation failed"**
- Verify output directory exists and is writable
- Check that conversations are selected for export
- Ensure sufficient disk space for export files

### Log Files
Application logs are written to:
```
~/.warp-chat-archiver.log
```

Enable debug logging in Settings for detailed troubleshooting information.

### Database Issues
If the database becomes corrupted or inaccessible:

1. Close Warp Terminal completely
2. Try running the application again
3. Check database integrity:
   ```bash
   sqlite3 ~/.local/state/warp-terminal/warp.sqlite "PRAGMA integrity_check;"
   ```
4. Restore from backup if necessary

## Development

### Architecture
The application follows a modular design:

- **GUI Layer**: `warp_archiver_gui.py` - User interface and main application logic
- **Data Layer**: `database_manager.py` - Database operations and conversation handling
- **Export Layer**: `export_manager.py` - Format-specific export implementations
- **Backup Layer**: `backup_manager.py` - Backup creation, scheduling, and management

### Adding New Export Formats
To add a new export format:

1. Add export method to `ExportManager` class
2. Update format selection in GUI
3. Add format-specific tests

### Testing
```bash
# Install development dependencies
pip install pytest pytest-cov

# Run tests
pytest tests/

# Run with coverage
pytest --cov=. tests/
```

## Security Considerations

- **Database Access**: Read-only access to Warp database
- **File Permissions**: Backups inherit system permissions
- **No Network Access**: Application works entirely offline
- **Data Privacy**: All processing happens locally

For sensitive conversations, consider:
- Encrypting backup files (future feature)
- Storing backups on encrypted storage
- Using secure deletion for old backups

## Contributing

Contributions are welcome! Please:

1. Fork the repository
2. Create a feature branch
3. Add tests for new functionality
4. Ensure code follows existing style
5. Submit a pull request

### Development Setup
```bash
git clone <repository-url>
cd warp-chat-archiver
python -m venv venv
source venv/bin/activate  # Linux/macOS
# or
venv\\Scripts\\activate   # Windows
pip install -r requirements-dev.txt
```

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Support

- **Issues**: Report bugs or request features on GitHub Issues
- **Documentation**: Check this README for comprehensive usage information
- **Community**: Join discussions in GitHub Discussions

## Changelog

### v1.0.0 (2025-01-15)
- Initial release
- Full GUI application with conversation browsing
- Multiple export formats (JSON, Markdown, HTML, CSV)
- Automated backup system with compression
- Configuration management and statistics
- Cross-platform compatibility

## Acknowledgments

- Thanks to the Warp Terminal team for creating an amazing terminal with agent mode
- Built with Python standard library for maximum compatibility
- GUI framework: Tkinter (included with Python)

---

**Made with ❤️ for the Warp Terminal community**