from PySide6.QtWidgets import QWidget
from PySide6.QtCore import Qt, QPoint, QPointF
from PySide6.QtGui import QMouseEvent, QCursor
from signalflowgrapher.model.model import GraphMovedEvent
from signalflowgrapher.common.observable import ObjectObservable

# Some code is inspired by
# https://stackoverflow.com/questions/12219727/dragging-moving-a-qpushbutton-in-pyqt


class GraphItem(QWidget, ObjectObservable):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._selected = False
        self._selection_number = 0
        self.setCursor(QCursor(Qt.PointingHandCursor))
        self._mouse_press_pos = None
        self._mouse_move_pos = None

    @property
    def selected(self):
        return self._selected

    def get_selection_number(self):
        return self._selection_number

    def select(self, number):
        self._selected = True
        self._selection_number = number

    def unselect(self):
        self._selected = False

    def get_center(self) -> QPointF:
        return QPointF(self.x() + self.width() / 2,
                       self.y() + self.height() / 2)

    def move_relative(self, dx, dy):
        current_position = self.pos()
        new_position = QPoint(current_position.x() + dx,
                              current_position.y() + dy)
        self.move(new_position)

    def graph_moved_event(self, event: GraphMovedEvent):
        self.move_relative(event.dx, event.dy)

    def mousePressEvent(self, event, notify=True):
        self._mouse_press_pos = event.globalPos()
        self._mouse_move_pos = self._mouse_press_pos

        if notify:
            self._notify(
                WidgetPressEvent(self, event))

    def mouseMoveEvent(self, event):
        # Move is only triggered with left mouse button pressed
        if event.buttons() == Qt.LeftButton:
            self.setCursor(QCursor(Qt.ClosedHandCursor))
            global_position = event.globalPos()
            diff = global_position - self._mouse_move_pos

            self._notify(
                WidgetMoveEvent(
                    self,
                    diff.x(),
                    diff.y()))
            self._mouse_move_pos = global_position

        super(GraphItem, self).mouseMoveEvent(event)

    def mouseReleaseEvent(self, event, notify=True):
        self.setCursor(QCursor(Qt.PointingHandCursor))
        if notify:
            self._notify(
                WidgetReleaseEvent(self, self._mouse_press_pos, event))


class WidgetEvent(object):
    def __init__(self, widget: GraphItem):
        super().__init__()
        self.widget = widget


class WidgetClickEvent(WidgetEvent):
    def __init__(self,
                 widget: GraphItem,
                 press_pos: QPoint,
                 mouse_event: QMouseEvent):
        super().__init__(widget)
        self.press_pos = press_pos
        self.mouse_event = mouse_event


class WidgetPressEvent(WidgetClickEvent):
    def __init__(self, widget: GraphItem, mouse_event: QMouseEvent,
                 *args, **kwargs):
        super().__init__(widget, mouse_event.globalPos(), mouse_event,
                         *args, **kwargs)


class WidgetReleaseEvent(WidgetClickEvent):
    def __init__(self, press_pos: QPoint,
                 mouse_event: QMouseEvent, *args, **kwargs):
        super().__init__(press_pos, mouse_event, *args, **kwargs)


class WidgetMoveEvent(object):
    def __init__(self, widget: GraphItem, dx: int, dy: int):
        self.widget = widget
        self.dx = dx
        self.dy = dy
