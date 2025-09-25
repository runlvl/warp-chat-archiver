#!/usr/bin/env python3
"""
Warp Chat Archiver Installation Script
Automated setup and configuration
"""

import os
import sys
import shutil
import platform
from pathlib import Path

def create_desktop_file():
    """Create desktop entry for Linux"""
    if platform.system() != "Linux":
        return False
    
    app_dir = Path(__file__).parent.absolute()
    desktop_content = f"""[Desktop Entry]
Version=1.0
Type=Application
Name=Warp Chat Archiver
Comment=Archive and manage Warp Terminal conversations
Exec=python3 {app_dir}/launch.py
Icon={app_dir}/icon.png
Terminal=false
Categories=Utility;Development;
StartupWMClass=warp-chat-archiver
"""
    
    desktop_dir = Path.home() / ".local/share/applications"
    desktop_dir.mkdir(parents=True, exist_ok=True)
    
    desktop_file = desktop_dir / "warp-chat-archiver.desktop"
    
    try:
        with open(desktop_file, 'w') as f:
            f.write(desktop_content)
        
        # Make executable
        desktop_file.chmod(0o755)
        
        print(f"✅ Desktop entry created: {desktop_file}")
        return True
    except Exception as e:
        print(f"❌ Failed to create desktop entry: {e}")
        return False

def create_wrapper_script():
    """Create wrapper script for command line usage"""
    app_dir = Path(__file__).parent.absolute()
    
    # Determine appropriate bin directory
    bin_dirs = [
        Path.home() / ".local/bin",
        Path.home() / "bin",
        Path("/usr/local/bin"),
    ]
    
    target_bin = None
    for bin_dir in bin_dirs:
        if bin_dir.exists() or bin_dir == Path.home() / ".local/bin":
            target_bin = bin_dir
            break
    
    if not target_bin:
        print("❌ No suitable bin directory found")
        return False
    
    # Create bin directory if it doesn't exist
    target_bin.mkdir(parents=True, exist_ok=True)
    
    wrapper_script = target_bin / "warp-chat-archiver"
    
    script_content = f"""#!/bin/bash
# Warp Chat Archiver Wrapper Script
cd "{app_dir}"
exec python3 launch.py "$@"
"""
    
    try:
        with open(wrapper_script, 'w') as f:
            f.write(script_content)
        
        wrapper_script.chmod(0o755)
        
        print(f"✅ Command wrapper created: {wrapper_script}")
        
        # Check if bin directory is in PATH
        if str(target_bin) not in os.environ.get('PATH', ''):
            print(f"⚠️  Note: Add {target_bin} to your PATH to use 'warp-chat-archiver' command")
            print(f"   Add this to your ~/.bashrc or ~/.zshrc:")
            print(f"   export PATH=\"{target_bin}:$PATH\"")
        
        return True
    except Exception as e:
        print(f"❌ Failed to create wrapper script: {e}")
        return False

def setup_directories():
    """Set up application directories"""
    directories = [
        Path.home() / "warp-chat-backups",
        Path.home() / "warp_exports",
        Path.home() / ".config" / "warp-chat-archiver",
    ]
    
    for directory in directories:
        directory.mkdir(parents=True, exist_ok=True)
        print(f"✅ Created directory: {directory}")

def create_sample_config():
    """Create sample configuration file"""
    config_dir = Path.home() / ".config" / "warp-chat-archiver"
    sample_config = config_dir / "sample-config.json"
    
    config_content = {
        "backup_config": {
            "backup_dir": str(Path.home() / "warp-chat-backups"),
            "enable_compression": True,
            "retention_days": 30,
            "max_backups": 10,
            "backup_format": "sqlite",
            "include_metadata": True
        },
        "ui_settings": {
            "export_format": "json",
            "export_mode": "single",
            "export_path": str(Path.home() / "warp_exports"),
            "log_level": "INFO",
            "auto_refresh": True,
            "refresh_interval": 30
        }
    }
    
    try:
        import json
        with open(sample_config, 'w') as f:
            json.dump(config_content, f, indent=2)
        
        print(f"✅ Sample configuration created: {sample_config}")
        return True
    except Exception as e:
        print(f"❌ Failed to create sample config: {e}")
        return False

def setup_cron_backup():
    """Offer to set up automatic backups"""
    if platform.system() not in ["Linux", "Darwin"]:
        return False
    
    response = input("\n🕐 Set up automatic daily backups? (y/N): ").lower().strip()
    if response != 'y':
        return False
    
    app_dir = Path(__file__).parent.absolute()
    backup_script = app_dir / "run_backup.py"
    
    # Create backup script
    backup_content = f"""#!/usr/bin/env python3
import sys
import os
sys.path.insert(0, '{app_dir}')

from backup_manager import BackupManager, BackupConfig
from pathlib import Path
import logging

# Setup logging
log_file = Path.home() / ".warp-chat-archiver-cron.log"
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(log_file),
        logging.StreamHandler()
    ]
)

try:
    config = BackupConfig(backup_dir=str(Path.home() / "warp-chat-backups"))
    backup_manager = BackupManager(config)
    
    backup_info = backup_manager.create_full_backup()
    if backup_info:
        print(f"Backup created: {{backup_info.filename}}")
        backup_manager.cleanup_old_backups()
    else:
        print("Backup failed!")
        sys.exit(1)
        
except Exception as e:
    print(f"Backup error: {{e}}")
    sys.exit(1)
"""
    
    try:
        with open(backup_script, 'w') as f:
            f.write(backup_content)
        
        backup_script.chmod(0o755)
        
        # Add to crontab
        import subprocess
        
        cron_command = f"0 2 * * * {backup_script} >> ~/.warp-chat-archiver-cron.log 2>&1"
        
        # Get current crontab
        try:
            result = subprocess.run(["crontab", "-l"], capture_output=True, text=True, check=False)
            current_crontab = result.stdout if result.returncode == 0 else ""
        except:
            current_crontab = ""
        
        # Check if already exists
        if str(backup_script) in current_crontab:
            print("✅ Cron job already exists")
            return True
        
        # Add new cron job
        new_crontab = current_crontab.rstrip() + f"\n{cron_command}\n"
        
        process = subprocess.run(["crontab", "-"], input=new_crontab, text=True, check=True)
        
        print("✅ Automatic daily backups configured (2 AM)")
        print(f"   Log file: ~/.warp-chat-archiver-cron.log")
        return True
        
    except Exception as e:
        print(f"❌ Failed to set up automatic backups: {e}")
        return False

def run_tests():
    """Run basic functionality tests"""
    print("\n🧪 Running basic tests...")
    
    try:
        from database_manager import WarpDatabaseManager
        db_manager = WarpDatabaseManager()
        conversations = db_manager.get_all_conversations()
        print(f"✅ Database test passed ({len(conversations)} conversations found)")
    except Exception as e:
        print(f"❌ Database test failed: {e}")
        return False
    
    try:
        from backup_manager import BackupManager, BackupConfig
        test_config = BackupConfig(backup_dir="/tmp/warp_test_install")
        backup_manager = BackupManager(test_config)
        stats = backup_manager.get_backup_stats()
        print("✅ Backup system test passed")
    except Exception as e:
        print(f"❌ Backup test failed: {e}")
        return False
    
    try:
        from export_manager import ExportManager
        export_manager = ExportManager()
        print("✅ Export system test passed")
    except Exception as e:
        print(f"❌ Export test failed: {e}")
        return False
    
    return True

def main():
    """Main installation function"""
    print("🚀 Warp Chat Archiver Installation")
    print("=" * 40)
    
    app_dir = Path(__file__).parent.absolute()
    print(f"Installing from: {app_dir}")
    
    # Basic setup
    print("\\n📁 Setting up directories...")
    setup_directories()
    
    print("\\n⚙️  Creating configuration...")
    create_sample_config()
    
    # System integration
    system = platform.system()
    print(f"\\n🖥️  Setting up system integration ({system})...")
    
    if system == "Linux":
        create_desktop_file()
    
    create_wrapper_script()
    
    # Optional features
    setup_cron_backup()
    
    # Tests
    if not run_tests():
        print("\\n❌ Some tests failed. Installation may be incomplete.")
        sys.exit(1)
    
    # Success message
    print("\\n" + "=" * 50)
    print("✅ Installation completed successfully!")
    print("\\n🎯 How to use:")
    print(f"   GUI: python3 {app_dir}/launch.py")
    
    wrapper = Path.home() / ".local/bin/warp-chat-archiver"
    if wrapper.exists():
        print(f"   CLI: warp-chat-archiver")
    
    print("\\n📚 Documentation:")
    print(f"   README: {app_dir}/README.md")
    print(f"   Config: ~/.config/warp-chat-archiver/")
    print(f"   Backups: ~/warp-chat-backups/")
    print(f"   Exports: ~/warp_exports/")
    
    print("\\n🎉 Happy archiving!")

if __name__ == "__main__":
    main()