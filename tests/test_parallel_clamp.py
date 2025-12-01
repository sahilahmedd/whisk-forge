import unittest

class TestParallelClamp(unittest.TestCase):
    def clamp_threads(self, n):
        return max(1, min(2, int(n)))

    def test_clamp(self):
        self.assertEqual(self.clamp_threads(1), 1)
        self.assertEqual(self.clamp_threads(2), 2)
        self.assertEqual(self.clamp_threads(3), 2)
        self.assertEqual(self.clamp_threads(0), 1)
        self.assertEqual(self.clamp_threads(100), 2)
        self.assertEqual(self.clamp_threads(-5), 1)

if __name__ == '__main__':
    unittest.main()
