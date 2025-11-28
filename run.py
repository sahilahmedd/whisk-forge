import sys
import os

# Ensure current dir is in path
if getattr(sys, 'frozen', False):
    # Running as compiled executable
    application_path = sys._MEIPASS
else:
    # Running from source
    application_path = os.path.dirname(os.path.abspath(__file__))

sys.path.append(application_path)

from src.ui.app_ui import WhiskApp

if __name__ == "__main__":
    app = WhiskApp()
    app.protocol("WM_DELETE_WINDOW", app.on_closing)
    app.mainloop()
