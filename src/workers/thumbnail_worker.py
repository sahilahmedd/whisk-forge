from PySide6.QtCore import QRunnable, Signal, QObject, Slot
from PySide6.QtGui import QImage, QPixmap
import os

class ThumbnailWorkerSignals(QObject):
    thumbnail_ready = Signal(str, str) # job_id, path
    error = Signal(str, str)

class ThumbnailWorker(QRunnable):
    def __init__(self, job_id, image_path, cache_dir):
        super().__init__()
        self.job_id = job_id
        self.image_path = image_path
        self.cache_dir = cache_dir
        self.signals = ThumbnailWorkerSignals()

    def run(self):
        try:
            if not os.path.exists(self.image_path):
                return

            # Ensure cache dir exists
            if not os.path.exists(self.cache_dir):
                os.makedirs(self.cache_dir)

            # Generate cache filename
            # We use modification time or size to invalidate if needed, but simple name is fine for now
            base_name = os.path.basename(self.image_path)
            cache_name = f"thumb_{base_name}.webp"
            cache_path = os.path.join(self.cache_dir, cache_name)

            if os.path.exists(cache_path):
                self.signals.thumbnail_ready.emit(self.job_id, cache_path)
                return

            # Load and scale
            img = QImage(self.image_path)
            if img.isNull():
                raise Exception("Failed to load image")

            # Scale to 220x120 (keeping aspect ratio or crop? Spec says "Center a thumbnail image (size ~200x120)")
            # We'll scale to cover and crop or just fit. Let's fit for now to avoid cropping important details.
            # Or better, scale to height 120, then crop width if too wide, or pad.
            # Let's just scale to fixed height 120 and let width be whatever, but delegate draws it centered.
            # Actually spec says "Center a thumbnail image (size ~200x120) inside cell".
            
            scaled = img.scaled(220, 120, aspectMode=1) # KeepAspect
            scaled.save(cache_path, "WEBP")
            
            self.signals.thumbnail_ready.emit(self.job_id, cache_path)

        except Exception as e:
            self.signals.error.emit(self.job_id, str(e))
