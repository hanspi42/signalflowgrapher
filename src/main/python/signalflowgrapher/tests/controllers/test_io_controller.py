from unittest import TestCase
from unittest.mock import MagicMock, patch
from signalflowgrapher.model.model import Model, ObservableGraph
from signalflowgrapher.commands.command_handler import CommandHandler
from signalflowgrapher.controllers.io_controller import IOController
from signalflowgrapher.io.tikz import TikZExport
from signalflowgrapher.io.json import JSONExport, JSONImport
from signalflow_algorithms.algorithms.mason import mason
from signalflow_algorithms.algorithms.graph import Graph, Node, Branch


class TestIOController(TestCase):

    def test_generate_tikz(self):
        model = MagicMock(Model)
        command_handler = MagicMock(CommandHandler)
        tikz_export = MagicMock(TikZExport)

        with patch("signalflowgrapher.controllers.io_controller.TikZExport",
                   MagicMock(return_value=tikz_export)):
            controller = IOController(model, command_handler)
            controller.generate_tikz("Test Path")

        tikz_export.write_tikz.assert_called_once_with(model.graph.nodes,
                                                       model.graph.branches,
                                                       "Test Path")

    def test_save_graph(self):
        model = MagicMock(Model)
        command_handler = MagicMock(CommandHandler)
        json_export = MagicMock(JSONExport)

        with patch("signalflowgrapher.controllers.io_controller.JSONExport",
                   MagicMock(return_value=json_export)):
            controller = IOController(model, command_handler)
            controller.save_graph("Path to save graph to")

        json_export.write_as_json.assert_called_once_with(
            model.graph, model.get_grid_position(),
            "Path to save graph to")
        command_handler.reset.assert_called_once()

    def test_new_graph(self):
        model = MagicMock(Model)
        command_handler = MagicMock(CommandHandler)
        observable_graph = MagicMock(ObservableGraph)

        with patch("signalflowgrapher.controllers.io_controller."
                   "ObservableGraph",
                   MagicMock(return_value=observable_graph)):
            controller = IOController(model, command_handler)
            controller.new_graph()

        self.assertEqual(observable_graph, model.graph)
        command_handler.reset.assert_called_once()

    def test_load_graph(self):
        model = MagicMock(Model)
        command_handler = MagicMock(CommandHandler)
        observable_graph = MagicMock(ObservableGraph)
        json_import = MagicMock(JSONImport)

        with patch("signalflowgrapher.controllers.io_controller."
                   "ObservableGraph",
                   observable_graph):
            with patch("signalflowgrapher.controllers.io_controller."
                       "JSONImport",
                       MagicMock(return_value=json_import)):
                controller = IOController(model, command_handler)
                controller.load_graph("Path to load")

        json_import.read_from_json.assert_called_once_with("Path to load")
        observable_graph.from_dict.assert_called_once_with(
            json_import.read_from_json())
        self.assertEqual(observable_graph.from_dict(), model.graph)
        command_handler.reset.assert_called_once()

    def test_generate_mason(self):
        model = MagicMock(Model)
        command_handler = MagicMock(CommandHandler)
        mason_mock = MagicMock(mason)

        graph = MagicMock(Graph)
        start = MagicMock(Node)
        end = MagicMock(Node)
        branch1 = MagicMock(Branch)
        branch1.weight = "a"
        branch2 = MagicMock(Branch)
        branch2.weight = None
        branch3 = MagicMock(Branch)
        branch3.weight = ""
        graph.branches = {branch1, branch2, branch3}

        with patch("signalflowgrapher.controllers.io_controller."
                   "mason",
                   mason_mock):
            controller = IOController(model, command_handler)
            controller.generate_mason(graph, start, end)

        mason_mock.assert_called_once_with(graph, start, end)
        self.assertEqual("a", branch1.weight)
        self.assertEqual(None, branch2.weight)
        self.assertEqual("", branch3.weight)
