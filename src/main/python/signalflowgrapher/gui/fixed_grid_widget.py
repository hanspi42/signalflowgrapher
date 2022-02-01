from PyQt5.Qt import QPoint
from PyQt5.QtWidgets import QWidget
from PyQt5.QtGui import QPaintEvent, QPainter, QPen, QColor


class FixedGridWidget(QWidget):
    def __init__(self, size, *args, ** kwargs):
        super().__init__(*args, **kwargs)
        self.__grid_size = size
        self.__pen_width = 1
        self.__line_color = QColor(192, 192, 192, 255)
        self.__offset = QPoint(0, 0)

        # Disable the widgets to ignore all events
        # Widget should not become mousegrabber
        self.setDisabled(True)

    def set_offset(self, offset):
        """
        Sets an offset on the grid to simulate a move.
        """
        self.__offset = QPoint(int(offset.x() % self.__grid_size),
                               int(offset.y() % self.__grid_size))

    def paintEvent(self, event: QPaintEvent):
        # Init painter
        pen = QPen()
        pen.setWidth(self.__pen_width)
        pen.setColor(self.__line_color)
        painter = QPainter()
        painter.begin(self)
        painter.setPen(pen)

        # Horizontal lines
        start_h = QPoint(0, int(self.__offset.y()))
        end_h = QPoint(int(self.width()), int(self.__offset.y()))
        distance_h = QPoint(0, int(self.__grid_size))

        # Vertical lines
        start_v = QPoint(int(self.__offset.x()), 0)
        end_v = QPoint(int(self.__offset.x()), int(self.height()))
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
