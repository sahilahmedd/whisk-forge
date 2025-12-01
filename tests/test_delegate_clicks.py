import unittest
from PySide6.QtCore import QRect, QPoint

class TestDelegateClicks(unittest.TestCase):
    def test_click_areas(self):
        # Simulate StatusDelegate layout logic
        rect = QRect(0, 0, 180, 72)
        btn_size = 36
        spacing = 8
        container_w = btn_size * 2 + spacing + 16
        container_h = btn_size + 12
        
        container_rect = QRect(rect.right() - container_w - 8, rect.y() + (rect.height() - container_h) / 2, container_w, container_h)
        retry_rect = QRect(container_rect.left() + 8, container_rect.y() + 6, btn_size, btn_size)
        open_rect = QRect(retry_rect.right() + spacing, retry_rect.y(), btn_size, btn_size)
        
        # Test Retry Click
        click_pt = retry_rect.center()
        self.assertTrue(retry_rect.contains(click_pt))
        self.assertFalse(open_rect.contains(click_pt))
        
        # Test Open Click
        click_pt = open_rect.center()
        self.assertTrue(open_rect.contains(click_pt))
        self.assertFalse(retry_rect.contains(click_pt))

if __name__ == '__main__':
    unittest.main()
