import math
from importlib import resources
from PySide6.QtWidgets import QLabel
from PySide6.QtGui import QFont, QFontDatabase, QCursor, QPalette
from PySide6.QtCore import Qt, QPoint, QPointF
from signalflowgrapher.common.observable import ObjectObservable
from signalflowgrapher.model.model import (
    PositionedNodeAddedEvent, PositionedNodeMovedEvent,
    CurvedBranchTransformedEvent, CurvedBranch, LabeledObject,
    LabelMovedEvent, LabelChangedTextEvent
)

from signalflowgrapher.gui.graph_item import (
    WidgetPressEvent, WidgetMoveEvent, WidgetReleaseEvent
)
from signalflowgrapher.gui import glyphs
from signalflowgrapher.gui.view_transform import ViewTransform

# Load font using importlib.resources
with resources.as_file(
        resources.files("signalflowgrapher.resources")
        .joinpath("HeptaSlab-Regular.ttf")) as font_path:
    roman_font = str(font_path)


class LabelWidget(QLabel, ObjectObservable):
    def __init__(self,
                 text: str,
                 owner: LabeledObject,
                 owner_widget,
                 view: ViewTransform,
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
        self.__view = view

        font_id = QFontDatabase.addApplicationFont(roman_font)
        if (font_id == -1):
            raise IOError("Font could not be loaded")
        self.__font_name = QFontDatabase.applicationFontFamilies(font_id)[0]
        self.__zoom = None
        self.__apply_zoom()
        self.__reposition()

    def __apply_zoom(self):
        """
        The text scales with the zoom, like everything else that is drawn.
        """
        self.__zoom = self.__view.zoom
        font = QFont(self.__font_name)
        font.setPointSizeF(glyphs.LABEL_FONT_POINTS * self.__zoom)
        self.setFont(font)
        # A label without text (a node without a name) does not notice that
        # its size hint is out of date after a change of the font. Changing
        # the margin (setting the same value is ignored) makes it compute
        # the size hint again.
        self.setMargin(1)
        self.setMargin(0)
        self.adjustSize()

    # Selection
    @property
    def selected(self):
        return self._selected

    def get_selection_number(self):
        return self._selection_number
    
    def select(self, number):
        self._selected = True
        self._selection_number = number
        self.setForegroundRole(QPalette.Highlight)

    def unselect(self):
        self._selected = False
        self.setForegroundRole(QPalette.WindowText)

    # Position / movement
    def get_center(self) -> QPointF:
        return QPointF(self.x() + self.width() / 2,
                       self.y() + self.height() / 2)
    
    def get_world_center(self) -> QPointF:
        """
        The centre of the label in world coordinates, converted from the
        position on the screen (the label is placed in whole pixels).
        """
        return self.__view.to_world(self.get_center())

    def refresh(self, force: bool = False):
        """
        Derive the position from the owner widget and the label offset.
        The owner widget has to be up to date: refresh it first.
        """
        if force or self.__zoom != self.__view.zoom:
            self.__apply_zoom()
        self.__reposition()

    def __reposition(self):
        """
        Reposition on parent widget based on own size and owner position.
        """
        # floor (not int): a move of the owner by a whole number of pixels
        # moves the label by exactly that number, also at negative positions
        # The offset is in world units, it scales with the zoom
        center = self.__owner_widget.get_center()
        dx = self.__view.to_screen_delta(self.__owner.label_dx)
        dy = self.__view.to_screen_delta(self.__owner.label_dy)
        p = QPoint(
            math.floor(center.x() + dx - self.width() / 2),
            math.floor(center.y() + dy - self.height() / 2))
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
        Makes sure the position is updated accordingly if necessary. The
        label of a branch is placed relative to the middle of the branch,
        which moves when one of its end nodes moves.
        """
        if self.__owner is event.node:
            self.__reposition()
        elif isinstance(self.__owner, CurvedBranch) and (
                self.__owner.start is event.node
                or self.__owner.end is event.node):
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
        self._mouse_press_pos = event.globalPosition().toPoint()
        self._mouse_move_pos = self._mouse_press_pos

        if notify:
            self._notify(WidgetPressEvent(self, event))

    def mouseMoveEvent(self, event):
        if event.buttons() == Qt.LeftButton:
            self.setCursor(QCursor(Qt.ClosedHandCursor))
            global_pos = event.globalPosition().toPoint()
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
