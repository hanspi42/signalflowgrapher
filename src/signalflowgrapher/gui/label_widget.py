from PyQt5.Qt import Qt, QFont, QFontDatabase, QLabel, QPoint
from signalflowgrapher.gui.graph_item import GraphItem
from signalflowgrapher.model.model import PositionedNodeAddedEvent, \
    PositionedNodeMovedEvent, CurvedBranchTransformedEvent, LabeledObject, \
    LabelMovedEvent, LabelChangedTextEvent
import os


class LabelWidget(QLabel, GraphItem):
    def __init__(self,
                 str,
                 owner: LabeledObject,
                 owner_widget: GraphItem,
                 parent=None,
                 flags=Qt.WindowFlags()):
        super().__init__(str, parent=parent, flags=flags)
        self.__owner = owner
        self.__owner_widget = owner_widget
        font_database = QFontDatabase()

        # Build absolute path to prevent problems on macOS
        path = os.path.join(os.path.dirname(__file__),
                            "../ressources/fonts/lmroman8-regular.otf")
        font_id = font_database.addApplicationFont(path)
        if (font_id == -1):
            raise IOError("Font could not be loaded")
        font_name = QFontDatabase.applicationFontFamilies(font_id)[0]
        font = QFont(font_name, 16)
        self.setFont(font)
        self.adjustSize()
        self.__reposition()

    def __reposition(self):
        """
        Reposition on parent widget based on own size and owner position.
        """
        center = self.__owner_widget.get_center()
        p = QPoint(int(center.x() + self.__owner.label_dx - self.width() / 2),
                   int(center.y() + self.__owner.label_dy - self.height() / 2))
        self.move(p)

    def select(self, number):
        """
        Select this widget. This changes the widget style.
        """
        self.setStyleSheet("QLabel {color: blue}")
        return super().select(number)

    def unselect(self):
        """
        Unselect this widget. This changes the widget style.
        """
        self.setStyleSheet("")
        return super().unselect()

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
            self.__reposition()
