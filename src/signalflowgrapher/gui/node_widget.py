from PySide6.QtGui import QPainter, QPen, QRegion
from PySide6.QtWidgets import QSizePolicy
from PySide6.QtCore import Qt, QPoint, QPointF, QRect
from signalflowgrapher.gui.graph_item import GraphItem
from signalflowgrapher.gui.view_transform import ViewTransform
from signalflowgrapher.model.model import (
    PositionedNode, PositionedNodeMovedEvent)


class NodeWidget(GraphItem):
    def __init__(self, owner: PositionedNode, view: ViewTransform,
                 *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.__owner = owner
        self.__view = view
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
        if self.selected:
            pen.setColor(self.palette().highlight().color())
        else:
            pen.setColor(self.palette().text().color())

        painter.setPen(pen)
        width = 2 * self.__radius
        height = width
        painter.setBrush(self.palette().window())
        painter.drawEllipse(
            self.__circle_width,
            self.__circle_width,
            width,
            height)

        if self.selected:
            pen.setColor(self.palette().highlight().color())
            painter.setPen(pen)
            painter.setBrush(self.palette().highlight())
            rect = QRect(0, 0, self.__size, self.__size)
            painter.drawText(
                rect, Qt.AlignCenter, str(self.get_selection_number()))

        painter.end()

    def refresh(self, force: bool = False):
        """
        Place the widget so that its centre is on the node.
        """
        center = self.__view.to_screen_point(
            QPointF(self.__owner.x, self.__owner.y))
        self.move(QPoint(int(center.x() - self.width() / 2),
                         int(center.y() - self.height() / 2)))

    def node_moved_event(self, event: PositionedNodeMovedEvent):
        """
        Triggered after node has been moved.
        """
        if self.__owner is event.node:
            self.refresh()

    def get_world_center(self) -> QPointF:
        """
        The position of the node in world coordinates (exactly, not the
        rounded position of the widget on the screen).
        """
        return QPointF(self.__owner.x, self.__owner.y)

    def get_center(self) -> QPointF:
        """
        Get the position of the center of the widget.
        """
        return QPointF(self.x() + self.width() / 2,
                       self.y() + self.height() / 2)
