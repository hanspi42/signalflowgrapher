"""
Snapshots of everything that leaves the application or is shown on screen,
in a canonical, order-independent form. Used for golden-file regression
tests (test_golden.py) and for A/B comparison between development steps.

  model_snapshot(h)     model data (ids, coordinates, labels), sorted
  tikz_snapshot(text)   TikZ export with node numbering/order removed
  geometry_snapshot(h)  widget rectangles, branch mid points, label centres
"""
import re

from signalflowgrapher.tests.gui.harness import Harness


def model_snapshot(h: Harness):
    d = h.model.graph.to_dict()
    return {
        "grid_pos": list(h.model.get_grid_position()),
        "nodes": sorted(d["nodes"], key=lambda n: n["id"]),
        "branches": sorted(d["branches"], key=lambda b: b["id"]),
    }


_NODE = re.compile(r"\\node\[Node\] \(N(\d+)\) at \(([^,]+), ([^)]+)\) \{\};")
_NODENAME = re.compile(
    r"\\node\[NodeName\] at \(\$ \(N(\d+)\) \+ \(([^,]+), ([^)]+)\) \$\) "
    r"\{(.*)\};")
_DRAW = re.compile(
    r"\\draw \[->-, Connection, MarkMiddle=(\d+)\] \(N(\d+)\) "
    r"\.\.controls\(([^,]+), ([^)]+)\) and \(([^,]+), ([^)]+)\) "
    r"\.\. \(N(\d+)\);")
_ARROWNAME = re.compile(
    r"\\node\[ArrowName\] at\(\$ \(middle_(\d+)\) \+ \(([^,]+), ([^)]+)\) "
    r"\$\) \{(.*)\};")


def tikz_snapshot(text: str):
    """
    Canonical form of a TikZ export. The exporter numbers nodes and
    branches in set-iteration order (not reproducible between runs), so
    node numbers are replaced by their data and everything is sorted.
    """
    nodes, names, draws, arrows = {}, {}, {}, {}
    for line in text.splitlines():
        for regex, store, conv in (
                (_NODE, nodes, lambda m: [m[2], m[3]]),
                (_NODENAME, names, lambda m: [m[2], m[3], m[4]]),
                (_DRAW, draws,
                 lambda m: [m[2], m[3], m[4], m[5], m[6], m[7]]),
                (_ARROWNAME, arrows, lambda m: [m[2], m[3], m[4]])):
            m = regex.match(line)
            if m:
                store[m[1]] = conv(m)
    node_key = {k: nodes[k] + names.get(k, ["", "", ""]) for k in nodes}
    result_nodes = sorted(node_key.values())
    result_branches = []
    for k, (s, c1x, c1y, c2x, c2y, e) in draws.items():
        result_branches.append({
            "start": node_key[s], "end": node_key[e],
            "controls": [c1x, c1y, c2x, c2y],
            "label": arrows.get(k)})
    result_branches.sort(key=repr)
    return {"nodes": result_nodes, "branches": result_branches,
            "header": [l for l in text.splitlines()
                       if "tikzpicture}[" in l]}


def geometry_snapshot(h: Harness):
    h.process_events()
    ox, oy = h.grid_offset.x(), h.grid_offset.y()
    nodes, branches, labels = {}, {}, {}
    for model_obj, w in h.model_widget_map.items():
        key = model_obj.id.hex
        g = w.geometry()
        entry = {"rect": [g.x(), g.y(), g.width(), g.height()]}
        c = w.get_center()
        entry["center"] = [round(c.x(), 1), round(c.y(), 1)]
        (branches if hasattr(model_obj, "spline1_x") else nodes)[key] = entry
    for model_obj, lw in h.model_label_map.items():
        # label size depends on the installed font, so only the centre
        c = lw.geometry().center()
        labels[model_obj.id.hex] = {
            "center": [lw.x() + lw.width() / 2, lw.y() + lw.height() / 2]}
    return {"grid_offset": [ox, oy], "nodes": nodes, "branches": branches,
            "labels": labels}


def snapshots_close(a, b, tolerance, path=""):
    """
    Compare two nested snapshots; numbers may differ by `tolerance`.
    Returns a list of differences (empty = equal).
    """
    diffs = []
    if isinstance(a, dict) and isinstance(b, dict):
        for k in sorted(set(a) | set(b), key=str):
            if k not in a or k not in b:
                diffs.append("%s/%s: only in %s"
                             % (path, k, "expected" if k in a else "actual"))
            else:
                diffs.extend(snapshots_close(a[k], b[k], tolerance,
                                             "%s/%s" % (path, k)))
    elif isinstance(a, (list, tuple)) and isinstance(b, (list, tuple)):
        if len(a) != len(b):
            diffs.append("%s: length %d != %d" % (path, len(a), len(b)))
        else:
            for i, (x, y) in enumerate(zip(a, b)):
                diffs.extend(snapshots_close(x, y, tolerance,
                                             "%s[%d]" % (path, i)))
    elif isinstance(a, (int, float)) and isinstance(b, (int, float)) \
            and not isinstance(a, bool):
        if abs(a - b) > tolerance:
            diffs.append("%s: %r != %r" % (path, a, b))
    elif a != b:
        diffs.append("%s: %r != %r" % (path, a, b))
    return diffs
