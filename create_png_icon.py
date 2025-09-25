#!/usr/bin/env python3
"""
PNG Icon Creator
Creates PNG icons from SVG using Python
"""

try:
    from PIL import Image, ImageDraw, ImageFont
    PIL_AVAILABLE = True
except ImportError:
    PIL_AVAILABLE = False

def create_simple_png_icon(size=128):
    """Create a simple PNG icon using PIL"""
    if not PIL_AVAILABLE:
        print("⚠️  PIL/Pillow not available, skipping PNG icon creation")
        return False
    
    # Create image with transparency
    img = Image.new('RGBA', (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    
    # Colors (matching SVG design)
    bg_color = (26, 26, 46, 255)  # #1a1a2e
    terminal_color = (15, 52, 96, 255)  # #0f3460
    border_color = (22, 33, 62, 255)  # #16213e
    blue_color = (74, 144, 226, 255)  # #4a90e2
    green_color = (126, 211, 33, 255)  # #7ed321
    orange_color = (245, 166, 35, 255)  # #f5a623
    
    # Draw background circle
    margin = size // 16
    draw.ellipse([margin, margin, size-margin, size-margin], 
                fill=bg_color, outline=border_color, width=2)
    
    # Draw terminal window
    term_x = size // 6
    term_y = size // 4
    term_w = size * 2 // 3
    term_h = size // 2
    
    draw.rounded_rectangle([term_x, term_y, term_x + term_w, term_y + term_h], 
                          radius=size//16, fill=terminal_color, outline=border_color, width=1)
    
    # Draw terminal header
    header_h = size // 10
    draw.rounded_rectangle([term_x, term_y, term_x + term_w, term_y + header_h], 
                          radius=size//16, fill=border_color)
    
    # Draw window controls
    control_r = size // 32
    control_y = term_y + header_h // 2
    draw.ellipse([term_x + size//16 - control_r, control_y - control_r, 
                 term_x + size//16 + control_r, control_y + control_r], fill=(255, 95, 86))
    draw.ellipse([term_x + size//8 - control_r, control_y - control_r, 
                 term_x + size//8 + control_r, control_y + control_r], fill=(255, 189, 46))
    draw.ellipse([term_x + size*3//16 - control_r, control_y - control_r, 
                 term_x + size*3//16 + control_r, control_y + control_r], fill=(39, 202, 63))
    
    # Draw chat bubbles
    bubble_h = size // 12
    
    # User bubble (blue, left)
    bubble_y = term_y + size // 5
    draw.rounded_rectangle([term_x + size//16, bubble_y, term_x + size//3, bubble_y + bubble_h], 
                          radius=size//24, fill=blue_color)
    
    # AI bubble (green, right)
    bubble_y += size // 8
    draw.rounded_rectangle([term_x + size//2, bubble_y, term_x + term_w - size//16, bubble_y + bubble_h], 
                          radius=size//24, fill=green_color)
    
    # Draw archive symbol
    archive_x = term_x + size * 3 // 8
    archive_y = term_y + size * 3 // 8
    archive_w = size // 6
    archive_h = size // 10
    
    draw.rounded_rectangle([archive_x, archive_y, archive_x + archive_w, archive_y + archive_h], 
                          radius=size//32, fill=orange_color, outline=(214, 137, 16), width=1)
    
    # Draw archive lines
    line_y1 = archive_y + archive_h // 4
    line_y2 = archive_y + archive_h // 2
    draw.rectangle([archive_x + size//32, line_y1, archive_x + archive_w - size//32, line_y1 + 2], 
                  fill=(214, 137, 16))
    draw.rectangle([archive_x + size//32, line_y2, archive_x + archive_w * 3//4, line_y2 + 2], 
                  fill=(214, 137, 16))
    
    return img

def main():
    """Create PNG icons in multiple sizes"""
    print("🎨 Creating PNG icons...")
    
    sizes = [16, 24, 32, 48, 64, 128, 256]
    
    for size in sizes:
        try:
            img = create_simple_png_icon(size)
            if img:
                filename = f"warp-chat-archiver-{size}.png"
                img.save(filename, "PNG")
                print(f"✅ Created {filename}")
            else:
                print(f"❌ Failed to create {size}x{size} icon")
        except Exception as e:
            print(f"❌ Error creating {size}x{size} icon: {e}")
    
    # Create a symlink for the default icon
    try:
        import os
        if os.path.exists("warp-chat-archiver-128.png"):
            if os.path.exists("warp-chat-archiver.png"):
                os.remove("warp-chat-archiver.png")
            os.symlink("warp-chat-archiver-128.png", "warp-chat-archiver.png")
            print("✅ Created default icon symlink")
    except Exception as e:
        print(f"⚠️  Could not create symlink: {e}")

if __name__ == "__main__":
    if PIL_AVAILABLE:
        main()
    else:
        print("⚠️  PIL/Pillow not available.")
        print("   Install with: pip install Pillow")
        print("   Or use the SVG icon (works fine on most systems)")