from signalflowgrapher.io.json import JSONExport, JSONImport
from signalflowgrapher.io.tikz import TikZExport
from signalflowgrapher.model.model import ObservableGraph, Model
from signalflow_algorithms.algorithms.graph import Graph, Node
from signalflow_algorithms.algorithms.mason import MasonResult, mason
from signalflowgrapher.commands.command_handler import CommandHandler
import logging
logger = logging.getLogger(__name__)


class IOController(object):
    def __init__(self, model: Model, command_handler: CommandHandler):
        self.__model = model
        self.__command_handler = command_handler

    def generate_tikz(self, path: str):
        """Generate tikz representation for graph
           and save in under the given path
        """
        logger.info("Save tikz to path: %s", path)
        export = TikZExport()
        export.write_tikz(self.__model.graph.nodes,
                          self.__model.graph.branches,
                          path)

    def save_graph(self, path: str):
        """Save graph as json under the given path"""
        logger.info("Save graph to path: %s", path)
        export = JSONExport()
        export.write_as_json(self.__model.graph, path)
        self.__command_handler.reset()

    def new_graph(self):
        """Initialize new graph"""
        logger.info("Create new graph")
        graph = ObservableGraph()
        self.__model.graph = graph
        self.__command_handler.reset()

    def load_graph(self, path: str):
        """Load graph from the given path"""
        logger.info("Load graph from path: %s", path)
        json_import = JSONImport()
        dict = json_import.read_from_json(path)
        graph = ObservableGraph.from_dict(dict)
        self.__model.graph = graph
        self.__command_handler.reset()

    def generate_mason(self,
                       graph: Graph,
                       start: Node,
                       end: Node) -> MasonResult:
        """Apply mason rule"""
        logger.debug("Generate Mason")
        return mason(graph, start, end)
