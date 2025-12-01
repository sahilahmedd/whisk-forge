from PySide6.QtWidgets import QStyledItemDelegate, QStyleOptionViewItem, QApplication
from PySide6.QtCore import Qt, QRect, QSize, Signal, QPoint
from PySide6.QtGui import QPainter, QColor, QPen, QBrush, QPixmap, QIcon, QFontMetrics, QPainterPath

class PromptDelegate(QStyledItemDelegate):
    editRequested = Signal(str)  # job_id

    def __init__(self, parent=None):
        super().__init__(parent)
        self.pencil_icon = QIcon("assets/icons/pencil.svg") # Placeholder path

    def paint(self, painter, option, index):
        painter.save()
        painter.setRenderHint(QPainter.Antialiasing)

        # Draw background (handled by table usually, but we want a rounded box inside)
        # Table background is white/gray. We draw a rounded box.
        
        rect = option.rect
        box_rect = rect.adjusted(4, 4, -4, -4)
        
        # Selection highlight
        if option.state & QStyleOptionViewItem.State_Selected:
            painter.setPen(QPen(QColor("#2B8CE6"), 2))
            painter.setBrush(QColor("#FFFFFF"))
        else:
            painter.setPen(QPen(QColor("#DFE6EA"), 1))
            painter.setBrush(QColor("#FFFFFF"))

        path = QPainterPath()
        path.addRoundedRect(box_rect, 6, 6)
        painter.drawPath(path)

        # Draw Text
        text = index.data(Qt.DisplayRole)
        # print(f"PromptDelegate painting: {text}")
        text_rect = box_rect.adjusted(8, 8, -24, -8) # Leave room for pencil
        painter.setPen(QColor("#111827"))
        painter.drawText(text_rect, Qt.AlignLeft | Qt.AlignTop | Qt.TextWordWrap, text)

        # Draw Pencil Icon
        pencil_rect = QRect(box_rect.right() - 20, box_rect.bottom() - 20, 16, 16)
        # Just drawing a circle for now if icon missing
        painter.setPen(Qt.NoPen)
        painter.setBrush(QColor("#E5E7EB"))
        painter.drawEllipse(pencil_rect)
        # If we had the icon: self.pencil_icon.paint(painter, pencil_rect)

        painter.restore()

    def editorEvent(self, event, model, option, index):
        # Handle click on pencil
        if event.type() == event.MouseButtonRelease:
            rect = option.rect
            box_rect = rect.adjusted(4, 4, -4, -4)
            pencil_rect = QRect(box_rect.right() - 20, box_rect.bottom() - 20, 16, 16)
            
            if pencil_rect.contains(event.pos()):
                job = index.data(Qt.UserRole)
                if job:
                    self.editRequested.emit(job["job_id"])
                return True
        return super().editorEvent(event, model, option, index)


class ThumbnailDelegate(QStyledItemDelegate):
    deleteRequested = Signal(str) # job_id

    def paint(self, painter, option, index):
        painter.save()
        painter.setRenderHint(QPainter.Antialiasing)
        
        job = index.data(Qt.UserRole)
        thumb_path = job.get("thumbnail")
        
        rect = option.rect
        # Center 220x120
        w, h = 220, 120
        x = rect.x() + (rect.width() - w) / 2
        y = rect.y() + (rect.height() - h) / 2
        img_rect = QRect(int(x), int(y), w, h)

        if thumb_path:
            pixmap = QPixmap(thumb_path)
            if not pixmap.isNull():
                painter.drawPixmap(img_rect, pixmap, pixmap.rect())
            else:
                self._draw_placeholder(painter, img_rect)
        else:
            self._draw_placeholder(painter, img_rect)

        # Hover overlay
        if option.state & QStyleOptionViewItem.State_MouseOver:
            painter.setBrush(QColor(0, 0, 0, 50))
            painter.drawRect(img_rect)
            
            # Trash icon
            trash_rect = QRect(img_rect.right() - 24, img_rect.bottom() - 24, 20, 20)
            painter.setBrush(QColor("#EF4444"))
            painter.setPen(Qt.NoPen)
            painter.drawEllipse(trash_rect)
            # Draw 'X' or trash glyph
            painter.setPen(Qt.white)
            painter.drawLine(trash_rect.center() + QPoint(-3, -3), trash_rect.center() + QPoint(3, 3))
            painter.drawLine(trash_rect.center() + QPoint(-3, 3), trash_rect.center() + QPoint(3, -3))

        painter.restore()

    def _draw_placeholder(self, painter, rect):
        painter.setBrush(QColor("#F3F4F6"))
        painter.setPen(QColor("#E5E7EB"))
        painter.drawRect(rect)
        painter.setPen(QColor("#9CA3AF"))
        painter.drawText(rect, Qt.AlignCenter, "No Image")

    def editorEvent(self, event, model, option, index):
        if event.type() == event.MouseButtonRelease:
            rect = option.rect
            w, h = 220, 120
            x = rect.x() + (rect.width() - w) / 2
            y = rect.y() + (rect.height() - h) / 2
            img_rect = QRect(int(x), int(y), w, h)
            trash_rect = QRect(img_rect.right() - 24, img_rect.bottom() - 24, 20, 20)
            
            if trash_rect.contains(event.pos()):
                job = index.data(Qt.UserRole)
                if job:
                    self.deleteRequested.emit(job["job_id"])
                return True
        return super().editorEvent(event, model, option, index)


class StatusDelegate(QStyledItemDelegate):
    retryRequested = Signal(str)
    openRequested = Signal(str)

    def paint(self, painter, option, index):
        painter.save()
        painter.setRenderHint(QPainter.Antialiasing)
        
        job = index.data(Qt.UserRole)
        status = job.get("status", "QUEUED")
        
        rect = option.rect
        # Layout: [Badge] [Container [Retry] [Open]]
        
        # Container for buttons
        btn_size = 36
        spacing = 8
        container_w = btn_size * 2 + spacing + 16 # padding
        container_h = btn_size + 12
        
        container_rect = QRect(rect.right() - container_w - 8, rect.y() + (rect.height() - container_h) / 2, container_w, container_h)
        
        # Draw Badge (Left of container)
        badge_rect = QRect(rect.x(), rect.y(), container_rect.left() - rect.x() - 8, rect.height())
        
        # Badge Text
        status_color = "#16A34A" if status == "COMPLETED" else "#6B7280"
        if status == "FAILED": status_color = "#EF4444"
        if status == "RUNNING": status_color = "#2B8CE6"
        
        painter.setPen(QColor(status_color))
        font = painter.font()
        font.setWeight(600) # SemiBold
        painter.setFont(font)
        painter.drawText(badge_rect, Qt.AlignRight | Qt.AlignVCenter, status.title())

        # Draw Button Container
        painter.setPen(QColor("#DFE6EA"))
        painter.setBrush(QColor("#FFFFFF"))
        path = QPainterPath()
        path.addRoundedRect(container_rect, 6, 6)
        painter.drawPath(path)
        
        # Buttons
        retry_rect = QRect(container_rect.left() + 8, container_rect.y() + 6, btn_size, btn_size)
        open_rect = QRect(retry_rect.right() + spacing, retry_rect.y(), btn_size, btn_size)
        
        # Retry Button (Orange)
        painter.setPen(Qt.NoPen)
        painter.setBrush(QColor("#F59E0B"))
        painter.drawRoundedRect(retry_rect, 6, 6)
        # Icon placeholder (Loop)
        painter.setPen(Qt.white)
        painter.drawText(retry_rect, Qt.AlignCenter, "R")
        
        # Open Button (Blue)
        painter.setBrush(QColor("#2B8CE6"))
        painter.drawRoundedRect(open_rect, 6, 6)
        # Icon placeholder (Folder)
        painter.drawText(open_rect, Qt.AlignCenter, "O")

        painter.restore()

    def editorEvent(self, event, model, option, index):
        if event.type() == event.MouseButtonRelease:
            rect = option.rect
            btn_size = 36
            spacing = 8
            container_w = btn_size * 2 + spacing + 16
            container_h = btn_size + 12
            container_rect = QRect(rect.right() - container_w - 8, rect.y() + (rect.height() - container_h) / 2, container_w, container_h)
            
            retry_rect = QRect(container_rect.left() + 8, container_rect.y() + 6, btn_size, btn_size)
            open_rect = QRect(retry_rect.right() + spacing, retry_rect.y(), btn_size, btn_size)
            
            job = index.data(Qt.UserRole)
            if not job: return False

            if retry_rect.contains(event.pos()):
                self.retryRequested.emit(job["job_id"])
                return True
            elif open_rect.contains(event.pos()):
                self.openRequested.emit(job["job_id"])
                return True
                
        return super().editorEvent(event, model, option, index)
