import sys
import os

# Ensure current dir is in path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from src.ui.app_ui import WhiskApp

if __name__ == "__main__":
    app = WhiskApp()
    app.protocol("WM_DELETE_WINDOW", app.on_closing)
    app.mainloop()
