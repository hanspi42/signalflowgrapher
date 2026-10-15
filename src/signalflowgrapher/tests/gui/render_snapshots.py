"""
Render the example graphs (and a few edited states) to PNG files, and
compare two rendering directories pixel by pixel.

    python -m signalflowgrapher.tests.gui.render_snapshots render OUTDIR
    python -m signalflowgrapher.tests.gui.render_snapshots compare DIR_A DIR_B

Typical use in the V3.0 plan: render a baseline before a step, render again
after it and compare. At zoom 1 the images must be identical; for the
pixel-exact steps (2, 3, 4) any difference is a regression. Rendering uses
the offscreen Qt platform, so results are only comparable on the same
machine / Qt / font setup.
"""
import os
import sys

from signalflowgrapher.tests.gui.harness import Harness
from signalflowgrapher.tests.gui.test_golden import (
    example_files, example_name)


def scenes():
    """Yield (name, harness) for every scene to render."""
    for path in example_files():
        h = Harness()
        h.load(path)
        h.field.on_esc_press()     # loading leaves an arbitrary node selected
        yield example_name(path), h
        h.close()
    # edited states exercising pan, handles and selection
    path = example_files()[-1]
    h = Harness()
    h.load(path)
    h.field.on_esc_press()
    h.pan(120, -60)
    yield "edited__panned", h
    node = sorted(h.nodes, key=lambda n: n.id.int)[0]
    h.select(node)
    yield "edited__node_selected", h
    branch = sorted(h.branches, key=lambda b: b.id.int)[0]
    h.select_branch(branch)
    yield "edited__branch_with_handles", h
    h.close()


def render(outdir):
    os.makedirs(outdir, exist_ok=True)
    for name, h in scenes():
        img = h.render()
        target = os.path.join(outdir, name + ".png")
        img.save(target)
        print("wrote", target, img.width(), "x", img.height())


def compare(dir_a, dir_b):
    from PySide6.QtGui import QImage
    names = sorted(set(os.listdir(dir_a)) | set(os.listdir(dir_b)))
    different = 0
    for name in names:
        pa, pb = os.path.join(dir_a, name), os.path.join(dir_b, name)
        if not (os.path.exists(pa) and os.path.exists(pb)):
            print("MISSING  ", name)
            different += 1
            continue
        a, b = QImage(pa), QImage(pb)
        if a.size() != b.size():
            print("SIZE     ", name, a.size(), b.size())
            different += 1
            continue
        count = sum(1 for y in range(a.height()) for x in range(a.width())
                    if a.pixel(x, y) != b.pixel(x, y))
        print("%-9s" % ("identical" if count == 0 else "DIFFERENT"), name,
              "" if count == 0 else "(%d pixels)" % count)
        different += count != 0
    return different


def main(argv):
    if len(argv) == 3 and argv[1] == "render":
        render(argv[2])
        return 0
    if len(argv) == 4 and argv[1] == "compare":
        return 1 if compare(argv[2], argv[3]) else 0
    print(__doc__)
    return 2


if __name__ == "__main__":
    sys.exit(main(sys.argv))
