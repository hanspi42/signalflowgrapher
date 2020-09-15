from signalflow_algorithms.algorithms.graph import \
    Graph, Node, Branch
from signalflow_algorithms.common.json_dict import JSONDict
from signalflowgrapher.common.observable import ObjectObservable
from typing import Dict, List
import uuid
import abc


class LabeledObject(JSONDict, abc.ABC):
    """
    Object with an attached label that has a relative position.
    """
    def __init__(self, dx, dy, *args):
        self._dx = dx
        self._dy = dy
        super().__init__(*args)

    @property
    def label_dx(self):
        """
        Distance between graph object and label on x-axis.
        """
        return self._dx

    @property
    def label_dy(self):
        """
        Distance between graph object and label on y-axis.
        """
        return self._dy

    def move_label_relative(self, dx, dy):
        """Move relative postion relative to graph object
        """
        self._dx += dx
        self._dy += dy

    @property
    def label_text(self) -> str:
        """
        Property of the label text.
        Can be overridden to return other values of an object.
        """
        return ''

    def to_dict(self) -> Dict:
        """
        Create dict from labeled object.
        """
        return {**super().to_dict(),
                "label_dx": self._dx,
                "label_dy": self._dy}


class CurvedBranch(LabeledObject, Branch):
    """
    Branch with start node, end node that can be curved using the splines.
    """
    def __init__(self, start_node, end_node, spline1_x,
                 spline1_y, spline2_x, spline2_y,
                 label_dx, label_dy, weight: str = "", *args):
        self.__spline1_x = spline1_x
        self.__spline1_y = spline1_y
        self.__spline2_x = spline2_x
        self.__spline2_y = spline2_y
        super().__init__(label_dx, label_dy,
                         start_node, end_node, weight, *args)

    @property
    def spline1_x(self) -> int:
        """
        Position of spline1 on the x-axis.
        """
        return self.__spline1_x

    @property
    def spline1_y(self) -> int:
        """
        Position of spline1 on the y-axis.
        """
        return self.__spline1_y

    @property
    def spline2_x(self) -> int:
        """
        Position of spline2 on the x-axis.
        """
        return self.__spline2_x

    @property
    def spline2_y(self) -> int:
        """
        Position of spline2 on the y-axis.
        """
        return self.__spline2_y

    @Branch.weight.setter
    def weight(self, value):
        """
        Set weight of branch to the given weight.
        """
        if self.weight != value:
            # Use parent setter
            Branch.weight.fset(self, value)

            # Notify graph about weight change
            self.graph.set_branch_weight(self, value)

    def transform(self, spline1_dx, spline1_dy, spline2_dx, spline2_dy):
        """
        Transform branch by moving spline1 and spline2 relative to its
        current position on x-axis and y-axis by the given deviations
        and notify of change.
        """
        self.__spline1_x += spline1_dx
        self.__spline1_y += spline1_dy
        self.__spline2_x += spline2_dx
        self.__spline2_y += spline2_dy

    def to_dict(self) -> Dict:
        """
        Create dict from branch.
        """
        return {**super().to_dict(),
                "spline1_x": self.__spline1_x,
                "spline1_y": self.__spline1_y,
                "spline2_x": self.__spline2_x,
                "spline2_y": self.__spline2_y,
                "label_dx": self._dx,
                "label_dy": self._dy}

    @classmethod
    def from_dict(cls, dict: Dict, nodes: List[Node]):
        """
        Create branch from dict.
        """
        # Map ids of start and end to objects
        start_id = dict["start"]
        end_id = dict["end"]
        start = next(node for node in nodes if node.id.hex == start_id)
        end = next(node for node in nodes if node.id.hex == end_id)

        branch = cls(start,
                     end,
                     dict["spline1_x"],
                     dict["spline1_y"],
                     dict["spline2_x"],
                     dict["spline2_y"],
                     dict["label_dx"],
                     dict["label_dy"])
        branch._id = uuid.UUID(dict["id"])
        branch._weight = dict["weight"]
        return branch

    @property
    def label_text(self) -> str:
        """
        Label text of branch.
        """
        return self.weight


class PositionedNode(LabeledObject, Node):
    """
    A Node with label and position.
    """
    def __init__(self,
                 graph: 'ObservableGraph',
                 x: int,
                 y: int,
                 label_dx: int,
                 label_dy: int,
                 *args):
        self.__x = x
        self.__y = y
        self.__name = ""
        super().__init__(label_dx, label_dy, graph, *args)

    def move(self, dx, dy):
        """
        Move the node relative to its current position on the x-axis and
        y-axis by the given deviations.
        """
        self.__x += dx
        self.__y += dy

    @property
    def x(self) -> int:
        """
        Get the position of the node on the x-axis.
        """
        return self.__x

    @property
    def y(self) -> int:
        """
        Get the position of the node on the y-axis.
        """
        return self.__y

    @property
    def name(self) -> str:
        """
        Get name of the node.
        """
        return self.__name

    @name.setter
    def name(self, value):
        """
        Set name of the node.
        """
        if self.name != value:
            self.__name = value

            # Notify graph about name change
            self.graph.set_node_name(self, value)

    def to_dict(self) -> Dict:
        """
        Create dict from node.
        """
        return {**super().to_dict(),
                "name": self.__name,
                "x": self.__x,
                "y": self.__y,
                "label_dx": self._dx,
                "label_dy": self._dy}

    @classmethod
    def from_dict(cls, dict: Dict):
        """
        Create node from dict.
        """
        node = cls(dict["graph"],
                   dict["x"],
                   dict["y"],
                   dict["label_dx"],
                   dict["label_dy"])
        node._id = uuid.UUID(dict["id"])
        node.__name = dict["name"]
        return node

    @property
    def label_text(self) -> str:
        """
        Label text of node.
        """
        return self.__name


class ObservableGraph(Graph, ObjectObservable):
    def __init__(self):
        super().__init__()
        self.__change_listeners = list()

    def add_node(self, node: PositionedNode):
        """
        Add a node to the graph and notify of change.
        """
        super().add_node(node)
        self._notify(PositionedNodeAddedEvent(node))

    def remove_node(self, node: PositionedNode):
        """
        Remove a node from the graph with all connected branches
        and notify of change.
        This can also be done on the node itself.
        """
        super().remove_node(node)
        self._notify(PositionedNodeRemovedEvent(node))

    def add_branch(self, branch: CurvedBranch):
        """
        Add a branch to the graph and notify of change.
        """
        super().add_branch(branch)
        self._notify(CurvedBranchAddedEvent(branch))

    def remove_branch(self, branch: CurvedBranch):
        """
        Remove a branch from the graph and notify of change.
        The branch will also be removed from the connected nodes ingoing and
        outgoing branches.
        This can also be done on the branch itself.
        """
        super().remove_branch(branch)
        self._notify(CurvedBranchRemovedEvent(branch))

    def move_node_relative(self, node: PositionedNode, dx, dy):
        """
        Move a node relative to its current position on x-axis and y-axis by
        the given deviations and notify of change.
        """
        node.move(dx, dy)
        self._notify(PositionedNodeMovedEvent(node, dx, dy))

    def move_label_relative(self, labeled_object: LabeledObject, dx, dy):
        """
        Move a label of a branch or node on x-axis and y-axis by the given
        deviations and notify of change.
        """
        labeled_object.move_label_relative(dx, dy)
        self._notify(LabelMovedEvent(labeled_object, dx, dy))

    def set_node_name(self, node: PositionedNode, name):
        """
        Set the name of the given node to the given name and notify of change.
        This can also be done on the node itself.
        """
        node.name = name
        self._notify(LabelChangedTextEvent(node, name))

    def set_branch_weight(self, branch: CurvedBranch, weight):
        """
        Set the given branch to the given weight and notify of change.
        This can also be done on the branch itself.
        """
        branch.weight = weight
        self._notify(LabelChangedTextEvent(branch, weight))

    def transform_branch(self,
                         branch: CurvedBranch,
                         spline1_dx,
                         spline1_dy,
                         spline2_dx,
                         spline2_dy):
        """
        Transform the given branch by moving spline1 and spline2 relative to
        its current position on x-axis and y-axis by the given deviations
        and notify of change.
        This can also be done on the branch itself.
        """
        branch.transform(spline1_dx, spline1_dy, spline2_dx, spline2_dy)
        self._notify(CurvedBranchTransformedEvent(
            branch,
            spline1_dx=spline1_dx,
            spline1_dy=spline1_dy,
            spline2_dx=spline2_dx,
            spline2_dy=spline2_dy)
        )

    @classmethod
    def from_dict(cls, dict):
        """
        Create the graph from dictionary.
        """
        graph = cls()
        for node in dict["nodes"]:
            node['graph'] = graph
            PositionedNode.from_dict(node)
        for branch in dict["branches"]:
            CurvedBranch.from_dict(branch, graph.nodes)
        return graph


class Model(ObjectObservable):
    """
    Observable model that holds a graph.
    """

    def __init__(self):
        super().__init__()
        self.__graph: ObservableGraph = None

    @property
    def graph(self) -> ObservableGraph:
        """
        The graph.
        """
        return self.__graph

    @graph.setter
    def graph(self, graph: ObservableGraph):
        """
        Set a new graph and notify of change.
        """
        # Remove listener from old graph
        if self.graph is not None:
            self.graph.unobserve(self.__handle_model_change)

        # Add listener to new graph
        graph.observe(self.__handle_model_change)

        # Set new graph
        self.__graph = graph

        # Notify
        self._notify(GraphChangedEvent(
            graph.nodes,
            graph.branches
        ))

    def move_graph_relative(self, dx, dy):
        """
        Move the whole graph relative to its current position on x-axis and
        y-axis by dx and dy.
        """
        nodes = self.__graph.nodes
        for node in nodes:
            node.move(dx, dy)

        branches = self.__graph.branches
        for branch in branches:
            branch.transform(dx, dy, dx, dy)

        self._notify(GraphMovedEvent(nodes, branches, dx, dy))

    def __handle_model_change(self, event):
        self._notify(event)


class LabelEvent(object):
    """Base class for all events related to a label."""

    def __init__(self, labeled_obj):
        super().__init__()
        self.labeled_obj = labeled_obj


class LabelMovedEvent(LabelEvent):
    """Occurs after a label has been moved."""

    def __init__(self, labeled_obj, dx, dy):
        super().__init__(labeled_obj)
        self.dx = dx
        self.dy = dy


class LabelChangedTextEvent(LabelEvent):
    """Occurs after the text of a label has changed."""

    def __init__(self, labeled_obj, new_text):
        super().__init__(labeled_obj)
        self.new_text = new_text


class PositionedNodeEvent(object):
    """Base class for all events related to a node."""

    def __init__(self, node):
        self.node = node


class PositionedNodeAddedEvent(PositionedNodeEvent):
    """Occurs after a node has been added."""

    def __init__(self, node):
        super().__init__(node)


class PositionedNodeRemovedEvent(PositionedNodeEvent):
    """Occurs after a node has been removed."""

    def __init__(self, node):
        super().__init__(node)


class PositionedNodeMovedEvent(object):
    """Occurs after a node has been moved."""

    def __init__(self, node, dx, dy):
        super().__init__()
        self.node = node
        self.dx = dx
        self.dy = dy


class CurvedBranchEvent(object):
    """Base class for all events related to a branch."""

    def __init__(self, branch):
        self.branch = branch


class CurvedBranchAddedEvent(CurvedBranchEvent):
    """Occurs after a branch has been added"""

    def __init__(self, branch):
        super().__init__(branch)


class CurvedBranchRemovedEvent(CurvedBranchEvent):
    """Occurs after a branch has been removed."""

    def __init__(self, branch):
        super().__init__(branch)


class CurvedBranchTransformedEvent(CurvedBranchEvent):
    """Occurs after the splines of a branch have changed."""

    def __init__(self, branch, spline1_dx, spline1_dy,
                 spline2_dx, spline2_dy):
        self.spline1_dx = spline1_dx
        self.spline1_dy = spline1_dy
        self.spline2_dx = spline2_dx
        self.spline2_dy = spline2_dy
        super().__init__(branch)


class GraphEvent(object):
    """Base class for all events related to the whole graph."""

    def __init__(self, nodes, branches):
        self.nodes = nodes
        self.branches = branches
        super().__init__()


class GraphChangedEvent(GraphEvent):
    """Occurs after the whole graph has been changed."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)


class GraphMovedEvent(GraphEvent):
    """Occurs after the whole graph has been moved."""

    def __init__(self, nodes, branches, dx, dy, **kwargs):
        super().__init__(nodes, branches, **kwargs)
        self.dx = dx
        self.dy = dy
