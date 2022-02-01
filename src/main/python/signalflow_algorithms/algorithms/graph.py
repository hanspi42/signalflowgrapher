from __future__ import annotations
from signalflow_algorithms.common.json_dict import JSONDict
import uuid
from typing import Dict, Set


class GraphMember(object):
    def __init__(self, graph: Graph, **kwargs):
        super().__init__()
        self._graph = graph
        if 'id' in kwargs:
            self._id = kwargs['id']
        else:
            self._id = uuid.uuid4()

    @property
    def id(self) -> uuid.UUID:
        """Graph member id"""
        return self._id

    @property
    def graph(self) -> Graph:
        """The graph this object belongs to."""
        return self._graph

    @graph.setter
    def graph(self, graph: Graph):
        self._graph = graph


class Branch(GraphMember, JSONDict):
    def __init__(self,
                 start: Node,
                 end: Node,
                 weight: str = "",
                 *args,
                 **kwargs):
        """ Initialize new branch """
        if start.graph is not end.graph:
            raise ValueError(
                "Start and end node are part of different graphs.")
        super().__init__(start.graph, *args, **kwargs)

        # Set attributes
        self._weight = weight
        self.__start = start
        self.__end = end

        # Add branch to nodes
        self.__start.add_outgoing_branch(self)
        self.__end.add_ingoing_branch(self)

        # Add branch to graph
        self._graph.add_branch(self)

    @property
    def weight(self) -> str:
        return self._weight

    @weight.setter
    def weight(self, value):
        self._weight = value

    @property
    def start(self) -> Node:
        """Get start node"""
        return self.__start

    @property
    def end(self) -> Node:
        """Get end node"""
        return self.__end

    @GraphMember.graph.setter
    def graph(self, graph: Graph):
        # Allow set only if graph is being cleared
        # or has been cleared previously
        if graph is None or self.graph is None:
            self._graph = graph
        else:
            raise ValueError("This attribute is only to be set by the graph.")

    def reconnect(self, start: Node, end: Node):
        """Connect branch to nodes."""
        if self.graph is not None or \
                self.start is not None or \
                self.end is not None:
            raise ValueError("Branch must be removed before connect.")

        self.__start = start
        self.__end = end

        # Add branch to graph
        self._graph = start.graph
        self._graph.add_branch(self)

        # Add branch to nodes
        self.__start.add_outgoing_branch(self)
        self.__end.add_ingoing_branch(self)

    def remove(self):
        """Remove branch from and its nodes and the graph"""
        if not self.graph:
            raise ValueError("This branch is not part of a graph.")

        # Remove from nodes to avoid traverse after remove
        self.start.remove_outgoing_branch(self)
        self.end.remove_ingoing_branch(self)

        # Clear start and end node
        self.__start = None
        self.__end = None

        # Remove from graph
        self.graph.remove_branch(self)

        # Remove owning graph
        self._graph = None

    def to_dict(self) -> Dict:
        return {**super().to_dict(),
                "id": self.id.hex,
                "weight": self.weight,
                "start": self.start.id.hex,
                "end": self.end.id.hex}

    @classmethod
    def from_dict(cls, dict: Dict, nodes: Set[Node]) -> Branch:
        raise NotImplementedError()


class Node(GraphMember, JSONDict):
    def __init__(self, graph: Graph, **kwargs):
        super().__init__(graph, **kwargs)
        self.__ingoing: Set[Branch] = set()
        self.__outgoing: Set[Branch] = set()
        # Add self to graph
        graph.add_node(self)

    @property
    def ingoing(self) -> Set[Branch]:
        # Return copy to avoid manipulation
        return self.__ingoing.copy()

    @property
    def outgoing(self) -> Set[Branch]:
        # Return copy to avoid manipulation
        return self.__outgoing.copy()

    @GraphMember.graph.setter
    def graph(self, graph: Graph):
        # Allow set only if graph is being cleared
        # or has been cleared previously
        if graph is None or self.graph is None:
            self._graph = graph
        else:
            raise ValueError("This attribute is only to be set by the graph.")

    def remove(self):
        """Remove node with all connected branches."""
        # Find all branches that are connected to this node
        connected_branches = self.outgoing.union(self.ingoing)

        # Remove connected branches
        for branch in connected_branches:
            branch.remove()

        # Remove node from graph
        self.graph.remove_node(self)
        self._graph = None

    def add_outgoing_branch(self, branch: Branch):
        if branch.start is not self:
            raise ValueError("Another node is start of the branch.")

        self.__add_branch(branch, self.__outgoing)

    def add_ingoing_branch(self, branch: Branch):
        if branch.end is not self:
            raise ValueError("Another node is end of the branch.")

        self.__add_branch(branch, self.__ingoing)

    def __add_branch(self, branch: Branch, set: Set[Branch]):
        if self.graph is None:
            raise ValueError("Node is not part of a graph")

        if branch in set:
            raise ValueError("Branch is already connected to node.")

        if branch.graph is not self.graph:
            raise ValueError("Branch is part of other graph")

        set.add(branch)

    def remove_outgoing_branch(self, branch: Branch):
        if branch not in self.outgoing:
            raise ValueError("Branch is not connected to this node.")

        self.__outgoing.remove(branch)

    def remove_ingoing_branch(self, branch: Branch):
        if branch not in self.ingoing:
            raise ValueError("Branch is not connected to node.")

        self.__ingoing.remove(branch)

    def to_dict(self) -> Dict:
        return {**super().to_dict(),
                "id": self._id.hex}

    @classmethod
    def from_dict(cls, dict: Dict) -> Node:
        raise NotImplementedError()


class Graph(JSONDict):
    def __init__(self, graph: Graph = None):
        super().__init__()
        self._nodes: Set[Node] = set()
        self._branches: Set[Branch] = set()

        # Copy from given graph if any
        if graph is not None:
            node_map = {}

            for n in graph.nodes:
                new_node = Node(self, id=n.id)
                self._nodes.add(new_node)
                node_map[n] = new_node

            for b in graph.branches:
                self._branches.add(Branch(
                    node_map[b.start],
                    node_map[b.end],
                    b.weight,
                    id=b.id
                ))

    def add_node(self, node: Node):
        if node.graph is None:
            node.graph = self

        if node.graph is not self:
            raise ValueError("Node is already part of another graph.")

        if node in self.nodes:
            raise ValueError("Node has already been added to the graph.")

        if len(node.ingoing) > 0 or len(node.outgoing) > 0:
            raise ValueError("Cannot add connected node to graph.")

        self._nodes.add(node)

    def add_branch(self, branch: Branch):
        if branch.start is None or branch.end is None:
            raise ValueError("Can't add unconnected branch to graph.")

        if branch.graph is None:
            branch.graph = self

        if branch.graph is not self:
            raise ValueError("Branch is already part of another graph.")

        if branch in self._branches:
            raise ValueError("Branch is already part of this graph.")

        self._branches.add(branch)

    def remove_node(self, node: Node):
        """
        Remove a node that has no connected branches.
        """
        if node.graph is not self:
            raise ValueError("Node is not part of this graph.")

        if len(node.ingoing) > 0 or len(node.ingoing) > 0:
            raise ValueError("Node is still connected to branches.")

        self._nodes.remove(node)

    def remove_branch(self, branch: Branch):
        """Remove a not connected branch from the graph."""
        if branch.graph is not self:
            raise ValueError("Branch is not part of this graph.")

        if branch.start is not None or branch.end is not None:
            raise ValueError("Branch is still connected to nodes. " +
                             "To remove a branch call remove() on the branch.")

        self._branches.remove(branch)

    def __attach_node(self, node: Node):
        if node.graph is not None:
            raise ValueError("Node is already part of another graph.")

        if node in self.nodes:
            raise ValueError("Node is already part of this graph.")

        node.graph = self
        self._nodes.add(node)

    def __detach_node(self, node: Node):
        if node not in self.nodes:
            raise ValueError("Node is not part of this graph.")

        node.graph = None
        self._nodes.remove(node)

    def __attach_branch(self, branch: Branch):
        if branch.graph is not None:
            raise ValueError("Branch is already part of another graph.")

        if branch in self.branches:
            raise ValueError("Branch is already part of this graph.")

        branch.graph = self
        self._branches.add(branch)

    def __detach_branch(self, branch: Branch):
        if branch not in self.branches:
            raise ValueError("Branch is not part of this graph.")

        branch.graph = None
        self._branches.remove(branch)

    @property
    def nodes(self) -> Set[Node]:
        return self._nodes.copy()

    @property
    def branches(self) -> Set[Branch]:
        return self._branches.copy()

    def copy(self):
        """Make a deep copy of the graph. IDs will stay the same."""
        return Graph(self)

    def to_dict(self) -> Dict:
        return {**super().to_dict(),
                "nodes": [node.to_dict() for node in self._nodes],
                "branches": [branch.to_dict() for branch in self._branches]}

    @classmethod
    def from_dict(cls, dict: Dict) -> Graph:
        raise NotImplementedError()

    def subgraph(self, nodes: Set[Node]):
        """
        Get subgraph of self, including all nodes in given set of
        Nodes. Nodes in the given set are removed from the current graph
        Branches between the current graph and the subgraph will be removed.
        """
        new_graph = Graph()
        for node in nodes:
            for branch in node.outgoing:
                if branch.end not in nodes:
                    branch.remove()
                else:
                    self.__detach_branch(branch)
                    new_graph.__attach_branch(branch)
            for branch in node.ingoing:
                if (branch.start not in nodes):
                    branch.remove()
            self.__detach_node(node)
            new_graph.__attach_node(node)

        return new_graph
