import logging
import os
from pathlib import Path

def setup_logger():
    log_dir = Path(os.environ.get("LOCALAPPDATA")) / "WhiskForge" / "logs"
    log_dir.mkdir(parents=True, exist_ok=True)
    log_file = log_dir / "app.log"
    
    logging.basicConfig(
        level=logging.DEBUG,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_file),
            logging.StreamHandler()
        ]
    )
    return logging.getLogger("WhiskForge")

logger = setup_logger()
