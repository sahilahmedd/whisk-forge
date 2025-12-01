import threading
import queue
import sqlite3
import time
import os
import json
from typing import Callable, Optional, Dict, Any
from .api_client import WhiskClient
from .utils import save_image, save_metadata, sanitize_filename

class JobManager:
    def __init__(self, db_path: str = "jobs.db"):
        self.db_path = db_path
        self.queue = queue.Queue()
        self.running = False
        self.pause_event = threading.Event()
        self.pause_event.set() # Start unpaused
        self.worker_threads: list[threading.Thread] = []
        self.client: Optional[WhiskClient] = None
        self.output_dir = "output"
        
        # Callbacks
        self.on_progress: Optional[Callable[[str], None]] = None
        self.on_job_complete: Optional[Callable[[Dict], None]] = None
        self.on_job_error: Optional[Callable[[str], None]] = None
        self.on_status_change: Optional[Callable[[str], None]] = None

        self._init_db()

    def _init_db(self):
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        # Add new columns if they don't exist (simple migration for dev)
        try:
            c.execute("ALTER TABLE jobs ADD COLUMN aspect_ratio TEXT")
        except sqlite3.OperationalError:
            pass
        try:
            c.execute("ALTER TABLE jobs ADD COLUMN count INTEGER DEFAULT 1")
        except sqlite3.OperationalError:
            pass
        try:
            c.execute("ALTER TABLE jobs ADD COLUMN prompt_index INTEGER DEFAULT 0")
        except sqlite3.OperationalError:
            pass
            
        c.execute('''CREATE TABLE IF NOT EXISTS jobs
                      (id INTEGER PRIMARY KEY AUTOINCREMENT,
                       prompt TEXT,
                       status TEXT,
                       result_path TEXT,
                       aspect_ratio TEXT,
                       count INTEGER DEFAULT 1,
                       prompt_index INTEGER DEFAULT 0,
                       created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)''')
        conn.commit()
        conn.close()

    def set_client(self, token: str, cookies: Optional[Dict[str, str]] = None):
        self.client = WhiskClient(token, cookies)

    def set_output_dir(self, path: str):
        self.output_dir = path
        if not os.path.exists(path):
            os.makedirs(path)

    def add_job(self, prompt: str, aspect_ratio: str = "IMAGE_ASPECT_RATIO_LANDSCAPE", count: int = 1, prompt_index: int = 0):
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        
        # Add single entry with count
        c.execute("INSERT INTO jobs (prompt, status, aspect_ratio, count, prompt_index) VALUES (?, ?, ?, ?, ?)", (prompt, "PENDING", aspect_ratio, count, prompt_index))
        job_id = c.lastrowid
        self.queue.put({"id": job_id, "prompt": prompt, "aspect_ratio": aspect_ratio, "count": count, "prompt_index": prompt_index})
            
        conn.commit()
        conn.close()
        
        if self.on_status_change:
            self.on_status_change(f"Added job for: {prompt[:30]}... (Count: {count})")
        return job_id

    def retry_job(self, job_id):
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        
        # Get job details
        c.execute("SELECT prompt, aspect_ratio, count, prompt_index FROM jobs WHERE id=?", (job_id,))
        row = c.fetchone()
        if row:
            prompt, aspect_ratio, count, prompt_index = row
            if not count: count = 1
            if prompt_index is None: prompt_index = 0
            
            # Reset status
            c.execute("UPDATE jobs SET status='PENDING', result_path=NULL WHERE id=?", (job_id,))
            conn.commit()
            
            self.queue.put({"id": job_id, "prompt": prompt, "aspect_ratio": aspect_ratio, "count": count, "prompt_index": prompt_index})
            
            if self.on_status_change:
                self.on_status_change(f"Retrying job {job_id}...")
        
        conn.close()

    def start_processing(self, max_workers: int = 1):
        if self.running:
            return
        
        if not self.client:
            if self.on_job_error:
                self.on_job_error("Client not initialized. Please set token.")
            return

        self.running = True
        self.pause_event.set() # Ensure we start unpaused
        self.worker_threads = []
        
        for _ in range(max_workers):
            t = threading.Thread(target=self._process_queue, daemon=True)
            t.start()
            self.worker_threads.append(t)
            
        if self.on_status_change:
            self.on_status_change(f"Processing started with {max_workers} workers.")

    def stop_processing(self):
        self.running = False
        self.pause_event.set() # Unblock any waiting threads so they can exit
        if self.on_status_change:
            self.on_status_change("Processing stopping...")
            
    def pause_processing(self):
        self.pause_event.clear()
        if self.on_status_change:
            self.on_status_change("Processing paused.")

    def resume_processing(self):
        self.pause_event.set()
        if self.on_status_change:
            self.on_status_change("Processing resumed.")

    def _process_queue(self):
        while self.running:
            self.pause_event.wait() # Wait if paused
            if not self.running: break

            try:
                job = self.queue.get(timeout=1)
            except queue.Empty:
                continue

            job_id = job["id"]
            prompt = job["prompt"]
            aspect_ratio = job.get("aspect_ratio", "IMAGE_ASPECT_RATIO_LANDSCAPE")
            count = job.get("count", 1)
            prompt_index = job.get("prompt_index", 0)

            if self.on_status_change:
                self.on_status_change(f"Processing: {prompt[:30]}...")

            try:
                # Update DB to RUNNING
                self._update_job_status(job_id, "RUNNING")
                
                all_images = []

                for i in range(count):
                    self.pause_event.wait() # Wait if paused between images
                    if not self.running: break
                    
                    status_msg = f"Creating {i+1}/{count}"
                    if self.on_job_complete: # Use this to update status in UI row
                         self.on_job_complete({"id": job_id, "prompt": prompt, "images": all_images, "status": status_msg})

                    # Call API
                    if not self.client:
                        raise Exception("Client not initialized")
                    
                    response = self.client.generate_image(prompt, aspect_ratio=aspect_ratio)
                    
                    # Process Response
                    if "imagePanels" in response:
                        for panel in response["imagePanels"]:
                            for img in panel.get("generatedImages", []):
                                encoded = img.get("encodedImage")
                                if encoded:
                                    # Strict Sequential Naming
                                    if count == 1:
                                        filename = f"image_{prompt_index}.jpg"
                                    else:
                                        # 1-based variation index
                                        filename = f"image_{prompt_index}_{i+1}.jpg"
                                    
                                    file_path = os.path.join(self.output_dir, filename)
                                    
                                    if save_image(encoded, file_path):
                                        all_images.append(file_path)
                                        # Update UI with new image immediately
                                        if self.on_job_complete:
                                             self.on_job_complete({"id": job_id, "prompt": prompt, "images": all_images, "status": status_msg})

                if all_images:
                    self._update_job_status(job_id, "COMPLETED", result_path=json.dumps(all_images))
                    if self.on_job_complete:
                        self.on_job_complete({"id": job_id, "prompt": prompt, "images": all_images, "status": "COMPLETED"})
                    if self.on_status_change:
                        self.on_status_change(f"Completed: {prompt[:30]}")
                else:
                    self._update_job_status(job_id, "FAILED", result_path="No images returned")
                    if self.on_job_error:
                        self.on_job_error(f"No images returned for: {prompt}")
                    if self.on_job_complete:
                         self.on_job_complete({"id": job_id, "prompt": prompt, "images": [], "status": "FAILED", "error": "No images returned"})

            except Exception as e:
                print(f"Job failed: {e}")
                self._update_job_status(job_id, "FAILED", result_path=str(e))
                if self.on_job_error:
                    self.on_job_error(f"Error processing {prompt}: {str(e)}")
                if self.on_job_complete:
                     self.on_job_complete({"id": job_id, "prompt": prompt, "images": [], "status": "FAILED", "error": str(e)})
            finally:
                self.queue.task_done()

    def _update_job_status(self, job_id, status, result_path=None):
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        if result_path:
            c.execute("UPDATE jobs SET status = ?, result_path = ? WHERE id = ?", (status, result_path, job_id))
        else:
            c.execute("UPDATE jobs SET status = ? WHERE id = ?", (status, job_id))
        conn.commit()
        conn.close()

    def clear_queue(self):
        """Clears the internal queue and resets running state."""
        with self.queue.mutex:
            self.queue.queue.clear()
        self.running = False
        self.pause_event.set()
        if self.on_status_change:
            self.on_status_change("Queue cleared.")
