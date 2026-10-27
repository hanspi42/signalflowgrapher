from PySide6.QtGui import QPainter, QPen, QRegion
from PySide6.QtWidgets import QSizePolicy
from PySide6.QtCore import Qt, QPoint, QPointF, QRect
from signalflowgrapher.gui import glyphs
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
        self.__zoom = None
        self.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        self.__apply_zoom()

    def __apply_zoom(self):
        """
        Size of the widget and of the area that reacts to the mouse. The
        node is drawn in the scale of the zoom (see paintEvent); the widget
        has an even size, so that its centre is on a pixel, and it is not
        smaller than the minimum click area.
        """
        self.__zoom = self.__view.zoom
        half = glyphs.node_half_size(self.__zoom)
        self.resize(2 * half, 2 * half)
        self.setMask(QRegion(0, 0, 2 * half, 2 * half, QRegion.Ellipse))
        self.update()

    def paintEvent(self, QPaintEvent):
        painter = QPainter()
        painter.begin(self)
        painter.setRenderHint(QPainter.Antialiasing)

        # Draw in units of zoom 100% around the centre of the widget, so
        # that the circle, its line width and the number scale together
        zoom = self.__view.zoom
        painter.translate(self.width() / 2, self.height() / 2)
        painter.scale(zoom, zoom)

        pen = QPen()
        pen.setWidth(glyphs.NODE_CIRCLE_WIDTH)
        if self.selected:
            pen.setColor(self.palette().highlight().color())
        else:
            pen.setColor(self.palette().text().color())

        painter.setPen(pen)
        radius = glyphs.NODE_RADIUS
        painter.setBrush(self.palette().window())
        painter.drawEllipse(-radius, -radius, 2 * radius, 2 * radius)

        if self.selected:
            pen.setColor(self.palette().highlight().color())
            painter.setPen(pen)
            painter.setBrush(self.palette().highlight())
            half = glyphs.NODE_HALF_SIZE
            rect = QRect(-half, -half, 2 * half, 2 * half)
            painter.drawText(
                rect, Qt.AlignCenter, str(self.get_selection_number()))

        painter.end()

    def refresh(self, force: bool = False):
        """
        Size the widget for the zoom and place it so that its centre is on
        the node.
        """
        if force or self.__zoom != self.__view.zoom:
            self.__apply_zoom()
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
