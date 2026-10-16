import abc
from typing import Callable, Tuple
from PySide6.QtCore import QPoint
from signalflowgrapher.gui.graph_item import GraphItem

# Distance between two grid lines. The single definition of the grid size,
# used by the grid snapping, the grid drawing and paste.
GRID_SIZE = 30

# Returns the current pan of the graph (x, y). The model is the only owner
# of this state, e.g. `Model.get_grid_position`.
OffsetSource = Callable[[], Tuple[int, int]]


class Grid(abc.ABC):
    def __init__(self):
        super().__init__()
        self.__start_called = False
        self.__deviation_x = None
        self.__deviation_y = None

    @abc.abstractmethod
    def get_grid_position(self, p):
        pass

    def start_move(self):
        """
        Start move of widget on the grid.
        """
        # Deviation of move because of grid
        self.__deviation_x = 0
        self.__deviation_y = 0
        self.__start_called = True

    def relative_move(self, dx: int, dy: int, widget: GraphItem):
        """
        Do a relative move of a widget on the grid.
        """
        # When the user switches grid while dragging, start is not
        # called. Because of that variables must be initialized manually
        if (not self.__start_called):
            self.__deviation_x = 0
            self.__deviation_y = 0
            self.__start_called = True

        # Calculate the new absolute postion of the widget
        old_pos = widget.get_center()
        new_pos = QPoint(int(old_pos.x() + dx + self.__deviation_x),
                         int(old_pos.y() + dy + self.__deviation_y))

        # Calculate absolut position on grid
        grid_pos = self.get_grid_position(new_pos)

        # Calculate relative movement to grid position
        grid_dx = grid_pos.x() - old_pos.x()
        grid_dy = grid_pos.y() - old_pos.y()

        # Calculate deviation of relative move caused by grid
        self.__deviation_x += dx - grid_dx
        self.__deviation_y += dy - grid_dy

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

    def relative_move(self, dx: int, dy: int, widget: GraphItem):
        return super().relative_move(dx,
                                     dy,
                                     widget)

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

    def relative_move(self, dx, dy, widget):
        return QPoint(dx, dy)
