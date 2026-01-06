from importlib import resources
from PySide6.QtWidgets import QLabel
from PySide6.QtGui import QFont, QFontDatabase, QCursor
from PySide6.QtCore import Qt, QPoint, QPointF
from signalflowgrapher.common.observable import ObjectObservable
from signalflowgrapher.model.model import (
    PositionedNodeAddedEvent, PositionedNodeMovedEvent,
    CurvedBranchTransformedEvent, LabeledObject,
    LabelMovedEvent, LabelChangedTextEvent,
    GraphMovedEvent
)

from signalflowgrapher.gui.graph_item import (
    WidgetPressEvent, WidgetMoveEvent, WidgetReleaseEvent
)

# Load font using importlib.resources
with resources.path("signalflowgrapher.resources", "HeptaSlab-Regular.ttf") as font_path:
    roman_font = str(font_path)


class LabelWidget(QLabel, ObjectObservable):
    def __init__(self,
                 text: str,
                 owner: LabeledObject,
                 owner_widget,
                 parent=None,
                 flags=Qt.WindowFlags()):
        QLabel.__init__(self, text, parent=parent, flags=flags)
        ObjectObservable.__init__(self)

        # --- was in GraphItem ---
        self._selected = False
        self._selection_number = 0
        self.setCursor(QCursor(Qt.PointingHandCursor))
        self._mouse_press_pos = None
        self._mouse_move_pos = None

        # --- LabelWidget-specific ---
        self.__owner = owner
        self.__owner_widget = owner_widget

        font_database = QFontDatabase()
        font_id = font_database.addApplicationFont(roman_font)
        if (font_id == -1):
            raise IOError("Font could not be loaded")
        font_name = QFontDatabase.applicationFontFamilies(font_id)[0]
        font = QFont(font_name, 14)
        self.setFont(font)
        self.adjustSize()
        self.__reposition()

    # Selection
    @property
    def selected(self):
        return self._selected
    
    def get_selection_number(self):
        return self._selection_number
    
    def select(self, number):
        self._selected = True
        self._selection_number = number
        self.setStyleSheet("QLabel { color: blue; }")

    def unselect(self):
        self._selected = False
        self.setStyleSheet("")
    

    # Position / movement
    def get_center(self) -> QPointF:
        return QPointF(self.x() + self.width() / 2,
                       self.y() + self.height() / 2)
    
    def move_relative(self, dx, dy):
        pos = self.pos()
        self.move(QPoint(pos.x() + dx, pos.y() + dy))

    def graph_moved_event(self, event: GraphMovedEvent):
        self.move_relative(event.dx, event.dy)
    
    def __reposition(self):
        """
        Reposition on parent widget based on own size and owner position.
        """
        center = self.__owner_widget.get_center()
        p = QPoint(int(center.x() + self.__owner.label_dx - self.width() / 2),
                   int(center.y() + self.__owner.label_dy - self.height() / 2))
        self.move(p)

    # Model events
    def node_added_event(self, event: PositionedNodeAddedEvent):
        """
        Triggered after node has been added.
        Makes sure the position is updated accordingly if necessary.
        """
        if self.__owner is event.node:
            self.__reposition()

    def node_moved_event(self, event: PositionedNodeMovedEvent):
        """
        Triggered after node has moved.
        Makes sure the position is updated accordingly if necessary.
        """
        if self.__owner is event.node:
            self.__reposition()

    def branch_transformed_event(self, event: CurvedBranchTransformedEvent):
        """
        Triggered after branch has been transformed.
        Makes sure the position is updated accordingly if necessary.
        """
        if self.__owner is event.branch:
            self.__reposition()

    def label_moved_event(self, event: LabelMovedEvent):
        """
        Triggered after the label has been moved relative to owner.
        Makes sure the position is updated accordingly if necessary.
        """
        if self.__owner is event.labeled_obj:
            self.__reposition()

    def label_changed_text_event(self, event: LabelChangedTextEvent):
        """
        Triggered after the label text has changed which also changes the
        label width. Makes sure the position is updated accordingly because
        the label is placed centered on the position.
        """
        if self.__owner is event.labeled_obj:
            self.adjustSize()
            self.__reposition()

    # Mouse handling (was in GraphItem)
    def mousePressEvent(self, event, notify=True):
        self._mouse_press_pos = event.globalPos()
        self._mouse_move_pos = self._mouse_press_pos

        if notify:
            self._notify(WidgetPressEvent(self, event))


    def mouseMoveEvent(self, event):
        if event.buttons() == Qt.LeftButton:
            self.setCursor(QCursor(Qt.ClosedHandCursor))
            global_pos = event.globalPos()
            diff = global_pos - self._mouse_move_pos

            self._notify(
                WidgetMoveEvent(self, diff.x(), diff.y())
            )
            self._mouse_move_pos = global_pos


    def mouseReleaseEvent(self, event, notify=True):
        self.setCursor(QCursor(Qt.PointingHandCursor))

        if notify:
            self._notify(
                WidgetReleaseEvent(self, self._mouse_press_pos, event)
            )



# Review Comments 08/23: Font changed to one that is more readable on screen.
# Source: https://fonts.google.com/specimen/Zilla+Slab
