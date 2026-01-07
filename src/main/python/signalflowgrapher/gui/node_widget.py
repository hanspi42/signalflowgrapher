from PySide6.QtGui import QPainter, QPen, QColor, QRegion
from PySide6.QtWidgets import QSizePolicy
from PySide6.QtCore import Qt, QPointF, QRect
from signalflowgrapher.gui.graph_item import GraphItem
from signalflowgrapher.model.model import (
    PositionedNode, PositionedNodeMovedEvent)


class NodeWidget(GraphItem):
    def __init__(self, owner: PositionedNode, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.__owner = owner
        self.__radius = 8
        self.__circle_width = 3
        self.__size = self.__radius * 2 + self.__circle_width * 2
        self.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        self.resize(self.__size, self.__size)
        mask = QRegion(0, 0, self.__size, self.__size, QRegion.Ellipse)
        self.setMask(mask)

    def paintEvent(self, QPaintEvent):
        painter = QPainter()
        painter.begin(self)
        painter.setRenderHint(QPainter.Antialiasing)

        pen = QPen()
        pen.setWidth(self.__circle_width)

        painter.setPen(pen)
        width = 2 * self.__radius
        height = width
        q = QColor()
        q.setNamedColor("white")
        painter.setBrush(q)
        painter.drawEllipse(
            self.__circle_width,
            self.__circle_width,
            width,
            height)

        if self.selected:
            color = QColor()
            color.setNamedColor("blue")
            pen.setColor(color)
            painter.setPen(pen)
            painter.setBrush(color)
            rect = QRect(0, 0, self.__size, self.__size)
            painter.drawText(rect,
                             Qt.AlignCenter,
                             str(self.get_selection_number()))

        painter.end()

    def node_moved_event(self, event: PositionedNodeMovedEvent):
        """
        Triggered after node has been moved.
        Reacts to node move with move of widget.
        """
        if self.__owner is event.node:
            self.move_relative(event.dx, event.dy)

    def get_center(self) -> QPointF:
        """
        Get the position of the center of the widget.
        """
        return QPointF(self.x() + self.width() / 2,
                       self.y() + self.height() / 2)
