"""
Headless GUI test harness for the SignalFlowGrapher.

Builds the real object graph (Model, CommandHandler, MainController,
IOController, GraphField) without the dependency-injection containers and
without MainWindow, and drives the GraphField with synthetic mouse events.

Used by the V3.0 safety net (see DEVDOCU.md, step 0). Must work unchanged
before and after the zoom refactoring, so only use public behaviour:
creating, dragging, panning, copy/paste, undo/redo, save/load.

Run with the offscreen Qt platform (set automatically below).
"""
import os
os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

import uuid  # noqa: E402
from signalflowgrapher.algorithms import graph as graph_module  # noqa: E402
from PySide6.QtCore import QEvent, QPoint, QPointF, Qt  # noqa: E402
from PySide6.QtGui import QCursor, QMouseEvent  # noqa: E402
from PySide6.QtWidgets import QApplication  # noqa: E402

from signalflowgrapher.commands.command_handler import CommandHandler  # noqa
from signalflowgrapher.controllers.io_controller import IOController  # noqa
from signalflowgrapher.controllers.main_controller import MainController  # noqa
from signalflowgrapher.gui.graph_field import GraphField  # noqa: E402
from signalflowgrapher.model.model import Model  # noqa: E402


_id_counter = [0]


def _deterministic_uuid4():
    _id_counter[0] += 1
    return uuid.UUID(int=_id_counter[0])


def use_deterministic_ids(start=1):
    """
    Make newly created nodes/branches get sequential UUIDs, so that set
    iteration orders (and therefore test runs) are reproducible.
    """
    _id_counter[0] = start - 1
    graph_module.uuid = type("uuid_stub", (), {
        "uuid4": staticmethod(_deterministic_uuid4),
        "UUID": uuid.UUID})


def get_app() -> QApplication:
    app = QApplication.instance()
    if app is None:
        app = QApplication([])
    return app


def _private(obj, cls, name):
    """Read a name-mangled private attribute (test support only)."""
    return getattr(obj, "_%s__%s" % (cls, name))


class Harness:
    """
    Real GraphField + Model + controllers in an offscreen window.

    Coordinates passed to the helper methods are canvas pixels (the
    coordinate space of GraphField), exactly what a user sees on screen.
    """

    def __init__(self, width=1000, height=700, deterministic_ids=True):
        get_app()
        if deterministic_ids:
            use_deterministic_ids()
        self.model = Model()
        self.command_handler = CommandHandler()
        self.controller = MainController(self.model, self.command_handler)
        self.io = IOController(self.model, self.command_handler)
        self.field = GraphField(self.controller, self.model,
                                self.command_handler)
        self.field.setMinimumSize(0, 0)
        self.field.resize(width, height)
        self.field.show()
        self.io.new_graph()
        self.process_events()

    # ------------------------------------------------------------ plumbing
    @staticmethod
    def process_events():
        get_app().processEvents()

    def private(self, name):
        """Private attribute of the GraphField (name without prefix)."""
        return _private(self.field, "GraphField", name)

    @property
    def model_widget_map(self):
        return self.private("model_widget_map")

    @property
    def model_label_map(self):
        return self.private("model_label_map")

    @property
    def grid_offset(self):
        return self.private("grid_offset")

    def widget_of(self, model_obj):
        return self.model_widget_map[model_obj]

    def label_of(self, model_obj):
        return self.model_label_map[model_obj]

    @property
    def nodes(self):
        return list(self.model.graph.nodes)

    @property
    def branches(self):
        return list(self.model.graph.branches)

    # ------------------------------------------------------ mouse emulation
    # Events are built from *global* mouse positions, like a real mouse:
    # the pointer does not move with the widget that is being dragged.
    def _event(self, etype, widget, glob, button=Qt.LeftButton,
               buttons=Qt.LeftButton, modifiers=Qt.NoModifier):
        glob = QPoint(glob)
        local = QPointF(widget.mapFromGlobal(glob))
        return QMouseEvent(etype, local, QPointF(glob), button, buttons,
                           modifiers)

    def _send(self, widget, event):
        QApplication.sendEvent(widget, event)
        self.process_events()

    def global_center(self, widget):
        return widget.mapToGlobal(self._center_local(widget))

    def press(self, widget, glob=None, modifiers=Qt.NoModifier):
        glob = glob if glob is not None else self.global_center(widget)
        self._send(widget, self._event(
            QEvent.MouseButtonPress, widget, glob, modifiers=modifiers))

    def move(self, widget, glob, modifiers=Qt.NoModifier):
        self._send(widget, self._event(
            QEvent.MouseMove, widget, glob, modifiers=modifiers))

    def release(self, widget, glob=None, modifiers=Qt.NoModifier):
        glob = glob if glob is not None else self.global_center(widget)
        self._send(widget, self._event(
            QEvent.MouseButtonRelease, widget, glob,
            buttons=Qt.NoButton, modifiers=modifiers))

    @staticmethod
    def _center_local(widget):
        return QPoint(widget.width() // 2, widget.height() // 2)

    def click(self, widget, modifiers=Qt.NoModifier):
        """Click on the widget centre (press + release, no movement)."""
        g = self.global_center(widget)
        self.press(widget, g, modifiers=modifiers)
        self.release(widget, g, modifiers=modifiers)

    def drag(self, widget, dx, dy, steps=4, modifiers=Qt.NoModifier):
        """
        Press on the widget centre, move the mouse by (dx, dy) screen
        pixels in `steps` equal parts, release. Events go to the widget
        that was pressed (like Qt's implicit mouse grab).
        """
        g0 = self.global_center(widget)
        self.press(widget, g0, modifiers=modifiers)
        for i in range(1, steps + 1):
            self.move(widget, g0 + QPoint(round(dx * i / steps),
                                          round(dy * i / steps)),
                      modifiers=modifiers)
        self.release(widget, g0 + QPoint(dx, dy), modifiers=modifiers)

    # ------------------------------------------------------ user operations
    def double_click(self, x, y):
        """Create a node by double-clicking the canvas at (x, y)."""
        before = set(self.nodes)
        g = self.field.mapToGlobal(QPoint(x, y))
        self._send(self.field, self._event(
            QEvent.MouseButtonDblClick, self.field, g))
        # Qt delivers a release after the double click
        self.release(self.field, g)
        new = set(self.nodes) - before
        assert len(new) == 1, "double click did not create exactly one node"
        return new.pop()

    def pan(self, dx, dy, start=(5, 5), steps=4):
        """Drag the empty canvas by (dx, dy) screen pixels."""
        g0 = self.field.mapToGlobal(QPoint(*start))
        self.press(self.field, g0)
        for i in range(1, steps + 1):
            self.move(self.field, g0 + QPoint(round(dx * i / steps),
                                              round(dy * i / steps)))
        self.release(self.field, g0 + QPoint(dx, dy))

    def drag_node(self, node, dx, dy, **kw):
        self.drag(self.widget_of(node), dx, dy, **kw)

    def drag_label(self, model_obj, dx, dy, **kw):
        self.drag(self.label_of(model_obj), dx, dy, **kw)

    def select(self, *model_objs):
        """Select exactly these nodes/branches (via single/shift clicks)."""
        first = True
        for obj in model_objs:
            w = self.widget_of(obj)
            self.click(w, modifiers=(Qt.NoModifier if first
                                     else Qt.ShiftModifier))
            first = False
        return self.field.get_selection()

    def ctrl_click_branch(self, start, end):
        """Select `start`, Ctrl+click `end` -> create branch (auto pos)."""
        before = set(self.branches)
        self.select(start)
        self.click(self.widget_of(end), modifiers=Qt.ControlModifier)
        new = set(self.branches) - before
        assert len(new) == 1, "branch not created"
        return new.pop()

    def selected_handles(self):
        return list(self.private("handles"))

    def select_branch(self, branch):
        self.click(self.widget_of(branch))
        return self.selected_handles()

    def drag_handle(self, handle, dx, dy, **kw):
        self.drag(handle, dx, dy, **kw)

    def copy(self):
        self.field.copy_to_clipboard()

    def move_cursor_to(self, x, y):
        """Put the (offscreen) mouse pointer at canvas position (x, y)."""
        QCursor.setPos(self.field.mapToGlobal(QPoint(x, y)))
        self.process_events()

    def paste_at(self, x, y):
        self.move_cursor_to(x, y)
        self.field.paste_from_clipboard()
        self.process_events()

    def delete_selection(self):
        # like SideWidget: the selection observable holds model objects
        sel = list(self.field.selection.get())
        self.controller.remove_nodes_and_branches(sel)
        self.process_events()

    def undo(self):
        self.command_handler.undo()
        self.process_events()

    def redo(self):
        self.command_handler.redo()
        self.process_events()

    # ----------------------------------------------------------------- I/O
    def load(self, path):
        self.io.load_graph(path)
        self.process_events()

    def save(self, path):
        self.io.save_graph(path)

    def normalize_stacking_order(self):
        """
        Make the z-order of the child widgets independent of set iteration
        order (grid < branches < nodes < labels < handles, each sorted by
        id), so that renderings are reproducible between runs.
        """
        self.private("grid_widget").lower()
        items = sorted(self.model_widget_map.items(),
                       key=lambda kv: kv[0].id.int)
        for model_obj, w in items:
            if hasattr(model_obj, "spline1_x"):
                w.raise_()
        for model_obj, w in items:
            if not hasattr(model_obj, "spline1_x"):
                w.raise_()
        for model_obj, lw in sorted(self.model_label_map.items(),
                                    key=lambda kv: kv[0].id.int):
            lw.raise_()
        for handle in self.selected_handles():
            handle.raise_()

    def render(self):
        """Render the GraphField to a QImage (for snapshot tooling)."""
        self.normalize_stacking_order()
        self.process_events()
        return self.field.grab().toImage()

    def close(self):
        self.field.close()
        self.field.deleteLater()
        self.process_events()
