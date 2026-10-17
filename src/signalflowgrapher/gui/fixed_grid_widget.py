import math
from PySide6.QtCore import QPoint, Qt
from PySide6.QtWidgets import QWidget, QApplication
from PySide6.QtGui import QPaintEvent, QPainter, QPen


class FixedGridWidget(QWidget):
    def __init__(self, size, offset_source, view, *args, ** kwargs):
        super().__init__(*args, **kwargs)
        self.__grid_size = size
        self.__pen_width = 1
        self.__offset_source = offset_source
        self.__view = view

        # Disable the widgets to ignore all events
        # Widget should not become mousegrabber
        self.setDisabled(True)

    @property
    def offset(self) -> QPoint:
        """
        Position of the grid lines in world coordinates: the pan of the
        graph modulo the grid size. Read from the offset source (the
        model) at every paint.
        """
        x, y = self.__offset_source()
        return QPoint(int(x % self.__grid_size), int(y % self.__grid_size))

    def paintEvent(self, event: QPaintEvent):
        # Init painter
        pen = QPen()
        pen.setWidth(self.__pen_width)
        scheme = QApplication.instance().styleHints().colorScheme()
        if scheme == Qt.ColorScheme.Dark:
            color = '#444444'
        else:
            color = '#cccccc'
        pen.setColor(color)
        painter = QPainter()
        painter.begin(self)
        painter.setPen(pen)

        # The grid lines are at world positions offset + k * size; the
        # view maps them to the screen
        offset = self.offset
        zoom = self.__view.zoom
        view_offset = self.__view.offset
        distance = self.__grid_size * zoom

        # Horizontal lines
        first = (zoom * offset.y() + view_offset.y()) % distance
        k = 0
        while first + k * distance < self.height():
            y = math.floor(first + k * distance + 0.5)
            painter.drawLine(QPoint(0, y), QPoint(int(self.width()), y))
            k += 1

        # Vertical lines
        first = (zoom * offset.x() + view_offset.x()) % distance
        k = 0
        while first + k * distance < self.width():
            x = math.floor(first + k * distance + 0.5)
            painter.drawLine(QPoint(x, 0), QPoint(x, int(self.height())))
            k += 1

        painter.end()
