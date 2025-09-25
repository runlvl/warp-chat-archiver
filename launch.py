#!/usr/bin/env python3
"""
Warp Chat Archiver Launcher
Simple launcher script with system checks and setup
"""

import sys
import os
import platform
from pathlib import Path

def check_python_version():
    """Check if Python version is compatible"""
    if sys.version_info < (3, 8):
        print("❌ Error: Python 3.8 or higher is required.")
        print(f"   Current version: {sys.version}")
        print("   Please upgrade Python and try again.")
        return False
    
    print(f"✅ Python {sys.version.split()[0]} - OK")
    return True

def check_warp_database():
    """Check if Warp database exists"""
    warp_db = Path.home() / ".local/state/warp-terminal/warp.sqlite"
    
    if not warp_db.exists():
        print("⚠️  Warning: Warp database not found at expected location:")
        print(f"   {warp_db}")
        print("   Make sure Warp Terminal is installed and has been used.")
        
        # Try alternative locations
        alt_paths = [
            Path.home() / ".warp" / "warp.sqlite",
            Path.home() / "Library/Application Support/dev.warp.Warp-Stable/warp.sqlite",  # macOS
            Path.home() / "AppData/Local/warp/warp.sqlite",  # Windows
        ]
        
        found_alternative = False
        for alt_path in alt_paths:
            if alt_path.exists():
                print(f"   Found alternative database at: {alt_path}")
                found_alternative = True
                break
        
        if not found_alternative:
            print("   No Warp database found in common locations.")
        
        response = input("\n   Continue anyway? (y/N): ").lower().strip()
        if response != 'y':
            return False
    else:
        print(f"✅ Warp database found - OK")
    
    return True

def check_dependencies():
    """Check if all required modules are available"""
    required_modules = [
        'tkinter', 'sqlite3', 'json', 'threading', 'datetime',
        'pathlib', 'logging', 'gzip', 'tarfile', 'csv', 'html'
    ]
    
    missing_modules = []
    
    for module in required_modules:
        try:
            __import__(module)
        except ImportError:
            missing_modules.append(module)
    
    if missing_modules:
        print(f"❌ Missing required modules: {', '.join(missing_modules)}")
        
        if 'tkinter' in missing_modules:
            system = platform.system()
            if system == "Linux":
                print("   Try installing: sudo apt-get install python3-tk")
            elif system == "Darwin":
                print("   Tkinter should be included with Python on macOS")
            elif system == "Windows":
                print("   Tkinter should be included with Python on Windows")
        
        return False
    
    print("✅ All dependencies available - OK")
    return True

def setup_directories():
    """Create necessary directories"""
    directories = [
        Path.home() / "warp-chat-backups",
        Path.home() / "warp_exports"
    ]
    
    for directory in directories:
        directory.mkdir(exist_ok=True)
    
    print("✅ Directories created - OK")

def main():
    """Main launcher function"""
    print("🚀 Warp Chat Archiver Launcher")
    print("=" * 40)
    
    # System checks
    if not check_python_version():
        sys.exit(1)
    
    if not check_dependencies():
        sys.exit(1)
    
    if not check_warp_database():
        sys.exit(1)
    
    # Setup
    setup_directories()
    
    print("\n✅ All checks passed!")
    print("🎯 Starting Warp Chat Archiver...")
    
    # Change to application directory
    app_dir = Path(__file__).parent
    os.chdir(app_dir)
    
    try:
        # Import and run the main application
        from warp_archiver_gui import main as gui_main
        gui_main()
        
    except ImportError as e:
        print(f"❌ Failed to import application: {e}")
        print("   Make sure all application files are present.")
        sys.exit(1)
    
    except Exception as e:
        print(f"❌ Application error: {e}")
        print("   Check the log file for more details.")
        sys.exit(1)

if __name__ == "__main__":
    main()