import abc
import math
from typing import Callable, Tuple
from PySide6.QtCore import QPoint, QPointF

# Distance between two grid lines. The single definition of the grid size,
# used by the grid snapping, the grid drawing and paste.
GRID_SIZE = 30

# Returns the current pan of the graph (x, y). The model is the only owner
# of this state, e.g. `Model.get_grid_position`.
OffsetSource = Callable[[], Tuple[int, int]]


class Grid(abc.ABC):
    """
    Snapping of moves to the grid. Everything here is in world coordinates
    (the coordinates of the model); the caller converts screen distances
    with the ViewTransform.
    """

    def __init__(self):
        super().__init__()
        self._start_called = False
        self._deviation_x = None
        self._deviation_y = None

    @abc.abstractmethod
    def get_grid_position(self, p):
        pass

    def start_move(self):
        """
        Start move of widget on the grid.
        """
        # Deviation of move because of grid
        self._deviation_x = 0
        self._deviation_y = 0
        self._start_called = True

    def _ensure_started(self):
        # When the user switches grid while dragging, start is not
        # called. Because of that variables must be initialized manually
        if (not self._start_called):
            self.start_move()

    def relative_move(self, dx: float, dy: float, center: QPointF):
        """
        Do a relative move of a widget on the grid.

        dx, dy: the distance the mouse has moved, in world units (may be
        fractional when zoomed). center: the world position of the centre
        of the dragged widget. Returns the move to apply to the model, in
        whole world units.
        """
        self._ensure_started()

        # Calculate the new absolute postion of the widget
        old_pos = center
        new_pos = QPoint(int(old_pos.x() + dx + self._deviation_x),
                         int(old_pos.y() + dy + self._deviation_y))

        # Calculate absolut position on grid
        grid_pos = self.get_grid_position(new_pos)

        # Calculate relative movement to grid position
        grid_dx = grid_pos.x() - old_pos.x()
        grid_dy = grid_pos.y() - old_pos.y()

        # Calculate deviation of relative move caused by grid
        self._deviation_x += dx - grid_dx
        self._deviation_y += dy - grid_dy

        return QPoint(int(grid_dx), int(grid_dy))


class FixedGrid(Grid):
    def __init__(self, size: int, offset_source: OffsetSource):
        super().__init__()
        self.__size = size
        self.__offset_source = offset_source

    @property
    def offset(self) -> QPoint:
        """
        Position of the grid lines relative to the origin: the pan of the
        graph modulo the grid size. Always read from the offset source.
        """
        x, y = self.__offset_source()
        return QPoint(int(x % self.__size), int(y % self.__size))

    def get_grid_position(self, p):
        # Subtract 2 for previnting flapping of widgets
        offset = self.offset
        return offset + QPoint(
            int(self.__size*round((p.x()-offset.x()-2) / self.__size)),
            int(self.__size*round((p.y()-offset.y()-2) / self.__size)))


class NoneGrid(Grid):
    def __init__(self):
        super().__init__()

    def get_grid_position(self, p):
        return p

    def relative_move(self, dx, dy, center):
        # No grid: move by whole world units. The fractions that come from
        # a zoom (a screen pixel is more than one world unit) are carried
        # to the next move so that nothing is lost.
        self._ensure_started()
        x = dx + self._deviation_x
        y = dy + self._deviation_y
        move_x, move_y = math.floor(x + 0.5), math.floor(y + 0.5)
        self._deviation_x = x - move_x
        self._deviation_y = y - move_y
        return QPoint(move_x, move_y)
