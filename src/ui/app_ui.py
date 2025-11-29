import customtkinter as ctk
import tkinter as tk
from tkinter import filedialog
import threading
import os
import sys
import datetime
from PIL import Image, ImageTk
from ..core.job_manager import JobManager
from ..core.job_manager import JobManager
from ..core.utils import parse_cookie_json, open_file

ctk.set_appearance_mode("System")
ctk.set_default_color_theme("blue")

class StdoutRedirector:
    def __init__(self, ui_callback):
        self.ui_callback = ui_callback

    def write(self, text):
        if text.strip():
            self.ui_callback(text.strip())

    def flush(self):
        pass

class WhiskApp(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("WhiskForge - AI Image Generator")
        self.geometry("1200x800")
        
        # Set window icon
        try:
            icon_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "assets", "logo.png")
            if os.path.exists(icon_path):
                img = tk.PhotoImage(file=icon_path)
                self.iconphoto(False, img)
        except Exception as e:
            print(f"Failed to set icon: {e}")

        self.job_manager = JobManager()
        self.job_rows = {} # Map job_id -> dict of UI widgets
        self.total_jobs = 0
        self.completed_jobs = 0
        
        self._setup_callbacks()
        
        # Grid Layout: 2 Columns (Sidebar, Main)
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        # --- Sidebar ---
        self.sidebar_frame = ctk.CTkFrame(self, width=300, corner_radius=0)
        self.sidebar_frame.grid(row=0, column=0, sticky="nsew")
        self.sidebar_frame.grid_rowconfigure(9, weight=1) # Push bottom items down

        self._setup_sidebar()

        # --- Main Area ---
        self.main_frame = ctk.CTkFrame(self, corner_radius=0, fg_color="transparent")
        self.main_frame.grid(row=0, column=1, sticky="nsew")
        self.main_frame.grid_rowconfigure(0, weight=1)
        self.main_frame.grid_columnconfigure(0, weight=1)

        self._setup_main_area()
        
        self.redirect_logging()

    def _setup_callbacks(self):
        self.job_manager.on_status_change = self.update_status
        self.job_manager.on_job_error = self.log_error
        self.job_manager.on_job_complete = self.handle_job_complete

    def redirect_logging(self):
        self.redirector = StdoutRedirector(self.log_message)
        sys.stdout = self.redirector
        sys.stderr = self.redirector

    def log_message(self, message):
        # Schedule UI update on main thread
        self.after(0, lambda: self._append_log(message))

    def _append_log(self, message):
        timestamp = datetime.datetime.now().strftime("%H:%M:%S")
        self.logs_textbox.configure(state="normal")
        self.logs_textbox.insert("end", f"[{timestamp}] {message}\n")
        self.logs_textbox.see("end")
        self.logs_textbox.configure(state="disabled")

    def log_error(self, message):
        self.log_message(f"ERROR: {message}")

    def update_status(self, message):
        self.log_message(f"STATUS: {message}")

    def _setup_sidebar(self):
        # Title
        ctk.CTkLabel(self.sidebar_frame, text="WhiskForge", font=ctk.CTkFont(size=20, weight="bold")).grid(row=0, column=0, padx=20, pady=(20, 10))

        # Cookie Section
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
        
        # Prompt Tools
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
        
        self.pause_btn = ctk.CTkButton(bottom_frame, text="PAUSE", fg_color="orange", command=self.toggle_pause, state="disabled")
        self.pause_btn.pack(side="left", fill="x", expand=True, padx=(5, 5))
        
        self.stop_btn = ctk.CTkButton(bottom_frame, text="STOP", fg_color="red", command=self.stop_processing, state="disabled")
        self.stop_btn.pack(side="right", fill="x", expand=True, padx=(5, 0))



    def _setup_main_area(self):
        self.main_tabview = ctk.CTkTabview(self.main_frame)
        self.main_tabview.pack(fill="both", expand=True, padx=10, pady=10)
        
        self.tab_queue = self.main_tabview.add("Job Queue")
        self.tab_logs = self.main_tabview.add("Logs")
        
        # --- Queue Tab ---
        # Header
        header_frame = ctk.CTkFrame(self.tab_queue, height=40, corner_radius=0)
        header_frame.pack(fill="x", pady=(0, 5))
        
        header_frame.grid_columnconfigure(0, weight=3) # Prompt
        header_frame.grid_columnconfigure(1, weight=1) # Status
        header_frame.grid_columnconfigure(2, weight=2) # Images
        
        ctk.CTkLabel(header_frame, text="Prompt", anchor="w").grid(row=0, column=0, padx=10, sticky="ew")
        ctk.CTkLabel(header_frame, text="Status").grid(row=0, column=1, padx=10)
        ctk.CTkLabel(header_frame, text="Generated Images").grid(row=0, column=2, padx=10)

        # Scrollable Job List
        self.job_list_frame = ctk.CTkScrollableFrame(self.tab_queue)
        self.job_list_frame.pack(fill="both", expand=True)
        self.job_list_frame.grid_columnconfigure(0, weight=3)
        self.job_list_frame.grid_columnconfigure(1, weight=1)
        self.job_list_frame.grid_columnconfigure(2, weight=2)

        # --- Logs Tab ---
        self.logs_textbox = ctk.CTkTextbox(self.tab_logs, state="disabled", font=("Consolas", 12))
        self.logs_textbox.pack(fill="both", expand=True)

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
                self.after(0, lambda: self._update_session_ui(True, email, expires))
            else:
                self.after(0, lambda: self._update_session_ui(False))
        except Exception as e:
            self.log_error(f"Validation error: {e}")
            self.after(0, lambda: self._update_session_ui(False))

    def _update_session_ui(self, is_valid, email=None, expires=None):
        if is_valid:
            self.cookie_frame.grid_forget()
            self.profile_card.grid(row=1, column=0, padx=20, pady=10, sticky="ew")
            
            self.email_label.configure(text=email)
            try:
                import datetime
                if isinstance(expires, (int, float)) or (isinstance(expires, str) and expires.isdigit()):
                     dt = datetime.datetime.fromtimestamp(int(expires) / 1000)
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
                    self.prompts_textbox.insert("1.0", content)
                self.update_status(f"Loaded prompts from {os.path.basename(filename)}")
            except Exception as e:
                self.log_error(f"Failed to load prompts: {e}")

    def start_processing(self):
        prompts_text = self.prompts_textbox.get("1.0", "end").strip()
        if not prompts_text:
            self.update_status("No prompts to process.")
            return

        prompts = [p.strip() for p in prompts_text.split('\n') if p.strip()]
        if not prompts:
            return

        # Config
        aspect_ratio_map = {
            "Horizontal 16:9": "IMAGE_ASPECT_RATIO_LANDSCAPE",
            "Vertical 9:16": "IMAGE_ASPECT_RATIO_PORTRAIT",
            "Square 1:1": "IMAGE_ASPECT_RATIO_SQUARE"
        }
        aspect_ratio = aspect_ratio_map.get(self.aspect_ratio_var.get(), "IMAGE_ASPECT_RATIO_LANDSCAPE")
        count = int(self.count_var.get())
        
        # Clear previous jobs from UI (optional, or append)
        # For now, let's just append.
        
        self.start_btn.configure(state="disabled")
        self.stop_btn.configure(state="normal")
        self.pause_btn.configure(state="normal", text="PAUSE", fg_color="orange")
        
        self.total_jobs = len(prompts)
        self.completed_jobs = 0
        
        # Add jobs
        for idx, prompt in enumerate(prompts, 1):
            if self.remove_index_var.get():
                # Simple logic to remove leading numbers like "1. ", "1 - "
                import re
                prompt = re.sub(r'^\d+[\.\-\)]\s*', '', prompt)
                
            job_id = self.job_manager.add_job(prompt, aspect_ratio, count, prompt_index=idx)
            self._add_job_to_ui(job_id, prompt)

        self.job_manager.start_processing()

    def stop_processing(self):
        self.job_manager.stop_processing()
        self.start_btn.configure(state="normal")
        self.stop_btn.configure(state="disabled")
        self.pause_btn.configure(state="disabled", text="PAUSE", fg_color="orange")

    def toggle_pause(self):
        if self.pause_btn.cget("text") == "PAUSE":
            self.job_manager.pause_processing()
            self.pause_btn.configure(text="RESUME", fg_color="yellow", text_color="black")
        else:
            self.job_manager.resume_processing()
            self.pause_btn.configure(text="PAUSE", fg_color="orange", text_color="white")

    def _add_job_to_ui(self, job_id, prompt):
        row = len(self.job_rows)
        
        # Prompt Label with wrapping
        # Calculate approximate wrap length based on column weight/width
        # A safe bet is around 400-500px for the prompt column
        lbl_prompt = ctk.CTkLabel(self.job_list_frame, text=prompt, anchor="w", justify="left", wraplength=400)
        lbl_prompt.grid(row=row, column=0, padx=10, pady=5, sticky="ew")
        
        # Status Label
        lbl_status = ctk.CTkLabel(self.job_list_frame, text="PENDING", text_color="orange")
        lbl_status.grid(row=row, column=1, padx=10, pady=5)
        
        # Images Container
        frame_images = ctk.CTkFrame(self.job_list_frame, fg_color="transparent")
        frame_images.grid(row=row, column=2, padx=10, pady=5, sticky="ew")
        
        self.job_rows[job_id] = {
            "status_label": lbl_status,
            "images_frame": frame_images
        }

    def handle_job_complete(self, data):
        # data = {"id": job_id, "prompt": prompt, "images": [paths], "status": status, "error": error}
        self.after(0, lambda: self._update_job_row(data))

    def _update_job_row(self, data):
        job_id = data.get("id")
        status = data.get("status")
        images = data.get("images", [])
        
        if job_id in self.job_rows:
            ui_elements = self.job_rows[job_id]
            lbl_status = ui_elements["status_label"]
            frame_images = ui_elements["images_frame"]
            
            lbl_status.configure(text=status)
            if status == "COMPLETED":
                lbl_status.configure(text_color="green")
                self._check_queue_completion()
            elif status == "FAILED":
                lbl_status.configure(text_color="red")
                self._check_queue_completion()
            else:
                lbl_status.configure(text_color="blue")
                
            # Update images (clear and redraw)
            for widget in frame_images.winfo_children():
                widget.destroy()
                
            for img_path in images:
                if os.path.exists(img_path):
                    try:
                        # Create thumbnail
                        pil_img = Image.open(img_path)
                        # CTkImage requires size argument for display size, and we can pass the PIL image
                        # We'll make it a square thumbnail
                        ctk_img = ctk.CTkImage(light_image=pil_img, dark_image=pil_img, size=(100, 100))
                        
                        btn = ctk.CTkButton(frame_images, text="", image=ctk_img, width=100, height=100,
                                            fg_color="transparent", hover_color="gray",
                                            command=lambda p=img_path: open_file(p))
                        btn.pack(side="left", padx=5, pady=2)
                    except Exception as e:
                        print(f"Error loading thumbnail: {e}")
                        # Fallback to text button
                        btn = ctk.CTkButton(frame_images, text="Open", width=50, height=20, 
                                            command=lambda p=img_path: open_file(p))
                        btn.pack(side="left", padx=2)

    def _check_queue_completion(self):
        self.completed_jobs += 1
        if self.completed_jobs >= self.total_jobs:
            self.after(500, self.on_queue_finished)

    def on_queue_finished(self):
        self.stop_processing()
        tk.messagebox.showinfo("WhiskForge", "Generation Finished!")

    def on_closing(self):
        self.job_manager.stop_processing()
        self.destroy()

if __name__ == "__main__":
    app = WhiskApp()
    app.protocol("WM_DELETE_WINDOW", app.on_closing)
    app.mainloop()
