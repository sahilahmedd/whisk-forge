import unittest
from src.services.prompt_parser import PromptParserWorker
from PySide6.QtTest import QSignalSpy

class TestPromptWorker(unittest.TestCase):
    def test_clean_prompt(self):
        worker = PromptParserWorker("", "textarea", remove_index=True)
        # We can test the private logic via process_lines
        lines = ["1. Apple", "002) Banana", "- Cherry", "Just Date"]
        
        # Mock signal emission by capturing batches
        batches = []
        def on_batch(b):
            batches.extend(b)
            
        worker.batchReady.connect(on_batch)
        worker.process_lines(lines)
        
        self.assertEqual(batches, ["Apple", "Banana", "Cherry", "Date"])

    def test_batching(self):
        worker = PromptParserWorker("", "textarea", batch_size=2)
        lines = ["A", "B", "C", "D", "E"]
        
        batches = []
        def on_batch(b):
            batches.append(b)
            
        worker.batchReady.connect(on_batch)
        worker.process_lines(lines)
        
        self.assertEqual(len(batches), 3) # [A,B], [C,D], [E]
        self.assertEqual(batches[0], ["A", "B"])
        self.assertEqual(batches[2], ["E"])

if __name__ == '__main__':
    # QObject needs a QCoreApplication to work properly with signals usually, 
    # but for direct method calls it might be okay. 
    # However, since we use signals, we might need a minimal app instance if we were using QSignalSpy properly.
    # Here we just connected a lambda, which works for direct calls in the same thread.
    unittest.main()
