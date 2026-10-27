from signalflowgrapher.io.json import JSONExport, JSONImport
from signalflowgrapher.io.tikz import TikZExport
from signalflowgrapher.model.model import ObservableGraph, Model
from signalflowgrapher.algorithms.graph import Graph, Node
from signalflowgrapher.algorithms.mason import MasonResult, mason
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
        export.write_as_json(self.__model.graph,
                             self.__model.get_grid_position(),
                             path,
                             view_origin=self.__model.get_view_origin())
        self.__command_handler.reset()

    def new_graph(self):
        """Initialize new graph"""
        logger.info("Create new graph")
        graph = ObservableGraph()
        # A new graph has the grid at the origin and is shown from there
        self.__model.set_grid_position((0, 0))
        self.__model.set_view_origin((0, 0))
        self.__model.graph = graph
        self.__command_handler.reset()

    def load_graph(self, path: str):
        """Load graph from the given path"""
        logger.info("Load graph from path: %s", path)
        json_import = JSONImport()
        dict = json_import.read_from_json(path)
        
        # extract grid position; default to (0,0) for backward compatibility
        grid_pos = tuple(dict.get("grid_pos", (0, 0)))
        if "grid_pos" in dict:
            del dict["grid_pos"]

        # extract the part of the graph that was shown when the file was
        # saved; files without it (all files of V2.0) are shown from (0, 0)
        view_origin = tuple(dict.get("view_origin", (0, 0)))
        if "view_origin" in dict:
            del dict["view_origin"]

        self.__model.set_grid_position(grid_pos)
        self.__model.set_view_origin(view_origin)
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
