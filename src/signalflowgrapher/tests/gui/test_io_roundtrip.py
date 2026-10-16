"""
File format tests: load/save round trips, backward compatibility and the
JSON schema as it is today. Zoom must never change what is written to disk.
"""
import copy
import json
import os
import tempfile
from unittest import TestCase

import jsonschema

from signalflowgrapher.io.json import FILE_FORMAT_VERSION, JSONValidator
from signalflowgrapher.tests.gui.harness import Harness
from signalflowgrapher.tests.gui.consistency import check_consistency
from signalflowgrapher.tests.gui.snapshot import model_snapshot
from signalflowgrapher.tests.gui.test_golden import example_files, \
    example_name


def normalized(d):
    d = copy.deepcopy(d)
    d.pop("version", None)      # files are written with the current version
    d["nodes"].sort(key=lambda n: n["id"])
    d["branches"].sort(key=lambda b: b["id"])
    return d


class TestRoundTrip(TestCase):
    def test_load_save_is_lossless_for_all_examples(self):
        for path in example_files():
            with self.subTest(example=example_name(path)):
                with open(path, encoding="utf-8") as f:
                    original = json.load(f)
                h = Harness()
                try:
                    h.load(path)
                    with tempfile.TemporaryDirectory() as tmp:
                        out = os.path.join(tmp, "out.sfg")
                        h.save(out)
                        with open(out, encoding="utf-8") as f:
                            saved = json.load(f)
                    self.assertEqual(normalized(original), normalized(saved))
                finally:
                    h.close()

    def test_double_roundtrip_keeps_model_snapshot(self):
        for path in example_files():
            with self.subTest(example=example_name(path)):
                h1, h2 = Harness(), Harness()
                try:
                    h1.load(path)
                    with tempfile.TemporaryDirectory() as tmp:
                        out = os.path.join(tmp, "out.sfg")
                        h1.save(out)
                        h2.load(out)
                    self.assertEqual(model_snapshot(h1), model_snapshot(h2))
                    self.assertEqual([], check_consistency(h2))
                finally:
                    h1.close()
                    h2.close()

    def test_grid_position_is_restored(self):
        path = example_files()[0]
        with open(path, encoding="utf-8") as f:
            expected = tuple(json.load(f)["grid_pos"])
        h = Harness()
        try:
            h.load(path)
            self.assertEqual(expected, tuple(h.model.get_grid_position()))
            self.assertEqual(expected,
                             (h.grid_offset.x(), h.grid_offset.y()))
        finally:
            h.close()

    def test_old_files_without_grid_pos_and_version_load(self):
        with open(example_files()[0], encoding="utf-8") as f:
            data = json.load(f)
        del data["grid_pos"]
        del data["version"]
        h = Harness()
        try:
            with tempfile.TemporaryDirectory() as tmp:
                p = os.path.join(tmp, "old.sfg")
                with open(p, "w", encoding="utf-8") as f:
                    json.dump(data, f)
                h.load(p)
            self.assertEqual((0, 0), tuple(h.model.get_grid_position()))
            self.assertEqual(len(data["nodes"]), len(h.nodes))
            self.assertEqual([], check_consistency(h))
        finally:
            h.close()

    def test_loading_replaces_previous_graph(self):
        paths = example_files()
        h = Harness()
        try:
            h.load(paths[0])
            h.load(paths[1])
            with open(paths[1], encoding="utf-8") as f:
                self.assertEqual(len(json.load(f)["nodes"]), len(h.nodes))
            self.assertEqual([], check_consistency(h))
        finally:
            h.close()

    def test_undo_stack_is_reset_by_load_and_save(self):
        h = Harness()
        try:
            h.double_click(100, 100)
            self.assertTrue(h.command_handler.can_undo.get())
            with tempfile.TemporaryDirectory() as tmp:
                h.save(os.path.join(tmp, "x.sfg"))
            self.assertFalse(h.command_handler.can_undo.get())
        finally:
            h.close()


REJECTED = jsonschema.exceptions.ValidationError


class TestSchemaToday(TestCase):
    """The schema as implemented today; documents what must stay valid."""

    def load_text(self, data):
        h = Harness()
        try:
            with tempfile.TemporaryDirectory() as tmp:
                p = os.path.join(tmp, "x.sfg")
                with open(p, "w", encoding="utf-8") as f:
                    json.dump(data, f)
                h.load(p)
            return h
        except Exception:
            h.close()
            raise

    def base(self):
        with open(example_files()[0], encoding="utf-8") as f:
            return json.load(f)

    def test_non_integer_node_coordinate_is_rejected(self):
        data = self.base()
        data["nodes"][0]["x"] = 12.5
        with self.assertRaises(REJECTED):
            self.load_text(data)

    def test_non_integer_node_label_offset_is_rejected(self):
        data = self.base()
        data["nodes"][0]["label_dy"] = 30.5
        with self.assertRaises(REJECTED):
            self.load_text(data)

    def test_float_branch_values_are_accepted(self):
        data = self.base()
        data["branches"][0]["spline1_x"] = 123.456
        data["branches"][0]["label_dx"] = -3.25
        h = self.load_text(data)
        try:
            self.assertEqual([], check_consistency(h))
        finally:
            h.close()

    def test_missing_required_key_is_rejected(self):
        data = self.base()
        del data["branches"][0]["spline2_y"]
        with self.assertRaises(REJECTED):
            self.load_text(data)

    def test_extra_keys_are_ignored(self):
        data = self.base()
        data["something_new"] = {"zoom": 0.5}
        h = self.load_text(data)       # e.g. a future 'view' section
        h.close()

    def test_invalid_file_raises_validation_error_with_message(self):
        """validate_json used to raise a TypeError (K5, 1c)."""
        data = self.base()
        data["nodes"][0]["x"] = 12.5
        with self.assertRaises(jsonschema.exceptions.ValidationError) as ctx:
            self.load_text(data)
        self.assertIn("12.5", str(ctx.exception.message))

    def test_invalid_grid_pos_is_rejected(self):
        for bad in ([1], [1, 2, 3], [1.5, 2], "x"):
            data = self.base()
            data["grid_pos"] = bad
            with self.subTest(grid_pos=bad):
                with self.assertRaises(REJECTED):
                    self.load_text(data)

    def test_schema_json_resource_equals_validator_schema(self):
        from importlib import resources
        text = resources.files("signalflowgrapher.resources") \
            .joinpath("schema.json").read_text(encoding="utf-8")
        self.assertEqual(JSONValidator().schema, json.loads(text))
        self.assertIn("grid_pos", json.loads(text)["properties"])
        self.assertIn("version", json.loads(text)["properties"])


class TestFileVersion(TestCase):
    def test_saved_files_carry_the_v3_file_format_version(self):
        self.assertEqual("3.0", FILE_FORMAT_VERSION)
        h = Harness()
        try:
            h.double_click(100, 100)
            with tempfile.TemporaryDirectory() as tmp:
                p = os.path.join(tmp, "v.sfg")
                h.save(p)
                with open(p, encoding="utf-8") as f:
                    self.assertEqual("3.0", json.load(f)["version"])
        finally:
            h.close()

    def test_files_of_older_versions_still_load(self):
        for version in ("2.0", "1.0", None):
            with open(example_files()[0], encoding="utf-8") as f:
                data = json.load(f)
            if version is None:
                del data["version"]
            else:
                data["version"] = version
            h = Harness()
            try:
                with tempfile.TemporaryDirectory() as tmp:
                    p = os.path.join(tmp, "old.sfg")
                    with open(p, "w", encoding="utf-8") as f:
                        json.dump(data, f)
                    h.load(p)
                self.assertEqual(len(data["nodes"]), len(h.nodes),
                                 "version %r" % version)
            finally:
                h.close()
