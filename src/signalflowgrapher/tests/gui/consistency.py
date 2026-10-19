"""
Consistency checker: compares everything the GUI shows with the model.

Written for the V3.0 refactoring (DEVDOCU.md, step 0). It encodes the
invariants that hold *today* between model coordinates and widget state:

  * node widget centre == the node's world position mapped to the screen
  * branch widget caches == the branch's points mapped to the screen
  * branch widget mid point == Bezier mid point of the curve on the screen
  * label widget centre == owner centre + label offset * zoom
  * everything that is drawn has the size of zoom 100% times the zoom:
    node widget size, label font size, branch widget covers its curve
  * visible spline handles == model splines (knob mirrored about the node)
  * grid offset state agrees everywhere (model, grid widgets)
  * the view origin that the model remembers for the file is the world
    position at the top left corner of the window
  * every model object has exactly one widget and one label widget
  * the model graph itself is topologically consistent

"mapped to the screen" is `harness.view.to_screen_point` (screen = zoom *
world + offset, rounded down to a pixel), so the checker is valid for every
zoom and offset. At zoom 1 and offset (0, 0) it checks the situation of
V2.0.

Usage:
    problems = check_consistency(harness)
    assert not problems, "\n".join(problems)
"""
from PySide6.QtCore import QPoint, QPointF, QRectF
from PySide6.QtGui import QPainterPath

from signalflowgrapher.gui import glyphs
from signalflowgrapher.gui.grid import FixedGrid, GRID_SIZE
from signalflowgrapher.tests.gui.harness import Harness, _private

LABEL_TOLERANCE = 1.5   # label widgets are placed with int() truncation
MIDPOINT_TOLERANCE = 1.0


def _close(a, b, tol):
    return abs(a.x() - b.x()) <= tol and abs(a.y() - b.y()) <= tol


def screen_point(h: Harness, x, y) -> QPoint:
    """Screen pixel of a model position, through the view transform."""
    return h.view.to_screen_point(QPointF(x, y))


def expected_branch_points(h: Harness, branch):
    return {
        "start": screen_point(h, branch.start.x, branch.start.y),
        "end": screen_point(h, branch.end.x, branch.end.y),
        "spline1": screen_point(h, branch.spline1_x, branch.spline1_y),
        "spline2": screen_point(h, branch.spline2_x, branch.spline2_y),
    }


def expected_branch_path(h: Harness, branch) -> QPainterPath:
    """Bezier path of a model branch on the screen, as the widget builds it."""
    p = expected_branch_points(h, branch)
    path = QPainterPath()
    path.moveTo(p["start"])
    path.cubicTo(p["spline1"], p["spline2"], p["end"])
    return path


def expected_branch_middle(h: Harness, branch) -> QPointF:
    path = expected_branch_path(h, branch)
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
        if not isinstance(node.label_dx, int) \
                or not isinstance(node.label_dy, int):
            problems.append("node %s has a non-integer label offset (%r, %r)"
                            % (node.id.hex, node.label_dx, node.label_dy))
        c = w.get_center()
        if not _close(c, screen_point(h, node.x, node.y), 0):
            problems.append("node %s: widget centre (%s, %s) != model "
                            "(%s, %s)" % (node.id.hex, c.x(), c.y(),
                                          node.x, node.y))
        if w.parent() is not h.field:
            problems.append("node widget %s has the wrong parent"
                            % node.id.hex)
        size = 2 * glyphs.node_half_size(h.view.zoom)
        if (w.width(), w.height()) != (size, size):
            problems.append("node widget %s has the size %sx%s, expected "
                            "%sx%s for zoom %s" % (node.id.hex, w.width(),
                                                   w.height(), size, size,
                                                   h.view.zoom))
    return problems


def check_branches(h: Harness):
    problems = []
    for branch in h.model.graph.branches:
        w = h.model_widget_map.get(branch)
        if w is None:
            continue
        cls = "BranchWidget"
        cached = expected_branch_points(h, branch)
        for name, expected in cached.items():
            actual = _private(w, cls, name)
            if actual != expected:
                problems.append("branch %s: cached %s (%s, %s) != model "
                                "(%s, %s)" % (branch.id.hex, name,
                                              actual.x(), actual.y(),
                                              expected.x(), expected.y()))
        mid = w.get_center()
        exp_mid = expected_branch_middle(h, branch)
        if not _close(mid, exp_mid, MIDPOINT_TOLERANCE):
            problems.append("branch %s: widget mid point (%.1f, %.1f) != "
                            "Bezier mid point of model (%.1f, %.1f)"
                            % (branch.id.hex, mid.x(), mid.y(),
                               exp_mid.x(), exp_mid.y()))
        # The widget must contain the whole curve (and its arrow) ...
        geo = w.geometry()
        curve = expected_branch_path(h, branch).boundingRect()
        # (compared edge by edge: QRectF.contains is false for a rect
        # without height or width, e.g. a straight horizontal branch)
        outer = QRectF(geo.adjusted(-1, -1, 1, 1))
        if not (outer.left() <= curve.left()
                and outer.top() <= curve.top()
                and outer.right() >= curve.right()
                and outer.bottom() >= curve.bottom()):
            problems.append("branch %s: widget geometry %s does not cover "
                            "the curve %s" % (branch.id.hex, geo, curve))
        # ... and has been built for the current zoom (the size of the arrow
        # follows from it)
        if w._BranchWidget__zoom != h.view.zoom:
            problems.append("branch %s was built for zoom %s, the zoom is %s"
                            % (branch.id.hex, w._BranchWidget__zoom,
                               h.view.zoom))
    return problems


def check_labels(h: Harness):
    problems = []
    for obj, lw in h.model_label_map.items():
        owner_widget = h.model_widget_map.get(obj)
        if owner_widget is None:
            continue
        c = owner_widget.get_center()
        centre = QPointF(lw.x() + lw.width() / 2, lw.y() + lw.height() / 2)
        zoom = h.view.zoom
        font_points = lw.font().pointSizeF()
        if abs(font_points - glyphs.LABEL_FONT_POINTS * zoom) > 0.01:
            problems.append("label of %s: font size %.2f pt, expected %.2f"
                            % (obj.id.hex, font_points,
                               glyphs.LABEL_FONT_POINTS * zoom))
        expected = QPointF(c.x() + obj.label_dx * zoom,
                           c.y() + obj.label_dy * zoom)
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
        origin = screen_point(h, node.x, node.y)
        spl = screen_point(h, spline[0], spline[1])
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


def check_view_origin(h: Harness):
    """The model remembers the part of the graph that is shown (for saving)."""
    problems = []
    expected = h.view.to_world(QPointF(0, 0))
    ox, oy = h.model.get_view_origin()
    if abs(ox - expected.x()) > 0.51 or abs(oy - expected.y()) > 0.51:
        problems.append("model view origin (%s, %s) != world position at the "
                        "top left of the window (%.1f, %.1f)"
                        % (ox, oy, expected.x(), expected.y()))
    return problems


def check_grid(h: Harness):
    """
    The grid position belongs to the graph and does not change with pan or
    zoom. The grid used for snapping and the grid drawn on the canvas must
    both have their lines at (grid position mod grid size) in world
    coordinates.
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
              check_labels, check_handles, check_grid, check_view_origin)


def check_consistency(h: Harness):
    """Run every check; returns a list of human-readable problems."""
    h.process_events()
    problems = []
    for check in ALL_CHECKS:
        problems.extend(check(h))
    return problems


def assert_consistent(test_case, h: Harness, context=""):
    problems = check_consistency(h)
    if problems:
        test_case.fail("GUI/model inconsistency%s:\n  %s"
                       % ((" after " + context) if context else "",
                          "\n  ".join(problems)))
