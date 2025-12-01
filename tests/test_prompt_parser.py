import unittest
import re

class TestPromptParser(unittest.TestCase):
    def clean_prompt(self, text):
        return re.sub(r'^\s*\d+[\).\-\s]*', '', text).strip()

    def test_clean_prompt(self):
        self.assertEqual(self.clean_prompt("1. A red cat"), "A red cat")
        self.assertEqual(self.clean_prompt("001) A blue dog"), "A blue dog")
        self.assertEqual(self.clean_prompt(" - A green bird"), "- A green bird") # Regex only targets digits
        self.assertEqual(self.clean_prompt("10.   A yellow fish"), "A yellow fish")
        self.assertEqual(self.clean_prompt("Just text"), "Just text")

if __name__ == '__main__':
    unittest.main()
