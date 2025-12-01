from PySide6.QtCore import QObject, Signal, QThread
import re
import csv
import os

class PromptParserWorker(QObject):
    batchReady = Signal(list)      # list of prompt strings
    finished = Signal(int)         # total count
    error = Signal(str)

    def __init__(self, text_or_path, mode, remove_index=False, batch_size=50):
        super().__init__()
        self.text_or_path = text_or_path
        self.mode = mode          # "textarea", "file"
        self.remove_index = remove_index
        self.batch_size = batch_size
        self.alive = True

    def run(self):
        try:
            total = 0
            if self.mode == "textarea":
                lines = self.text_or_path.split("\n")
                total = self.process_lines(lines)

            elif self.mode == "file":
                total = self.process_file(self.text_or_path)

            self.finished.emit(total)
        except Exception as e:
            self.error.emit(str(e))

    def process_lines(self, lines):
        batch = []
        total = 0

        for line in lines:
            if not self.alive:
                break

            prompt = line.strip()
            if not prompt:
                continue

            if self.remove_index:
                # Regex to remove leading numbers/bullets: "1. ", "001)", "- "
                prompt = re.sub(r'^\s*\d+[\).\-\s]*', '', prompt).strip()
                # Also handle just "- " bullet
                if prompt.startswith("- "):
                    prompt = prompt[2:].strip()

            if prompt:
                batch.append(prompt)
                total += 1

            if len(batch) >= self.batch_size:
                self.batchReady.emit(batch)
                batch = []
                QThread.msleep(10) # Yield to main thread

        if batch:
            self.batchReady.emit(batch)
            
        return total

    def process_file(self, path):
        total = 0
        batch = []
        
        if path.lower().endswith('.csv'):
            with open(path, 'r', encoding='utf-8') as f:
                reader = csv.reader(f)
                for row in reader:
                    if not self.alive: break
                    if row:
                        prompt = row[0].strip()
                        if self.remove_index:
                             prompt = re.sub(r'^\s*\d+[\).\-\s]*', '', prompt).strip()
                             if prompt.startswith("- "): prompt = prompt[2:].strip()
                        
                        if prompt:
                            batch.append(prompt)
                            total += 1
                            
                        if len(batch) >= self.batch_size:
                            self.batchReady.emit(batch)
                            batch = []
                            QThread.msleep(10)
        else:
            with open(path, 'r', encoding='utf-8') as f:
                for line in f:
                    if not self.alive: break
                    prompt = line.strip()
                    if not prompt: continue
                    
                    if self.remove_index:
                         prompt = re.sub(r'^\s*\d+[\).\-\s]*', '', prompt).strip()
                         if prompt.startswith("- "): prompt = prompt[2:].strip()
                    
                    if prompt:
                        batch.append(prompt)
                        total += 1
                        
                    if len(batch) >= self.batch_size:
                        self.batchReady.emit(batch)
                        batch = []
                        QThread.msleep(10)

        if batch:
            self.batchReady.emit(batch)
            
        return total

    def stop(self):
        self.alive = False
