"""
Golden-file regression tests on the example graphs shipped with the
application (resources/examples/**/*.sfg).

For each example the golden file (golden/<name>.json) stores
  * the model after loading (ids, coordinates, label offsets, grid_pos),
  * the canonical TikZ export,
  * the widget geometry on a 1000x700 canvas.

Everything that leaves the application (saved files, TikZ) must stay
identical while the view transform and zoom are introduced; the geometry
at zoom 1 / no pan must stay identical too.

If a change is intended (or the Qt version / fonts change widget
geometry), regenerate the files with
    SFG_UPDATE_GOLDEN=1 python -m pytest src/signalflowgrapher/tests/gui/test_golden.py
and review the diff.
"""
import glob
import json
import os
import tempfile
from importlib import resources
from unittest import TestCase

from signalflowgrapher.tests.gui.harness import Harness
from signalflowgrapher.tests.gui.consistency import check_consistency
from signalflowgrapher.tests.gui.snapshot import (
    geometry_snapshot, model_snapshot, snapshots_close, tikz_snapshot)

HERE = os.path.dirname(__file__)
GOLDEN_DIR = os.path.join(HERE, "golden")
UPDATE = os.environ.get("SFG_UPDATE_GOLDEN") == "1"
GEOMETRY_TOLERANCE = 1.0     # px; widget geometry comes from Qt's stroker


def example_files():
    root = str(resources.files("signalflowgrapher.resources")
               .joinpath("examples"))
    return sorted(glob.glob(os.path.join(root, "*", "*.sfg")))


def example_name(path):
    return os.path.basename(os.path.dirname(path)) + "__" + \
        os.path.splitext(os.path.basename(path))[0]


def build_snapshot(path):
    h = Harness()
    try:
        h.load(path)
        with tempfile.TemporaryDirectory() as tmp:
            tex = os.path.join(tmp, "out.tex")
            h.io.generate_tikz(tex)
            with open(tex, encoding="utf-8") as f:
                tikz = tikz_snapshot(f.read())
        return {"model": model_snapshot(h),
                "tikz": tikz,
                "geometry": geometry_snapshot(h)}
    finally:
        h.close()


class TestGolden(TestCase):
    def test_examples_exist(self):
        self.assertGreaterEqual(len(example_files()), 6)

    def test_examples_match_golden_files(self):
        os.makedirs(GOLDEN_DIR, exist_ok=True)
        for path in example_files():
            name = example_name(path)
            with self.subTest(example=name):
                actual = build_snapshot(path)
                golden_path = os.path.join(GOLDEN_DIR, name + ".json")
                if UPDATE:
                    with open(golden_path, "w", encoding="utf-8") as f:
                        json.dump(actual, f, indent=1, sort_keys=True)
                    continue
                self.assertTrue(os.path.exists(golden_path),
                                "missing golden file %s (run with "
                                "SFG_UPDATE_GOLDEN=1)" % golden_path)
                with open(golden_path, encoding="utf-8") as f:
                    expected = json.load(f)
                actual = json.loads(json.dumps(actual))   # tuples -> lists
                self.assertEqual(expected["model"], actual["model"],
                                 "model differs from golden file")
                self.assertEqual(expected["tikz"], actual["tikz"],
                                 "TikZ export differs from golden file")
                diffs = snapshots_close(expected["geometry"],
                                        actual["geometry"],
                                        GEOMETRY_TOLERANCE)
                self.assertEqual([], diffs[:10],
                                 "widget geometry differs from golden file")

    def test_loaded_examples_are_consistent(self):
        for path in example_files():
            with self.subTest(example=example_name(path)):
                h = Harness()
                try:
                    h.load(path)
                    self.assertEqual([], check_consistency(h))
                finally:
                    h.close()


class TestTikzExport(TestCase):
    def export(self, path):
        h = Harness()
        try:
            h.load(path)
            with tempfile.TemporaryDirectory() as tmp:
                tex = os.path.join(tmp, "out.tex")
                h.io.generate_tikz(tex)
                with open(tex, encoding="utf-8") as f:
                    return f.read()
        finally:
            h.close()

    def test_export_is_byte_identical_between_runs(self):
        """Nodes and branches are numbered in a reproducible order (K6)."""
        for path in example_files():
            with self.subTest(example=example_name(path)):
                self.assertEqual(self.export(path), self.export(path))


class TestRendering(TestCase):
    def render(self, path):
        h = Harness()
        try:
            h.load(path)
            h.field.on_esc_press()
            return h.render()
        finally:
            h.close()

    def test_rendering_is_reproducible_and_not_blank(self):
        path = example_files()[0]
        a, b = self.render(path), self.render(path)
        self.assertEqual(a, b)
        blank = a.copy()
        blank.fill(a.pixelColor(0, 0))
        self.assertNotEqual(blank, a, "rendering is blank")
