"""
A broad scenario through the GUI code that records every warning and exits
with an error if the application code used a deprecated function, e.g.
    python -m signalflowgrapher.tests.gui.deprecation_scenario
Used by test_deprecations.py. The application modules are imported inside
the recording block, so warnings that are only issued at import time are
found as well.
"""
import os
import sys
import tempfile
import warnings



def scenario():
    from PySide6.QtCore import Qt
    from signalflowgrapher.tests.gui.harness import Harness
    from signalflowgrapher.tests.gui.test_golden import example_files

    h = Harness()
    a = h.double_click(120, 120)
    b = h.double_click(420, 240)
    c = h.double_click(270, 420)
    ab = h.ctrl_click_branch(a, b)
    h.ctrl_click_branch(b, c)
    h.select(c)
    h.click(h.widget_of(c), Qt.ControlModifier)          # self loop
    h.drag_node(b, 60, 30)                               # node drag
    h.drag_label(ab, 20, 20)                             # label drag
    h.drag_label(a, -30, 30)
    h.drag_handle(h.select_branch(ab)[0], 30, -30)       # handle drag
    h.pan(40, -25)                                       # pan
    h.field.center_graph()
    h.select(a, b, ab)
    h.copy()
    h.paste_at(500, 400)
    h.undo()
    h.redo()
    h.select(c)
    h.delete_selection()
    h.undo()
    with tempfile.TemporaryDirectory() as tmp:
        h.save(os.path.join(tmp, "g.sfg"))
        h.io.generate_tikz(os.path.join(tmp, "g.tex"))
    h.load(example_files()[0])
    h.render()
    h.close()
    print("scenario finished")


def main():
    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always")
        scenario()
    mine = [w for w in caught
            if issubclass(w.category, DeprecationWarning)
            and "signalflowgrapher" in w.filename]
    for w in mine:
        print("%s:%s: %s" % (w.filename, w.lineno, w.message))
    print("%d deprecation warning(s) from the application" % len(mine))
    return 1 if mine else 0


if __name__ == "__main__":
    sys.exit(main())
