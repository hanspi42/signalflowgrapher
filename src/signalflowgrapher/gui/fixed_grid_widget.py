from PySide6.QtCore import QPoint, Qt
from PySide6.QtWidgets import QWidget, QApplication
from PySide6.QtGui import QPaintEvent, QPainter, QPen


class FixedGridWidget(QWidget):
    def __init__(self, size, offset_source, *args, ** kwargs):
        super().__init__(*args, **kwargs)
        self.__grid_size = size
        self.__pen_width = 1
        self.__offset_source = offset_source

        # Disable the widgets to ignore all events
        # Widget should not become mousegrabber
        self.setDisabled(True)

    @property
    def offset(self) -> QPoint:
        """
        Position of the grid lines: the pan of the graph modulo the grid
        size. Read from the offset source (the model) at every paint.
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

        offset = self.offset

        # Horizontal lines
        start_h = QPoint(0, int(offset.y()))
        end_h = QPoint(int(self.width()), int(offset.y()))
        distance_h = QPoint(0, int(self.__grid_size))

        # Vertical lines
        start_v = QPoint(int(offset.x()), 0)
        end_v = QPoint(int(offset.x()), int(self.height()))
        distance_v = QPoint(int(self.__grid_size), 0)

        while start_h.y() < self.height():
            painter.drawLine(start_h, end_h)
            start_h += distance_h
            end_h += distance_h

        while start_v.x() < self.width():
            painter.drawLine(start_v, end_v)
            start_v += distance_v
            end_v += distance_v

        painter.end()
