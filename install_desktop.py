#!/usr/bin/env python3
"""
Desktop Integration Installer
Installs desktop entry and icon for Warp Chat Archiver
"""

import os
import shutil
from pathlib import Path
import subprocess
import sys

def install_desktop_entry():
    """Install the desktop entry file"""
    # Paths
    app_dir = Path(__file__).parent.absolute()
    desktop_file = app_dir / "warp-chat-archiver.desktop"
    
    # Destination directories
    local_applications = Path.home() / ".local/share/applications"
    local_icons = Path.home() / ".local/share/icons"
    
    # Create directories if they don't exist
    local_applications.mkdir(parents=True, exist_ok=True)
    local_icons.mkdir(parents=True, exist_ok=True)
    
    # Copy desktop file
    dest_desktop = local_applications / "warp-chat-archiver.desktop"
    
    try:
        # Read and update desktop file with absolute paths
        with open(desktop_file, 'r') as f:
            content = f.read()
        
        # Replace placeholder paths with actual paths
        content = content.replace('/home/johann/warp-chat-archiver', str(app_dir))
        
        # Write updated desktop file
        with open(dest_desktop, 'w') as f:
            f.write(content)
        
        # Make executable
        dest_desktop.chmod(0o755)
        
        print(f"✅ Desktop entry installed: {dest_desktop}")
        
        # Copy icon
        icon_file = app_dir / "warp-chat-archiver.svg"
        dest_icon = local_icons / "warp-chat-archiver.svg"
        
        shutil.copy2(icon_file, dest_icon)
        print(f"✅ Icon installed: {dest_icon}")
        
        # Update desktop database
        try:
            subprocess.run(["update-desktop-database", str(local_applications)], 
                         check=False, capture_output=True)
            print("✅ Desktop database updated")
        except FileNotFoundError:
            print("⚠️  update-desktop-database not found, but installation should still work")
        
        # Try to update icon cache
        try:
            subprocess.run(["gtk-update-icon-cache", str(local_icons)], 
                         check=False, capture_output=True)
            print("✅ Icon cache updated")
        except FileNotFoundError:
            print("⚠️  gtk-update-icon-cache not found, but icons should still work")
        
        return True
        
    except Exception as e:
        print(f"❌ Failed to install desktop entry: {e}")
        return False

def create_system_wide_desktop():
    """Create system-wide desktop entry (requires sudo)"""
    print("\n🔧 System-wide installation (optional):")
    
    response = input("Install system-wide for all users? (requires sudo) [y/N]: ").lower().strip()
    
    if response != 'y':
        print("⏩ Skipping system-wide installation")
        return
    
    app_dir = Path(__file__).parent.absolute()
    
    try:
        # System directories
        system_applications = Path("/usr/share/applications")
        system_icons = Path("/usr/share/icons/hicolor/scalable/apps")
        
        # Desktop file content with absolute paths
        desktop_content = f"""[Desktop Entry]
Version=1.0
Type=Application
Name=Warp Chat Archiver
GenericName=Chat Archive Manager
Comment=Archive, manage and export Warp Terminal conversations
Comment[de]=Archivieren, verwalten und exportieren Sie Warp Terminal-Gespräche

# Execution
Exec=/usr/bin/python3 {app_dir}/launch.py
Path={app_dir}
Icon=warp-chat-archiver
Terminal=false
StartupNotify=true
StartupWMClass=warp-chat-archiver

# Categories and MIME types
Categories=Utility;Development;Office;Database;Archiving;
Keywords=warp;chat;archive;export;backup;conversation;ai;terminal;
MimeType=application/json;application/x-sqlite3;text/csv;

# Application properties
StartupNotify=true
NoDisplay=false
Hidden=false

# Additional metadata
X-GNOME-UsesNotifications=true
"""
        
        # Write temporary files
        temp_desktop = Path("/tmp/warp-chat-archiver.desktop")
        with open(temp_desktop, 'w') as f:
            f.write(desktop_content)
        
        # Install with sudo
        subprocess.run([
            "sudo", "cp", str(temp_desktop), 
            str(system_applications / "warp-chat-archiver.desktop")
        ], check=True)
        
        subprocess.run([
            "sudo", "mkdir", "-p", str(system_icons)
        ], check=True)
        
        subprocess.run([
            "sudo", "cp", str(app_dir / "warp-chat-archiver.svg"),
            str(system_icons / "warp-chat-archiver.svg")
        ], check=True)
        
        # Update system databases
        subprocess.run(["sudo", "update-desktop-database"], check=False)
        subprocess.run(["sudo", "gtk-update-icon-cache", "/usr/share/icons/hicolor"], check=False)
        
        # Cleanup
        temp_desktop.unlink()
        
        print("✅ System-wide installation completed")
        
    except subprocess.CalledProcessError as e:
        print(f"❌ System-wide installation failed: {e}")
    except Exception as e:
        print(f"❌ System-wide installation error: {e}")

def verify_installation():
    """Verify the installation worked"""
    print("\n🔍 Verifying installation...")
    
    # Check files
    local_applications = Path.home() / ".local/share/applications"
    desktop_file = local_applications / "warp-chat-archiver.desktop"
    
    if desktop_file.exists():
        print("✅ Desktop entry found")
        
        # Try to validate desktop file
        try:
            result = subprocess.run([
                "desktop-file-validate", str(desktop_file)
            ], capture_output=True, text=True, check=False)
            
            if result.returncode == 0:
                print("✅ Desktop file validation passed")
            else:
                print(f"⚠️  Desktop file validation warnings: {result.stderr}")
                
        except FileNotFoundError:
            print("⚠️  desktop-file-validate not found, cannot validate")
    else:
        print("❌ Desktop entry not found")
    
    # Check icon
    icon_file = Path.home() / ".local/share/icons/warp-chat-archiver.svg"
    if icon_file.exists():
        print("✅ Icon file found")
    else:
        print("❌ Icon file not found")

def create_mime_associations():
    """Create MIME type associations"""
    print("\n📄 Creating MIME associations...")
    
    mime_dir = Path.home() / ".local/share/mime/packages"
    mime_dir.mkdir(parents=True, exist_ok=True)
    
    mime_file = mime_dir / "warp-chat-archiver.xml"
    
    mime_content = """<?xml version="1.0" encoding="UTF-8"?>
<mime-info xmlns="http://www.freedesktop.org/standards/shared-mime-info">
    <mime-type type="application/x-warp-chat-archive">
        <comment>Warp Chat Archive</comment>
        <comment xml:lang="de">Warp Chat Archiv</comment>
        <icon name="warp-chat-archiver"/>
        <glob pattern="*.warp-chat"/>
        <glob pattern="*.warp-export"/>
    </mime-type>
</mime-info>"""
    
    try:
        with open(mime_file, 'w') as f:
            f.write(mime_content)
        
        # Update MIME database
        subprocess.run(["update-mime-database", str(Path.home() / ".local/share/mime")], 
                      check=False, capture_output=True)
        
        print("✅ MIME associations created")
        
    except Exception as e:
        print(f"⚠️  MIME association creation failed: {e}")

def main():
    print("🖥️  Warp Chat Archiver - Desktop Integration")
    print("="*50)
    
    # Install desktop entry and icon
    if install_desktop_entry():
        print("\n🎉 Local installation completed successfully!")
        
        # System-wide installation (optional)
        create_system_wide_desktop()
        
        # MIME associations
        create_mime_associations()
        
        # Verify installation
        verify_installation()
        
        print(f"\n✨ Installation Summary:")
        print(f"  📋 Desktop entry: ~/.local/share/applications/warp-chat-archiver.desktop")
        print(f"  🎨 Icon: ~/.local/share/icons/warp-chat-archiver.svg")
        print(f"  📁 Application: {Path(__file__).parent.absolute()}")
        
        print(f"\n🚀 The application should now appear in your:")
        print(f"  • Application menu/launcher")
        print(f"  • Activities overview (GNOME)")
        print(f"  • Start menu (KDE)")
        print(f"  • Application finder (XFCE)")
        
        print(f"\n💡 You can also:")
        print(f"  • Right-click JSON/SQLite files → 'Open with Warp Chat Archiver'")
        print(f"  • Pin to taskbar/favorites for quick access")
        print(f"  • Create desktop shortcuts")
        
    else:
        print("\n❌ Installation failed")
        sys.exit(1)

if __name__ == "__main__":
    main()