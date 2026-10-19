import math
from PySide6.QtCore import QObject, QPoint, QPointF, Signal


# The zoom that the user can choose in the program (the class itself works
# with every zoom greater than 0). The graph can be zoomed out to see all of
# a big graph; there is no zoom in beyond 100%.
MIN_ZOOM = 0.1
MAX_ZOOM = 1.0
# One step of the zoom keys or one notch of the mouse wheel changes the zoom
# by this factor; four steps halve it.
ZOOM_STEP = 2 ** 0.25


class ViewTransform(QObject):
    """
    Maps between the two coordinate systems of the graph field.

    World coordinates are the coordinates of the model: positions of nodes
    and spline points, label offsets. They do not depend on how the graph
    is shown, and they are what is saved in files, copied to the clipboard,
    exported to TikZ and stored in undo commands.

    Screen coordinates are the pixel coordinates of the graph field widget,
    where all widgets are placed and where all mouse events happen.

        screen = zoom * world + offset
        world  = (screen - offset) / zoom

    At zoom 1 and offset (0, 0) both are identical (the situation of V2.0).
    The zoom is the only thing that scales; sizes of glyphs (node circle,
    line width, font) are not part of this class.

    The signal `changed` is emitted when zoom or offset change; whoever
    shows the graph has to refresh its widgets then.
    """

    changed = Signal()

    def __init__(self, zoom: float = 1.0, offset: QPointF = None,
                 parent=None):
        super().__init__(parent)
        self.__zoom = self.__checked(zoom)
        self.__offset = QPointF(offset) if offset is not None else QPointF()

    @staticmethod
    def __checked(zoom: float) -> float:
        if not zoom > 0:
            raise ValueError("zoom must be greater than 0, got %r" % zoom)
        return float(zoom)

    @property
    def zoom(self) -> float:
        return self.__zoom

    @property
    def offset(self) -> QPointF:
        """Screen position of the world origin."""
        return QPointF(self.__offset)

    @property
    def is_identity(self) -> bool:
        return self.__zoom == 1.0 and self.__offset == QPointF()

    def set(self, zoom: float = None, offset: QPointF = None):
        """Change zoom and/or offset. Emits `changed` if something differs."""
        new_zoom = self.__zoom if zoom is None else self.__checked(zoom)
        new_offset = self.__offset if offset is None else QPointF(offset)
        if new_zoom == self.__zoom and new_offset == self.__offset:
            return
        self.__zoom = new_zoom
        self.__offset = new_offset
        self.changed.emit()

    def reset(self):
        """Back to zoom 1 and offset (0, 0)."""
        self.set(1.0, QPointF())

    # ------------------------------------------------------------ points
    def to_screen(self, p) -> QPointF:
        """Screen position of a world point (exact, not rounded)."""
        return QPointF(p.x() * self.__zoom + self.__offset.x(),
                       p.y() * self.__zoom + self.__offset.y())

    def to_world(self, p) -> QPointF:
        """World position of a screen point (exact, not rounded)."""
        return QPointF((p.x() - self.__offset.x()) / self.__zoom,
                       (p.y() - self.__offset.y()) / self.__zoom)

    def to_screen_point(self, p) -> QPoint:
        """
        Screen pixel of a world point. All widgets that show a model
        position (node centres, branch end and spline points, handles) use
        this one rule, so that a branch ends exactly at the node it
        belongs to. It rounds down (like int() for positive values did in
        V2.0), which makes a move by whole pixels an exact translation.
        """
        s = self.to_screen(p)
        return QPoint(math.floor(s.x()), math.floor(s.y()))

    # ------------------------------------------------------------ lengths
    def to_world_delta(self, d: float) -> float:
        """A distance on the screen as distance in the world."""
        return d / self.__zoom

    def to_screen_delta(self, d: float) -> float:
        """A distance in the world as distance on the screen."""
        return d * self.__zoom
