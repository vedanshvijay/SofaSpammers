import subprocess
import os
import sys

def install_dependencies():
    print("Installing dependencies for Office IP Messenger...")
    
    # List of dependencies needed
    dependencies = [
        "flet>=0.7.4",
        "emoji",
        "cryptography>=40.0.0",
        "pillow>=9.5.0",
        "argon2-cffi>=23.1.0",
        "python-dotenv>=1.0.0"
    ]
    
    # Install each dependency
    for dep in dependencies:
        print(f"Installing {dep}...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", dep])
    
    # Create assets directory if it doesn't exist
    if not os.path.exists("assets"):
        os.makedirs("assets")
        print("Created assets directory")
    
    # Create a basic icon for the system tray
    if not os.path.exists("assets/icon.png"):
        try:
            from PIL import Image, ImageDraw
            
            # Create a simple blue square icon with white letter M
            img = Image.new('RGBA', (256, 256), color=(0, 0, 0, 0))
            d = ImageDraw.Draw(img)
            
            # Draw background
            d.rectangle([(20, 20), (236, 236)], fill=(25, 118, 210))
            
            # Try to draw a letter M in the center
            try:
                from PIL import ImageFont
                font = ImageFont.truetype("arial.ttf", 150)
                d.text((85, 55), "M", fill=(255, 255, 255), font=font)
            except:
                # If font loading fails, draw a simple shape instead
                d.rectangle([(80, 80), (176, 176)], fill=(255, 255, 255))
            
            img.save('assets/icon.png')
            print("Created default icon at assets/icon.png")
        except Exception as e:
            print(f"Couldn't create icon: {e}")
            print("Please add your own icon file at assets/icon.png")
    
    print("\nAll dependencies installed successfully!")
    print("You can now run the messenger with: python main.py")

if __name__ == "__main__":
    install_dependencies() 