from typing import Optional

from PySide6.QtCore import QPointF, QRectF, QSize, Qt
from PySide6.QtGui import QColor, QPainter, QPainterPath, QPen, QTransform
from PySide6.QtWidgets import QWidget

from signalflowgrapher.gui.view_transform import ViewTransform
from signalflowgrapher.model.model import CurvedBranch, Model


class MiniMapMapping:
    """
    Maps world coordinates (the coordinates of the model) to positions in
    the mini map and back: a scale and a shift.
    """

    def __init__(self, scale: float, shift_x: float, shift_y: float):
        self.scale = scale
        self.shift_x = shift_x
        self.shift_y = shift_y

    def to_minimap(self, p: QPointF) -> QPointF:
        return QPointF(p.x() * self.scale + self.shift_x,
                       p.y() * self.scale + self.shift_y)

    def to_world(self, p: QPointF) -> QPointF:
        return QPointF((p.x() - self.shift_x) / self.scale,
                       (p.y() - self.shift_y) / self.scale)

    def transform(self) -> QTransform:
        return QTransform(self.scale, 0, 0, self.scale,
                          self.shift_x, self.shift_y)


class MiniMapWidget(QWidget):
    """
    A small map of the whole graph that lies over a corner of the graph
    field. It shows

      * all branches as thin lines and all nodes as dots,
      * a rectangle for the part of the graph that the graph field shows.

    Labels are not shown and the branches have no arrows. Everything is
    drawn from the model (not from the widgets of the graph field), in the
    scale that fits the whole graph and the visible part into the map.

    A click or drag in the map moves the view: the part that is shown
    follows the mouse. This changes only the view (like a pan), not the
    graph, so it is not an undoable operation.
    """

    SIZE = QSize(220, 160)
    # Distance from the border of the graph field to the map
    MARGIN = 10
    # Space between the border of the map and the content
    PADDING = 8
    NODE_RADIUS = 2.5
    LINE_WIDTH = 1.2

    def __init__(self, model: Model, view: ViewTransform, parent: QWidget):
        super().__init__(parent)
        self.__model = model
        self.__view = view
        self.setFixedSize(self.SIZE)
        # Clicking in the map must not take the keyboard from the graph
        self.setFocusPolicy(Qt.NoFocus)
        self.setCursor(Qt.PointingHandCursor)
        # While the mouse drags the view the mapping does not change, so
        # that the map does not rescale under the mouse (it would, as soon
        # as the shown part leaves the graph)
        self.__frozen_mapping: Optional[MiniMapMapping] = None
        self.__grab_offset = QPointF()
        self.hide()

    # ------------------------------------------------------------ geometry
    @staticmethod
    def __curve(branch: CurvedBranch) -> QPainterPath:
        path = QPainterPath(QPointF(branch.start.x, branch.start.y))
        path.cubicTo(QPointF(branch.spline1_x, branch.spline1_y),
                     QPointF(branch.spline2_x, branch.spline2_y),
                     QPointF(branch.end.x, branch.end.y))
        return path

    def graph_rect(self) -> Optional[QRectF]:
        """
        The smallest rectangle (world coordinates) that contains all nodes
        and all branches (the curves themselves, not only their end points).
        None for an empty graph. Labels do not count.
        """
        graph = self.__model.graph
        if graph is None:
            return None
        left = top = float("inf")
        right = bottom = float("-inf")
        for node in graph.nodes:
            left, right = min(left, node.x), max(right, node.x)
            top, bottom = min(top, node.y), max(bottom, node.y)
        for branch in graph.branches:
            curve = self.__curve(branch).boundingRect()
            left, right = min(left, curve.left()), max(right, curve.right())
            top, bottom = min(top, curve.top()), max(bottom, curve.bottom())
        if left > right:
            return None
        return QRectF(QPointF(left, top), QPointF(right, bottom))

    def visible_rect(self) -> QRectF:
        """The part of the world that the graph field shows."""
        field = self.parentWidget()
        top_left = self.__view.to_world(QPointF(0, 0))
        bottom_right = self.__view.to_world(
            QPointF(field.width(), field.height()))
        return QRectF(top_left, bottom_right).normalized()

    def world_rect(self) -> QRectF:
        """
        The part of the world that the map shows: the graph and the visible
        part, so that the rectangle of the visible part is always in the map
        also when the user has panned away from the graph.
        """
        rect = self.visible_rect()
        graph = self.graph_rect()
        if graph is not None:
            rect = QRectF(
                QPointF(min(rect.left(), graph.left()),
                        min(rect.top(), graph.top())),
                QPointF(max(rect.right(), graph.right()),
                        max(rect.bottom(), graph.bottom())))
        return rect

    def mapping(self) -> MiniMapMapping:
        """
        The mapping of world coordinates into the map that is in use: the
        frozen one while the mouse drags, else the one that fits the whole
        content into the map.
        """
        if self.__frozen_mapping is not None:
            return self.__frozen_mapping
        return self.fitting_mapping()

    def fitting_mapping(self) -> MiniMapMapping:
        rect = self.world_rect()
        width = max(rect.width(), 1.0)
        height = max(rect.height(), 1.0)
        available_w = self.width() - 2 * self.PADDING
        available_h = self.height() - 2 * self.PADDING
        scale = min(available_w / width, available_h / height)
        # centred in the map
        shift_x = (self.width() - width * scale) / 2 - rect.left() * scale
        shift_y = (self.height() - height * scale) / 2 - rect.top() * scale
        return MiniMapMapping(scale, shift_x, shift_y)

    def visible_rect_in_minimap(self) -> QRectF:
        """The rectangle of the shown part, in positions of the map."""
        mapping = self.mapping()
        rect = self.visible_rect()
        return QRectF(mapping.to_minimap(rect.topLeft()),
                      mapping.to_minimap(rect.bottomRight())).normalized()

    # ------------------------------------------------------------- drawing
    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        painter.setClipRect(self.rect())
        palette = self.palette()
        text = palette.text().color()
        highlight = palette.highlight().color()

        # Background (opaque: the widgets of the graph underneath would
        # shine through as grey bands) and border
        painter.fillRect(self.rect(), palette.window().color())
        border = QColor(text)
        border.setAlpha(120)
        painter.setPen(QPen(border, 1))
        painter.setBrush(Qt.NoBrush)
        painter.drawRect(QRectF(self.rect()).adjusted(0.5, 0.5, -0.5, -0.5))

        graph = self.__model.graph
        mapping = self.mapping()

        if graph is not None:
            # Branches: lines of the same width at every scale
            painter.save()
            painter.setTransform(mapping.transform())
            pen = QPen(text)
            pen.setCosmetic(True)
            pen.setWidthF(self.LINE_WIDTH)
            painter.setPen(pen)
            for branch in graph.branches:
                painter.drawPath(self.__curve(branch))
            painter.restore()

            # Nodes: dots
            painter.setPen(Qt.NoPen)
            painter.setBrush(text)
            for node in graph.nodes:
                centre = mapping.to_minimap(QPointF(node.x, node.y))
                painter.drawEllipse(centre, self.NODE_RADIUS,
                                    self.NODE_RADIUS)

        # The part that the graph field shows
        shown = self.visible_rect_in_minimap()
        fill = QColor(highlight)
        fill.setAlpha(45)
        painter.setPen(QPen(highlight, 2))
        painter.setBrush(fill)
        painter.drawRect(shown)
        painter.end()

    # --------------------------------------------------------------- mouse
    def mousePressEvent(self, event):
        if event.button() != Qt.LeftButton:
            event.ignore()
            return
        self.__frozen_mapping = self.fitting_mapping()
        position = event.position()
        shown = self.visible_rect_in_minimap()
        if shown.contains(position):
            # Pull the rectangle where it is, without a jump
            self.__grab_offset = position - shown.center()
        else:
            # Show the part around the clicked position
            self.__grab_offset = QPointF(0, 0)
        self.__show_around(position - self.__grab_offset)
        event.accept()

    def mouseMoveEvent(self, event):
        if self.__frozen_mapping is not None:
            self.__show_around(event.position() - self.__grab_offset)
            event.accept()

    def mouseReleaseEvent(self, event):
        if self.__frozen_mapping is not None:
            self.__frozen_mapping = None
            self.update()
            event.accept()

    def wheelEvent(self, event):
        # Zooming with Ctrl + wheel is done by the graph field
        event.ignore()

    def __show_around(self, position_in_minimap: QPointF):
        """
        Move the view so that the centre of the graph field shows the world
        position that is at `position_in_minimap`. The zoom does not change.
        """
        world = self.mapping().to_world(position_in_minimap)
        field = self.parentWidget()
        zoom = self.__view.zoom
        # whole pixels: the widgets are then only moved, not rebuilt
        self.__view.set(offset=QPointF(
            round(field.width() / 2 - zoom * world.x()),
            round(field.height() / 2 - zoom * world.y())))
