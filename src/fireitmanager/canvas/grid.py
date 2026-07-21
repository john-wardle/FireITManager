from PySide6.QtWidgets import QGraphicsItem
from PySide6.QtGui import QPen, QPainterPath, QBrush
from PySide6.QtCore import Qt, QRectF

class GridItem(QGraphicsItem):
    """Draws a background grid with minor and major lines."""
    MINOR_GRID_SIZE = 20
    MAJOR_GRID_SIZE = 100
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setZValue(-1)  # Draw below all other items
        
    def boundingRect(self) -> QRectF:
        return QRectF(-50000, -50000, 100000, 100000)
        
    def paint(self, painter: QPainter, option, widget=None):
        """Draw the grid lines."""
        pen = QPen(Qt.GlobalColor.lightGray, 1)
        major_pen = QPen(Qt.GlobalColor.gray, 2)
        
        # Draw minor grid
        for x in range(-50000, 50001, self.MINOR_GRID_SIZE):
            painter.drawLine(x, -50000, x, 50000)
        for y in range(-50000, 50001, self.MINOR_GRID_SIZE):
            painter.drawLine(-50000, y, 50000, y)
        
        # Draw major grid
        for x in range(-50000, 50001, self.MAJOR_GRID_SIZE):
            painter.setPen(major_pen)
            painter.drawLine(x, -50000, x, 50000)
        for y in range(-50000, 50001, self.MAJOR_GRID_SIZE):
            painter.setPen(major_pen)
            painter.drawLine(-50000, y, 50000, y)