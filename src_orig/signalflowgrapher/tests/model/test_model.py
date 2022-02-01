from unittest import TestCase
from unittest.mock import MagicMock
from signalflowgrapher.model.model import CurvedBranch, PositionedNode


class TestCurvedBranch(TestCase):
    def test_properties(self):
        start_node = MagicMock()
        end_node = MagicMock()
        graph_mock = MagicMock()
        start_node.graph = graph_mock
        end_node.graph = graph_mock
        model = CurvedBranch(start_node,
                             end_node,
                             10,
                             20,
                             30,
                             40,
                             5,
                             10,
                             "test")

        self.assertEqual(model.label_text, "test")
        self.assertEqual(model.spline1_x, 10)
        self.assertEqual(model.spline1_y, 20)
        self.assertEqual(model.spline2_x, 30)
        self.assertEqual(model.spline2_y, 40)
        self.assertEqual(model.label_dx, 5)
        self.assertEqual(model.label_dy, 10)

    def test_transform(self):
        start_node = MagicMock()
        end_node = MagicMock()
        graph_mock = MagicMock()
        start_node.graph = graph_mock
        end_node.graph = graph_mock
        model = CurvedBranch(start_node,
                             end_node,
                             10,
                             20,
                             30,
                             40,
                             5,
                             10,
                             "test")
        model.transform(1, 2, 3, 4)
        self.assertEqual(model.spline1_x, 11)
        self.assertEqual(model.spline1_y, 22)
        self.assertEqual(model.spline2_x, 33)
        self.assertEqual(model.spline2_y, 44)

        model.transform(-5, 7, 0, 9)
        self.assertEqual(model.spline1_x, 6)
        self.assertEqual(model.spline1_y, 29)
        self.assertEqual(model.spline2_x, 33)
        self.assertEqual(model.spline2_y, 53)

    def test_to_dict(self):
        start_node = MagicMock()
        end_node = MagicMock()
        graph_mock = MagicMock()
        start_node.graph = graph_mock
        start_hex = MagicMock()
        start_hex.hex = '1234'
        start_node.id = start_hex
        end_node.graph = graph_mock
        end_hex = MagicMock()
        end_hex.hex = '5678'
        end_node.id = end_hex
        model = CurvedBranch(start_node,
                             end_node,
                             10,
                             20,
                             30,
                             40,
                             5,
                             10,
                             "test")
        dict = {'id': model.id.hex,
                'weight': 'test',
                'start': '1234',
                'end': '5678',
                'label_dx': 5,
                'label_dy': 10,
                'spline1_x': 10,
                'spline1_y': 20,
                'spline2_x': 30,
                'spline2_y': 40}
        self.assertEqual(dict, model.to_dict())

    def test_from_dict(self):
        dict = {'id': '3a2e4e76baac4b408c49e79be48ce4e1',
                'weight': 'test',
                'start': '1234',
                'end': '5678',
                'label_dx': 5,
                'label_dy': 10,
                'spline1_x': 10,
                'spline1_y': 20,
                'spline2_x': 30,
                'spline2_y': 40}

        start_node = MagicMock()
        end_node = MagicMock()
        graph_mock = MagicMock()
        start_node.graph = graph_mock
        start_hex = MagicMock()
        start_hex.hex = '1234'
        start_node.id = start_hex
        end_node.graph = graph_mock
        end_hex = MagicMock()
        end_hex.hex = '5678'
        end_node.id = end_hex

        model = CurvedBranch.from_dict(dict, [start_node, end_node])
        self.assertEqual(model.label_text, "test")
        self.assertEqual(model.spline1_x, 10)
        self.assertEqual(model.spline1_y, 20)
        self.assertEqual(model.spline2_x, 30)
        self.assertEqual(model.spline2_y, 40)
        self.assertEqual(model.label_dx, 5)
        self.assertEqual(model.label_dy, 10)
        self.assertEqual(model.id.hex, '3a2e4e76baac4b408c49e79be48ce4e1')


class PositionedNodeTest(TestCase):
    def test_properties(self):
        graph_mock = MagicMock()
        model = PositionedNode(graph_mock, 5, 10, 15, 20)

        self.assertEqual(5, model.x)
        self.assertEqual(10, model.y)
        self.assertEqual(15, model.label_dx)
        self.assertEqual(20, model.label_dy)
        self.assertEqual("", model.name)

        model.name = "test_node"
        self.assertEqual("test_node", model.name)
        self.assertEqual("test_node", model.label_text)

    def test_move(self):
        graph_mock = MagicMock()
        model = PositionedNode(graph_mock, 5, 10, 15, 20)
        model.move(9, 14)
        self.assertEqual(14, model.x)
        self.assertEqual(24, model.y)

        model.move(-231, 495)
        self.assertEqual(-217, model.x)
        self.assertEqual(519, model.y)

        model.move_label_relative(99, 15)
        self.assertEqual(114, model.label_dx)
        self.assertEqual(35, model.label_dy)

    def test_to_dict(self):
        graph_mock = MagicMock()
        model = PositionedNode(graph_mock, 5, 10, 15, 20)
        model.name = "test name"
        dict = {'id': model.id.hex,
                'label_dx': 15,
                'label_dy': 20,
                'name': 'test name',
                'x': 5,
                'y': 10}
        self.assertEqual(dict, model.to_dict())

    def test_from_dict(self):
        dict = {'id': '52fd43dae4fe47d38c4d40e44b80cf9f',
                'label_dx': 15,
                'label_dy': 20,
                'name': 'test name',
                'x': 5,
                'y': 10,
                'graph': MagicMock()}
        model = PositionedNode.from_dict(dict)
        self.assertEqual('52fd43dae4fe47d38c4d40e44b80cf9f',
                         model.id.hex)
        self.assertEqual(5, model.x)
        self.assertEqual(10, model.y)
        self.assertEqual(15, model.label_dx)
        self.assertEqual(20, model.label_dy)
        self.assertEqual("test name", model.name)
