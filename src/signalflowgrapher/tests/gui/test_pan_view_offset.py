"""
Tests of step 4 of the V3.0 plan: panning changes the view, not the graph.

Up to step 3 a pan added its distance to the coordinates of every node and
spline point (and to the saved grid position), and the commands corrected
the coordinates of deleted objects. Now the coordinates are world
coordinates that never change by navigation; the view offset moves.
"""
import copy
import json
import os
import tempfile
from unittest import TestCase

import jsonschema
from PySide6.QtCore import QPointF

from signalflowgrapher.io.json import JSONValidator
from signalflowgrapher.model import model as model_module
from signalflowgrapher.model.model import Model
from signalflowgrapher.tests.gui import test_gui_operations as ops
from signalflowgrapher.tests.gui.consistency import check_consistency
from signalflowgrapher.tests.gui.harness import Harness
from signalflowgrapher.tests.gui.test_golden import (
    example_files, example_name)


def write_json(directory, name, data):
    path = os.path.join(directory, name)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f)
    return path


def shifted_like_version_2(data, dx, dy):
    """
    The same graph as a file of V2.0 would describe it after a pan by
    (dx, dy): all coordinates shifted, the shift added to grid_pos.
    """
    data = copy.deepcopy(data)
    for n in data["nodes"]:
        n["x"] += dx
        n["y"] += dy
    for b in data["branches"]:
        b["spline1_x"] += dx
        b["spline1_y"] += dy
        b["spline2_x"] += dx
        b["spline2_y"] += dy
    gx, gy = data.get("grid_pos", (0, 0))
    data["grid_pos"] = [gx + dx, gy + dy]
    return data


class TestPanIsOnlyAView(ops.GuiTestCase):
    def test_the_model_has_no_way_to_move_the_whole_graph(self):
        self.assertFalse(hasattr(Model, "move_graph_relative"))
        self.assertFalse(hasattr(model_module, "GraphMovedEvent"))

    def test_pan_leaves_graph_grid_and_undo_history_alone(self):
        a, b, br = self.make_two_nodes_and_branch()
        self.h.drag_label(br, 20, 20)
        before = ops.coords(self.h)
        history = self.h.command_handler.can_undo.get()
        for dx, dy in ((33, 17), (-500, 300), (0, 0), (7, -900)):
            self.h.pan(dx, dy)
            self.assertEqual(before, ops.coords(self.h))
            self.assertEqual(history, self.h.command_handler.can_undo.get())
            self.ok("pan %s %s" % (dx, dy))

    def test_pan_adds_up_exactly(self):
        self.make_two_nodes_and_branch()
        self.h.pan(33, 17, steps=7)
        self.h.pan(-50, 40, steps=3)
        self.h.pan(1, 1, steps=1)
        self.assertEqual(QPointF(-16, 58), self.h.view.offset)

    def test_undo_and_redo_do_not_care_about_panning_in_between(self):
        a, b, br = self.make_two_nodes_and_branch()
        h = self.h
        before_move = ops.coords(h)
        h.drag_node(b, 60, 30)
        after_move = ops.coords(h)
        h.pan(-120, 80)
        h.undo()
        self.assertEqual(before_move, ops.coords(h))
        self.ok("undo move after pan")
        h.pan(200, -100)
        h.redo()
        self.assertEqual(after_move, ops.coords(h))
        self.ok("redo move after pan")
        h.select(b)
        h.delete_selection()
        h.pan(11, 22)
        h.undo()
        self.assertEqual(after_move, ops.coords(h))
        h.pan(-11, -22)
        h.redo()
        h.pan(5, 5)
        h.undo()
        self.assertEqual(after_move, ops.coords(h))
        self.ok("delete, pan, undo, redo")

    def test_paste_and_new_nodes_use_the_world_grid_after_pan(self):
        a, b, br = self.make_two_nodes_and_branch()
        self.h.pan(13, 7)
        n = self.h.double_click(300, 300)
        self.assertEqual((0, 0), (n.x % 30, n.y % 30))
        self.h.select(a, b, br)
        self.h.copy()
        self.h.paste_at(500, 400)
        for node in self.h.nodes:
            self.assertEqual((0, 0), (node.x % 30, node.y % 30))
        self.ok("create and paste after pan")


class TestPanLooksLikeTheOldPan(TestCase):
    """
    The picture of a pan by (dx, dy) must be exactly the picture of the
    graph that a pan of V2.0 produced: the same graph with all coordinates
    shifted by (dx, dy), and the shift added to grid_pos. Rendered pixel by
    pixel, including grid lines, curves and labels.
    """

    def render(self, path, view_offset=None):
        h = Harness(900, 500)
        try:
            h.load(path)
            h.field.on_esc_press()      # loading leaves a node selected
            if view_offset is not None:
                h.set_view(1.0, view_offset)
            return h.render()
        finally:
            h.close()

    def test_new_pan_and_old_pan_give_the_same_picture(self):
        for example in example_files()[:4]:
            with open(example, encoding="utf-8") as f:
                data = json.load(f)
            for dx, dy in ((120, -60), (37, 21), (-85, 130), (0, 0)):
                with self.subTest(example=example_name(example), pan=(dx, dy)):
                    with tempfile.TemporaryDirectory() as tmp:
                        old_style = write_json(
                            tmp, "old.sfg", shifted_like_version_2(data, dx, dy))
                        old = self.render(old_style)
                        new = self.render(example, (dx, dy))
                    self.assertEqual(old, new)


class TestViewIsRememberedInTheFile(ops.GuiTestCase):
    def save_and_read(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = os.path.join(tmp, "g.sfg")
            self.h.save(path)
            with open(path, encoding="utf-8") as f:
                return json.load(f)

    def test_model_follows_the_view(self):
        self.assertEqual((0, 0), self.h.model.get_view_origin())
        self.h.pan(40, -25)
        self.assertEqual((-40, 25), self.h.model.get_view_origin())
        self.h.set_view(0.5, (37, -12))
        self.assertEqual((-74, 24), self.h.model.get_view_origin())
        self.ok("view origin follows")

    def test_file_contains_view_origin_and_constant_grid_position(self):
        self.make_two_nodes_and_branch()
        self.h.pan(40, -25)
        self.h.pan(-3, 3)
        data = self.save_and_read()
        self.assertEqual([-37, 22], data["view_origin"])
        self.assertEqual([0, 0], data["grid_pos"])
        self.assertEqual("3.0", data["version"])

    def test_reopening_shows_the_same_part_of_the_graph(self):
        a, b, br = self.make_two_nodes_and_branch()
        self.h.pan(-140, 85)
        centres = {o.id: self.h.widget_of(o).get_center() for o in (a, b)}
        with tempfile.TemporaryDirectory() as tmp:
            path = os.path.join(tmp, "g.sfg")
            self.h.save(path)
            h2 = Harness()
            try:
                h2.load(path)
                self.assertEqual(QPointF(-140, 85), h2.view.offset)
                self.assertEqual(1.0, h2.view.zoom)
                for node in h2.nodes:
                    self.assertEqual(centres[node.id],
                                     h2.widget_of(node).get_center())
                self.assertEqual([], check_consistency(h2))
            finally:
                h2.close()

    def test_zoom_is_not_saved_the_file_opens_at_100_percent(self):
        self.make_two_nodes_and_branch()
        self.h.set_view(0.25, (100, 50))
        data = self.save_and_read()
        self.assertEqual([-400, -200], data["view_origin"])
        self.assertNotIn("zoom", json.dumps(data))
        with tempfile.TemporaryDirectory() as tmp:
            path = os.path.join(tmp, "g.sfg")
            self.h.save(path)
            h2 = Harness()
            try:
                h2.load(path)
                self.assertEqual(1.0, h2.view.zoom)
                # same part of the graph at the top left corner
                self.assertEqual(QPointF(-400, -200),
                                 h2.view.to_world(QPointF(0, 0)))
            finally:
                h2.close()

    def test_files_without_view_origin_open_from_the_origin(self):
        """All files of V2.0 and of the steps 1 to 3."""
        with open(example_files()[0], encoding="utf-8") as f:
            data = json.load(f)
        self.assertNotIn("view_origin", data)
        self.h.pan(300, 300)
        self.h.set_view(0.5)
        with tempfile.TemporaryDirectory() as tmp:
            self.h.load(write_json(tmp, "old.sfg", data))
        self.assertEqual(QPointF(0, 0), self.h.view.offset)
        self.assertEqual(1.0, self.h.view.zoom)
        self.assertEqual(tuple(data["grid_pos"]),
                         tuple(self.h.model.get_grid_position()))
        self.ok("load a file without view origin")

    def test_loading_replaces_the_current_view(self):
        self.make_two_nodes_and_branch()
        self.h.pan(70, 30)
        with tempfile.TemporaryDirectory() as tmp:
            path = os.path.join(tmp, "g.sfg")
            self.h.save(path)
            self.h.pan(500, 500)
            self.h.set_view(0.3)
            self.h.load(path)
        self.assertEqual(QPointF(70, 30), self.h.view.offset)
        self.assertEqual(1.0, self.h.view.zoom)
        self.ok("load replaces the view")

    def test_new_graph_starts_at_the_origin(self):
        # a graph that has a grid position other than (0, 0), like every
        # file that was saved by a version before step 4
        with open(example_files()[0], encoding="utf-8") as f:
            data = shifted_like_version_2(json.load(f), 17, 44)
        with tempfile.TemporaryDirectory() as tmp:
            self.h.load(write_json(tmp, "old.sfg", data))
        self.assertNotEqual((0, 0), tuple(self.h.model.get_grid_position()))
        self.h.pan(70, 30)
        self.h.set_view(0.5)
        self.h.io.new_graph()
        self.h.process_events()
        self.assertEqual(QPointF(0, 0), self.h.view.offset)
        self.assertEqual(1.0, self.h.view.zoom)
        self.assertEqual((0, 0), tuple(self.h.model.get_grid_position()))
        self.assertEqual((0, 0), tuple(self.h.model.get_view_origin()))
        self.ok("new graph")

    def test_files_of_the_version_before_this_step_open_as_they_did(self):
        """
        A file that was saved after panning in step 3 or V2.0: shifted
        coordinates and the accumulated pan as grid_pos. It is shown with
        the grid lines where the old program drew them.
        """
        with open(example_files()[0], encoding="utf-8") as f:
            data = json.load(f)
        old = shifted_like_version_2(data, 17, 44)
        with tempfile.TemporaryDirectory() as tmp:
            self.h.load(write_json(tmp, "old.sfg", old))
        gx, gy = old["grid_pos"]
        grid = self.h.private("fixed_grid")
        self.assertEqual((gx % 30, gy % 30),
                         (grid.offset.x(), grid.offset.y()))
        self.ok("file with accumulated pan")


class TestViewOriginInTheSchema(TestCase):
    def validate(self, view_origin):
        with open(example_files()[0], encoding="utf-8") as f:
            data = json.load(f)
        data["view_origin"] = view_origin
        JSONValidator().validate_json(data)

    def test_numbers_are_accepted(self):
        self.validate([0, 0])
        self.validate([-74, 24])
        self.validate([12.5, -3.25])

    def test_everything_else_is_rejected(self):
        for bad in ([1], [1, 2, 3], ["a", 1], "x", None, {"x": 1}):
            with self.subTest(view_origin=bad):
                with self.assertRaises(jsonschema.exceptions.ValidationError):
                    self.validate(bad)

    def test_float_view_origin_loads_and_is_shown(self):
        with open(example_files()[0], encoding="utf-8") as f:
            data = json.load(f)
        data["view_origin"] = [12.5, -3.25]
        h = Harness()
        try:
            with tempfile.TemporaryDirectory() as tmp:
                h.load(write_json(tmp, "f.sfg", data))
            self.assertEqual(QPointF(-12.5, 3.25), h.view.offset)
            self.assertEqual([], check_consistency(h))
        finally:
            h.close()
