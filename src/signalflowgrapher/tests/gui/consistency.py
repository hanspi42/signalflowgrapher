"""
Consistency checker: compares everything the GUI shows with the model.

Written for the V3.0 refactoring (DEVDOCU.md, step 0). It encodes the
invariants that hold *today* between model coordinates and widget state:

  * node widget centre == node (x, y)
  * branch widget caches == int() of the model's end points / splines
  * branch widget mid point == Bezier mid point of the model's curve
  * label widget centre == owner centre + (label_dx, label_dy)
  * visible spline handles == model splines (knob mirrored about the node)
  * grid offset state agrees everywhere (model, GraphField, grid widgets)
  * every model object has exactly one widget and one label widget
  * the model graph itself is topologically consistent

After the refactoring (steps 2-5) the checker is adapted *once* to go
through the ViewTransform (screen = z * world + t); the identity case
(z = 1, t = 0) must keep passing with the checker as it is today.

Usage:
    problems = check_consistency(harness)
    assert not problems, "\n".join(problems)
"""
from PySide6.QtCore import QPoint, QPointF
from PySide6.QtGui import QPainterPath

from signalflowgrapher.gui.grid import FixedGrid, GRID_SIZE
from signalflowgrapher.tests.gui.harness import Harness, _private

LABEL_TOLERANCE = 1.5   # label widgets are placed with int() truncation
MIDPOINT_TOLERANCE = 1.0


def _pt(p) -> QPoint:
    return QPoint(int(p.x()), int(p.y()))


def _close(a, b, tol):
    return abs(a.x() - b.x()) <= tol and abs(a.y() - b.y()) <= tol


def expected_branch_path(branch) -> QPainterPath:
    """Absolute Bezier path of a model branch, as the widget builds it."""
    path = QPainterPath()
    path.moveTo(QPoint(int(branch.start.x), int(branch.start.y)))
    path.cubicTo(QPoint(int(branch.spline1_x), int(branch.spline1_y)),
                 QPoint(int(branch.spline2_x), int(branch.spline2_y)),
                 QPoint(int(branch.end.x), int(branch.end.y)))
    return path


def expected_branch_middle(branch) -> QPointF:
    path = expected_branch_path(branch)
    return path.pointAtPercent(path.percentAtLength(path.length() / 2))


def check_model(h: Harness):
    """Topological sanity of the model graph."""
    problems = []
    graph = h.model.graph
    nodes = set(graph.nodes)
    for b in graph.branches:
        if b.start not in nodes or b.end not in nodes:
            problems.append("branch %s has an end node outside the graph"
                            % b.id.hex)
        if b not in b.start.outgoing:
            problems.append("branch %s missing in start.outgoing" % b.id.hex)
        if b not in b.end.ingoing:
            problems.append("branch %s missing in end.ingoing" % b.id.hex)
    for n in nodes:
        for b in n.outgoing:
            if b not in graph.branches:
                problems.append("node %s has stale outgoing branch" % n.id.hex)
        for b in n.ingoing:
            if b not in graph.branches:
                problems.append("node %s has stale ingoing branch" % n.id.hex)
    return problems


def check_widget_sets(h: Harness):
    problems = []
    graph = h.model.graph
    expected = set(graph.nodes) | set(graph.branches)
    widget_map = h.model_widget_map
    label_map = h.model_label_map
    if set(widget_map.keys()) != expected:
        problems.append("model->widget map differs from graph content "
                        "(%d widgets, %d model objects)"
                        % (len(widget_map), len(expected)))
    if set(label_map.keys()) != expected:
        problems.append("model->label map differs from graph content "
                        "(%d labels, %d model objects)"
                        % (len(label_map), len(expected)))
    inverse = h.private("widget_model_map")
    if len(inverse) != len(widget_map):
        problems.append("widget->model map has a different size")
    label_inverse = h.private("label_model_map")
    if len(label_inverse) != len(label_map):
        problems.append("label->model map has a different size")
    return problems


def check_nodes(h: Harness):
    problems = []
    for node in h.model.graph.nodes:
        w = h.model_widget_map.get(node)
        if w is None:
            continue
        if not isinstance(node.x, int) or not isinstance(node.y, int):
            problems.append("node %s has non-integer coordinates (%r, %r)"
                            % (node.id.hex, node.x, node.y))
        c = w.get_center()
        if not _close(c, QPoint(int(node.x), int(node.y)), 0):
            problems.append("node %s: widget centre (%s, %s) != model "
                            "(%s, %s)" % (node.id.hex, c.x(), c.y(),
                                          node.x, node.y))
        if w.parent() is not h.field:
            problems.append("node widget %s has the wrong parent"
                            % node.id.hex)
    return problems


def check_branches(h: Harness):
    problems = []
    for branch in h.model.graph.branches:
        w = h.model_widget_map.get(branch)
        if w is None:
            continue
        cls = "BranchWidget"
        cached = {
            "start": QPoint(int(branch.start.x), int(branch.start.y)),
            "end": QPoint(int(branch.end.x), int(branch.end.y)),
            "spline1": QPoint(int(branch.spline1_x), int(branch.spline1_y)),
            "spline2": QPoint(int(branch.spline2_x), int(branch.spline2_y)),
        }
        for name, expected in cached.items():
            actual = _private(w, cls, name)
            if actual != expected:
                problems.append("branch %s: cached %s (%s, %s) != model "
                                "(%s, %s)" % (branch.id.hex, name,
                                              actual.x(), actual.y(),
                                              expected.x(), expected.y()))
        mid = w.get_center()
        exp_mid = expected_branch_middle(branch)
        if not _close(mid, exp_mid, MIDPOINT_TOLERANCE):
            problems.append("branch %s: widget mid point (%.1f, %.1f) != "
                            "Bezier mid point of model (%.1f, %.1f)"
                            % (branch.id.hex, mid.x(), mid.y(),
                               exp_mid.x(), exp_mid.y()))
        # The widget must at least contain its start and end node centre.
        geo = w.geometry()
        for name in ("start", "end"):
            p = cached[name]
            if not geo.adjusted(-1, -1, 1, 1).contains(p):
                problems.append("branch %s: widget geometry does not cover "
                                "its %s point" % (branch.id.hex, name))
    return problems


# Known defects that can be tolerated explicitly by a test (see
# DEVDOCU.md, "Known issues found by the safety net"). Every entry must be
# removed from here when the defect is fixed.
STALE_BRANCH_LABELS = "stale_branch_labels"


def check_labels(h: Harness, known_issues=()):
    problems = []
    for obj, lw in h.model_label_map.items():
        owner_widget = h.model_widget_map.get(obj)
        if owner_widget is None:
            continue
        if STALE_BRANCH_LABELS in known_issues and \
                obj in h.model.graph.branches:
            continue
        c = owner_widget.get_center()
        centre = QPointF(lw.x() + lw.width() / 2, lw.y() + lw.height() / 2)
        expected = QPointF(c.x() + obj.label_dx, c.y() + obj.label_dy)
        if not _close(centre, expected, LABEL_TOLERANCE):
            problems.append("label of %s: centre (%.1f, %.1f) != owner "
                            "centre + offset (%.1f, %.1f)"
                            % (obj.id.hex, centre.x(), centre.y(),
                               expected.x(), expected.y()))
    return problems


def check_handles(h: Harness):
    problems = []
    for hw in h.selected_handles():
        branch = hw.get_branch()
        if hw.__class__.__name__ == "Spline1HandleWidget":
            node, spline = branch.start, (branch.spline1_x, branch.spline1_y)
        else:
            node, spline = branch.end, (branch.spline2_x, branch.spline2_y)
        origin = QPoint(int(node.x), int(node.y))
        spl = QPoint(int(spline[0]), int(spline[1]))
        if hw._origin_abs != origin:
            problems.append("handle origin (%s, %s) != node (%s, %s)"
                            % (hw._origin_abs.x(), hw._origin_abs.y(),
                               origin.x(), origin.y()))
        if hw._spline_abs != spl:
            problems.append("handle spline (%s, %s) != model (%s, %s)"
                            % (hw._spline_abs.x(), hw._spline_abs.y(),
                               spl.x(), spl.y()))
        knob = hw.get_center()
        expected = QPointF(2 * origin.x() - spl.x(), 2 * origin.y() - spl.y())
        if not _close(knob, expected, MIDPOINT_TOLERANCE):
            problems.append("handle knob (%.1f, %.1f) is not the mirror of "
                            "the spline about the node (%.1f, %.1f)"
                            % (knob.x(), knob.y(),
                               expected.x(), expected.y()))
    return problems


def check_grid(h: Harness):
    """
    The pan is owned by the model; the grid used for snapping and the grid
    drawn on the canvas must both show the lines at (pan mod grid size).
    """
    problems = []
    gx, gy = h.model.get_grid_position()
    size = GRID_SIZE
    expected = (gx % size, gy % size)
    for attr in ("grid_offset", "grid_size"):
        if hasattr(h.field, "_GraphField__" + attr):
            problems.append("GraphField keeps its own copy of the pan "
                            "state (%s)" % attr)
    grid_widget = h.private("grid_widget")
    gw_offset = grid_widget.offset
    if (gw_offset.x(), gw_offset.y()) != expected:
        problems.append("FixedGridWidget offset (%s, %s) != pan mod %s "
                        "(%s, %s)" % (gw_offset.x(), gw_offset.y(), size,
                                      expected[0], expected[1]))
    for name in ("fixed_grid", "grid"):
        grid = h.private(name)
        if isinstance(grid, FixedGrid):
            g_offset = grid.offset
            if (g_offset.x(), g_offset.y()) != expected:
                problems.append("FixedGrid offset (%s, %s) != pan mod %s "
                                "(%s, %s)" % (g_offset.x(), g_offset.y(),
                                              size, expected[0], expected[1]))
    return problems


ALL_CHECKS = (check_model, check_widget_sets, check_nodes, check_branches,
              check_labels, check_handles, check_grid)


def check_consistency(h: Harness, known_issues=()):
    """
    Run every check; returns a list of human-readable problems.

    known_issues: names of documented defects to tolerate, e.g.
    (STALE_BRANCH_LABELS,). Default: tolerate nothing.
    """
    h.process_events()
    problems = []
    for check in ALL_CHECKS:
        if check is check_labels:
            problems.extend(check(h, known_issues))
        else:
            problems.extend(check(h))
    return problems


def assert_consistent(test_case, h: Harness, context=""):
    problems = check_consistency(h)
    if problems:
        test_case.fail("GUI/model inconsistency%s:\n  %s"
                       % ((" after " + context) if context else "",
                          "\n  ".join(problems)))
