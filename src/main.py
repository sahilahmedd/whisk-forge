import sys
import os

# Add src to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from src.ui.app_ui import WhiskApp

def main():
    app = WhiskApp()
    app.protocol("WM_DELETE_WINDOW", app.on_closing)
    app.mainloop()
    
if __name__ == "__main__":
    main()
