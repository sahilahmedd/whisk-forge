import customtkinter as ctk
import tkinter as tk
from tkinter import filedialog
import threading
import os
from PIL import Image
from ..core.job_manager import JobManager
from ..core.utils import parse_cookie_json

ctk.set_appearance_mode("System")
ctk.set_default_color_theme("blue")

class WhiskApp(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("WhiskForge - AI Image Generator")
        self.geometry("1100x700")

        self.job_manager = JobManager()
        self._setup_callbacks()
        self.redirect_logging()

        # Grid Layout: 2 Columns (Sidebar, Main)
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        # --- Sidebar ---
        self.sidebar_frame = ctk.CTkFrame(self, width=300, corner_radius=0)
        self.sidebar_frame.grid(row=0, column=0, sticky="nsew")
        self.sidebar_frame.grid_rowconfigure(8, weight=1) # Push bottom items down

        self._setup_sidebar()

        # --- Main Area ---
        self.main_frame = ctk.CTkFrame(self, corner_radius=0, fg_color="transparent")
        self.main_frame.grid(row=0, column=1, sticky="nsew")
        self.main_frame.grid_rowconfigure(1, weight=1)
        self.main_frame.grid_columnconfigure(0, weight=1)

        self._setup_main_area()

    def _setup_callbacks(self):
        self.job_manager.on_status_change = self.update_status
        self.job_manager.on_job_error = self.log_error
        self.job_manager.on_job_complete = self.handle_job_complete

    def _setup_sidebar(self):
        # Title
        ctk.CTkLabel(self.sidebar_frame, text="WhiskForge", font=ctk.CTkFont(size=20, weight="bold")).grid(row=0, column=0, padx=20, pady=(20, 10))

        # Cookie Section (Initial)
        self.cookie_frame = ctk.CTkFrame(self.sidebar_frame, fg_color="transparent")
        self.cookie_frame.grid(row=1, column=0, padx=0, pady=0, sticky="ew")
        
        ctk.CTkLabel(self.cookie_frame, text="Cookie (JSON):", anchor="w").pack(fill="x", padx=20, pady=(10, 0))
        self.cookie_textbox = ctk.CTkTextbox(self.cookie_frame, height=80)
        self.cookie_textbox.pack(fill="x", padx=20, pady=(5, 10))
        
        self.check_btn = ctk.CTkButton(self.cookie_frame, text="Check & Save", command=self.parse_token)
        self.check_btn.pack(fill="x", padx=20, pady=5)
        
        self.token_status = ctk.CTkLabel(self.cookie_frame, text="Session: Not Checked", text_color="gray")
        self.token_status.pack(padx=20, pady=(0, 5))

        # Profile Card (Hidden initially)
        self.profile_card = ctk.CTkFrame(self.sidebar_frame, fg_color=("gray85", "gray25"))
        # self.profile_card.grid(row=1, column=0, padx=20, pady=10, sticky="ew") # Will grid when valid
        
        self.profile_label = ctk.CTkLabel(self.profile_card, text="User Profile", font=ctk.CTkFont(weight="bold"))
        self.profile_label.pack(pady=(10, 5))
        self.email_label = ctk.CTkLabel(self.profile_card, text="")
        self.email_label.pack(pady=2)
        self.expiry_label = ctk.CTkLabel(self.profile_card, text="", font=ctk.CTkFont(size=10), text_color="gray")
        self.expiry_label.pack(pady=(0, 10))
        
        # Configuration Section
        config_frame = ctk.CTkFrame(self.sidebar_frame)
        config_frame.grid(row=6, column=0, padx=20, pady=10, sticky="ew")
        
        # Aspect Ratio
        ctk.CTkLabel(config_frame, text="Aspect Ratio:").grid(row=0, column=0, padx=10, pady=5, sticky="w")
        self.aspect_ratio_var = ctk.StringVar(value="Horizontal 16:9")
        self.aspect_ratio_menu = ctk.CTkOptionMenu(config_frame, variable=self.aspect_ratio_var, 
                                                   values=["Horizontal 16:9", "Vertical 9:16", "Square 1:1"])
        self.aspect_ratio_menu.grid(row=1, column=0, padx=10, pady=(0, 10), sticky="ew")

        # Count
        ctk.CTkLabel(config_frame, text="Count:").grid(row=0, column=1, padx=10, pady=5, sticky="w")
        self.count_var = ctk.StringVar(value="1")
        self.count_menu = ctk.CTkOptionMenu(config_frame, variable=self.count_var, values=["1", "2", "3", "4"], width=70)
        self.count_menu.grid(row=1, column=1, padx=10, pady=(0, 10), sticky="ew")

        # Prompts Label
        ctk.CTkLabel(self.sidebar_frame, text="Prompts List:", anchor="w").grid(row=7, column=0, padx=20, pady=(10, 0), sticky="ew")
        
        # Prompt Tools (Upload + Checkbox)
        tools_frame = ctk.CTkFrame(self.sidebar_frame, fg_color="transparent")
        tools_frame.grid(row=8, column=0, padx=20, pady=(0, 5), sticky="ew")
        
        ctk.CTkButton(tools_frame, text="Upload Prompts", command=self.upload_prompts, height=24).pack(side="left", fill="x", expand=True, padx=(0, 5))
        self.remove_index_var = ctk.BooleanVar(value=False)
        ctk.CTkCheckBox(tools_frame, text="Remove Index", variable=self.remove_index_var, font=ctk.CTkFont(size=12)).pack(side="right")

        # Prompts Textbox
        self.prompts_textbox = ctk.CTkTextbox(self.sidebar_frame, height=150)
        self.prompts_textbox.grid(row=9, column=0, padx=20, pady=(0, 10), sticky="nsew")

        # Bottom Controls
        bottom_frame = ctk.CTkFrame(self.sidebar_frame, fg_color="transparent")
        bottom_frame.grid(row=10, column=0, padx=20, pady=20, sticky="ew")

        # Output Dir
        self.dir_entry = ctk.CTkEntry(bottom_frame, placeholder_text="Output Folder")
        self.dir_entry.pack(side="top", fill="x", pady=(0, 5))
        self.dir_entry.insert(0, os.path.abspath("output"))
        ctk.CTkButton(bottom_frame, text="Browse", command=self.browse_dir, width=60).pack(side="top", anchor="e", pady=(0, 10))

        # Action Buttons
        self.start_btn = ctk.CTkButton(bottom_frame, text="START NOW", fg_color="green", command=self.start_processing)
        self.start_btn.pack(side="left", fill="x", expand=True, padx=(0, 5))
        
        self.stop_btn = ctk.CTkButton(bottom_frame, text="STOP", fg_color="red", command=self.stop_processing)
        self.stop_btn.pack(side="right", fill="x", expand=True, padx=(5, 0))

    def _setup_main_area(self):
        # Create TabView for Queue and Logs
        self.main_tabview = ctk.CTkTabview(self.main_frame)
        self.main_tabview.pack(fill="both", expand=True, padx=10, pady=10)
        
        self.tab_queue = self.main_tabview.add("Job Queue")
        self.tab_logs = self.main_tabview.add("Logs")
        
        # --- Queue Tab ---
        # Header
        header_frame = ctk.CTkFrame(self.tab_queue, height=40, corner_radius=0)
        header_frame.pack(fill="x", pady=(0, 5))
        
        # Grid layout for header to match columns
        header_frame.grid_columnconfigure(0, weight=3) # Prompt
        header_frame.grid_columnconfigure(1, weight=1) # Image 1
        header_frame.grid_columnconfigure(2, weight=1) # Image 2
        header_frame.grid_columnconfigure(3, weight=1) # Image 3
        header_frame.grid_columnconfigure(4, weight=1) # Image 4
        header_frame.grid_columnconfigure(5, weight=1) # Status
        
        ctk.CTkLabel(header_frame, text="Prompt", anchor="w").grid(row=0, column=0, padx=10, sticky="ew")
        ctk.CTkLabel(header_frame, text="Image 1").grid(row=0, column=1, padx=5)
        ctk.CTkLabel(header_frame, text="Image 2").grid(row=0, column=2, padx=5)
        ctk.CTkLabel(header_frame, text="Image 3").grid(row=0, column=3, padx=5)
        ctk.CTkLabel(header_frame, text="Image 4").grid(row=0, column=4, padx=5)
        ctk.CTkLabel(header_frame, text="Status").grid(row=0, column=5, padx=10)

        # Scrollable Job List
        self.job_list_frame = ctk.CTkScrollableFrame(self.tab_queue)
        self.job_list_frame.pack(fill="both", expand=True)


    def parse_token(self):
        json_str = self.cookie_textbox.get("1.0", "end").strip()
        if not json_str:
            self.update_status("Please paste cookie JSON first.")
            return
        
        token, cookies = parse_cookie_json(json_str)
        if token or cookies:
            if not token: 
                token = "placeholder"
                
            self.job_manager.set_client(token, cookies)
            
            self.token_status.configure(text="Checking Session...", text_color="orange")
            self.update_status("Validating session...")
            
            # Run validation in thread (No delay)
            threading.Thread(target=self._validate_session_thread, daemon=True).start()
        else:
            self.token_status.configure(text="INVALID FORMAT", text_color="red")
            self.update_status("Failed to extract token/cookies from JSON.")

    def _validate_session_thread(self):
        try:
            session_data = self.job_manager.client.validate_session()
            
            if session_data:
                user = session_data.get("user", {})
                email = user.get("email", "Unknown")
                expires = session_data.get("expires", "Unknown")
                
                # Use after to schedule UI update on main thread
                self.after(0, lambda: self._update_session_ui(True, email, expires))
            else:
                self.after(0, lambda: self._update_session_ui(False))
        except Exception as e:
            self.log_error(f"Validation error: {e}")
            self.after(0, lambda: self._update_session_ui(False))

    def _update_session_ui(self, is_valid, email=None, expires=None):
        if is_valid:
            self.cookie_frame.grid_forget() # Hide cookie input
            self.profile_card.grid(row=1, column=0, padx=20, pady=10, sticky="ew") # Show profile
            
            self.email_label.configure(text=email)
            # Format expiry if it's a timestamp
            try:
                import datetime
                if isinstance(expires, (int, float)) or (isinstance(expires, str) and expires.isdigit()):
                     dt = datetime.datetime.fromtimestamp(int(expires) / 1000) # Often ms
                     expires_str = dt.strftime("%Y-%m-%d %H:%M:%S")
                else:
                    expires_str = str(expires)
            except:
                expires_str = str(expires)
                
            self.expiry_label.configure(text=f"Expires: {expires_str}")
            self.update_status(f"Session Valid! User: {email}")
        else:
            self.token_status.configure(text="SESSION INVALID", text_color="red")
            self.update_status("Session validation failed.")

    def browse_dir(self):
        path = filedialog.askdirectory()
        if path:
            self.dir_entry.delete(0, "end")
            self.dir_entry.insert(0, path)
            self.job_manager.set_output_dir(path)

    def upload_prompts(self):
        filename = filedialog.askopenfilename(filetypes=[("Text Files", "*.txt")])
        if filename:
            try:
                with open(filename, "r", encoding="utf-8") as f:
                    content = f.read()
                    self.prompts_textbox.delete("1.0", "end")
        class StdoutRedirector:
            def __init__(self, ui):
                self.ui = ui
            def write(self, text):
                if text.strip():
                    self.ui.log_message(text.strip())
            def flush(self):
                pass
        
        sys.stdout = StdoutRedirector(self)
        sys.stderr = StdoutRedirector(self)

    def on_closing(self):
        self.job_manager.stop_processing()
        self.destroy()

if __name__ == "__main__":
    app = WhiskApp()
    app.protocol("WM_DELETE_WINDOW", app.on_closing)
    app.mainloop()
