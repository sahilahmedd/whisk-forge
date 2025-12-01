from PySide6.QtCore import QRunnable, Signal, QObject
import time
import os
import base64
from ..models.job import Job
from ..services.whisk_api import WhiskAPI
from ..utils.logger import logger

class JobWorkerSignals(QObject):
    started = Signal(str)
    finished = Signal(str, list)
    failed = Signal(str, str)
    progress = Signal(str, str)

class JobWorker(QRunnable):
    def __init__(self, job: Job, api: WhiskAPI, output_dir: str):
        super().__init__()
        self.job = job
        self.api = api
        self.output_dir = output_dir
        self.signals = JobWorkerSignals()
        self.is_cancelled = False
        logger.debug(f"JobWorker initialized for job {job.id}")

    def run(self):
        if self.is_cancelled: return

        self.signals.started.emit(self.job.id)
        
        try:
            generated_files = []
            for i in range(self.job.count):
                if self.is_cancelled: break
                
                self.signals.progress.emit(self.job.id, f"Generating {i+1}/{self.job.count}")
                
                # Call API
                # Note: This blocks the thread, which is fine for QRunnable
                logger.debug(f"JobWorker calling API for {self.job.prompt}")
                response = self.api.generate_image(self.job.prompt, aspect_ratio=self.job.aspect_ratio)
                logger.debug(f"JobWorker response keys: {list(response.keys())}")
                
                if "imagePanels" in response:
                    for panel in response["imagePanels"]:
                        for img in panel.get("generatedImages", []):
                            encoded = img.get("encodedImage")
                            if encoded:
                                # Naming logic
                                if self.job.count == 1:
                                    filename = f"image_{self.job.prompt_index}.jpg"
                                else:
                                    filename = f"image_{self.job.prompt_index}_{i+1}.jpg"
                                
                                filepath = os.path.join(self.output_dir, filename)
                                self._save_image(encoded, filepath)
                                generated_files.append(filepath)
                                logger.info(f"Saved image to {filepath}")
                else:
                    logger.warning(f"No imagePanels in response: {response}")
            
            if generated_files:
                self.signals.finished.emit(self.job.id, generated_files)
                logger.info(f"Job {self.job.id} finished with {len(generated_files)} images")
            else:
                if not self.is_cancelled:
                    logger.error("No images returned")
                    raise Exception("No images returned")

        except Exception as e:
            logger.error(f"Job failed: {e}", exc_info=True)
            self.signals.failed.emit(self.job.id, str(e))

    def _save_image(self, encoded: str, path: str):
        if ',' in encoded:
            encoded = encoded.split(',', 1)[1]
        data = base64.b64decode(encoded)
        
        # Ensure directory exists
        os.makedirs(os.path.dirname(path), exist_ok=True)
        
        with open(path, "wb") as f:
            f.write(data)
            
        # Verify
        if not os.path.exists(path):
            raise Exception(f"File not created: {path}")
        if os.path.getsize(path) == 0:
            raise Exception(f"File is empty: {path}")
            
        logger.debug(f"Wrote {len(data)} bytes to {path}")

    def cancel(self):
        self.is_cancelled = True
