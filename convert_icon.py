from PIL import Image
import os

def convert():
    try:
        img = Image.open("assets/logo.png")
        img.save("assets/icon.ico", format='ICO', sizes=[(256, 256)])
        print("Converted successfully")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    convert()
