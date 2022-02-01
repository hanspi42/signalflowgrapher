from unittest import TestCase
from unittest.mock import MagicMock
from signalflow_algorithms.algorithms.graph import Graph, Branch, Node


class TestGraph(TestCase):

    def test_graph_copy(self):
        # Create graph
        graph = Graph()

        node_1 = Node(graph)
        node_2 = Node(graph)
        node_3 = Node(graph)
        node_4 = Node(graph)

        Branch(node_1, node_2)
        Branch(node_2, node_2)
        Branch(node_2, node_3)
        Branch(node_3, node_1)
        Branch(node_1, node_4)

        # Make copy
        graph_copy = graph.copy()

        # Assert
        nodes_original = list(graph.nodes)
        nodes_original.sort(key=lambda n: n.id)
        nodes_copy = list(graph_copy.nodes)
        nodes_copy.sort(key=lambda n: n.id)

        branches_original = list(graph.branches)
        branches_original.sort(key=lambda n: n.id)
        branches_copy = list(graph_copy.branches)
        branches_copy.sort(key=lambda n: n.id)

        for node_original, node_copy in zip(nodes_original, nodes_copy):
            self.assertTrue(self.__node_equals(node_original, node_copy))

        for branch_original, branch_copy in zip(branches_original,
                                                branches_copy):
            self.assertTrue(self.__branch_equals(branch_original, branch_copy))

    def test_subgraph(self):
        graph = Graph()
        node = Node(graph)
        subgraph = graph.subgraph({node})
        self.assertEqual(1, len(subgraph.nodes))
        self.assertEqual(0, len(graph.nodes))
        self.assertEqual(node, list(subgraph.nodes)[0])
        self.assertEqual(node.graph, subgraph)

        graph = Graph()
        node_1 = Node(graph)
        node_2 = Node(graph)
        node_3 = Node(graph)

        branch_1 = Branch(node_1, node_2, "1")
        branch_2 = Branch(node_2, node_1, "2")
        Branch(node_2, node_3, "3")
        Branch(node_3, node_1, "4")
        branch_5 = Branch(node_3, node_3, "5")
        branch_6 = Branch(node_2, node_2, "6")

        subgraph = graph.subgraph([node_1, node_2])

        self.assertCountEqual([node_1, node_2], subgraph.nodes)
        self.assertCountEqual([node_3], graph.nodes)
        self.assertCountEqual([branch_1, branch_2, branch_6],
                              subgraph.branches)
        self.assertCountEqual([branch_5], graph.branches)

        self.assertEqual(node_1.graph, subgraph)
        self.assertEqual(node_2.graph, subgraph)
        self.assertEqual(node_3.graph, graph)

        self.assertEqual(branch_1.graph, subgraph)
        self.assertEqual(branch_2.graph, subgraph)
        self.assertEqual(branch_5.graph, graph)
        self.assertEqual(branch_6.graph, subgraph)

    def test_add_remove_nodes(self):
        graph = Graph()
        node1 = MagicMock(Node)
        node2 = MagicMock(Node)
        node3 = MagicMock(Node)
        node1.graph = graph
        node2.graph = graph
        node3.graph = graph

        graph.add_node(node1)
        self.assertSetEqual({node1}, graph.nodes)

        graph.add_node(node2)
        graph.add_node(node3)

        def add_node_again():
            graph.add_node(node1)

        self.assertRaises(ValueError, add_node_again)
        self.assertSetEqual({node1, node2, node3}, graph.nodes)

        node4 = MagicMock(Node)
        node4.graph = MagicMock(Graph)

        def add_node4():
            graph.add_node(node4)

        self.assertRaises(ValueError, add_node4)
        self.assertSetEqual({node1, node2, node3}, graph.nodes)
        node4.graph = graph
        node4.ingoing = [1, 2, 3]
        self.assertRaises(ValueError, add_node4)
        self.assertSetEqual({node1, node2, node3}, graph.nodes)

        graph.remove_node(node1)
        self.assertSetEqual({node2, node3}, graph.nodes)

        graph.remove_node(node2)
        graph.remove_node(node3)

        self.assertSetEqual(set(), graph.nodes)

    def test_add_remove_branches(self):
        graph = Graph()
        branch1 = MagicMock(Branch)
        branch2 = MagicMock(Branch)
        branch3 = MagicMock(Branch)
        branch1.start = MagicMock(Node)
        branch1.end = MagicMock(Node)
        branch1.graph = graph
        branch2.start = MagicMock(Node)
        branch2.end = MagicMock(Node)
        branch2.graph = graph
        branch3.start = MagicMock(Node)
        branch3.end = MagicMock(Node)
        branch3.graph = graph

        graph.add_branch(branch1)
        self.assertSetEqual({branch1}, graph.branches)

        graph.add_branch(branch2)
        graph.add_branch(branch3)
        self.assertSetEqual({branch1, branch2, branch3}, graph.branches)

        def add_branch_again():
            graph.add_branch(branch1)

        self.assertRaises(ValueError, add_branch_again)

        branch4 = MagicMock(Branch)
        branch4.start = MagicMock(Node)
        branch4.end = MagicMock(Node)
        branch4.graph = None

        def add_branch4():
            graph.add_branch(branch4)

        branch4.end = None
        self.assertRaises(ValueError, add_branch4)
        self.assertSetEqual({branch1, branch2, branch3}, graph.branches)

        branch1.start = None
        branch1.end = None
        branch2.start = None
        branch2.end = None
        branch3.start = None
        branch3.end = None
        graph.remove_branch(branch1)
        self.assertSetEqual({branch2, branch3}, graph.branches)
        graph.remove_branch(branch2)
        graph.remove_branch(branch3)
        self.assertSetEqual(set(), graph.branches)

    def test_to_dict(self):
        return

    def __node_equals(self, node_1: Node, node_2: Node):
        # Check attributes
        if node_1.id != node_2.id:
            return False

        # Check ingoing branches
        not_matched = node_2.ingoing
        for branch_1 in node_1.ingoing:
            for branch_2 in not_matched.copy():
                if self.__branch_equals(branch_1, branch_2):
                    not_matched.remove(branch_2)

        if len(not_matched) != 0:
            return False

        # Check outgoing branches
        not_matched = node_2.outgoing
        for branch_1 in node_1.outgoing:
            for branch_2 in not_matched.copy():
                if self.__branch_equals(branch_1, branch_2):
                    not_matched.remove(branch_2)

        if len(not_matched) != 0:
            return False

        return True

    def __branch_equals(self, branch_1: Branch, branch_2: Branch):
        # Check ids of branches and ids of start and end nodes
        if branch_1.id != branch_2.id or \
            branch_1.weight != branch_2.weight or \
                branch_1.start.id != branch_2.start.id or \
                branch_1.end.id != branch_2.end.id:
            return False

        return True


class TestBranch(TestCase):
    def test_properties(self):
        node1 = MagicMock(Node)
        node2 = MagicMock(Node)
        graph = MagicMock(Graph)
        node1.graph = graph
        node2.graph = graph
        branch = Branch(node1, node2, "1234")
        self.assertEqual(node1, branch.start)
        self.assertEqual(node2, branch.end)
        self.assertEqual("1234", branch.weight)
        self.assertEqual(graph, branch.graph)

        branch.weight = "1111"
        self.assertEqual("1111", branch.weight)

        def set_graph(graph: Graph):
            branch.graph = graph

        graph2 = MagicMock(Graph)
        self.assertRaises(ValueError, set_graph, graph2)
        branch.graph = None
        self.assertEqual(None, branch.graph)
        branch.graph = graph2
        self.assertEqual(graph2, branch.graph)

    def test_add_remove(self):
        node1 = MagicMock(Node)
        node2 = MagicMock(Node)
        graph = MagicMock(Graph)
        node1.graph = graph
        node2.graph = graph
        branch = Branch(node1, node2, "1234")
        graph.add_branch.assert_called_once_with(branch)
        node1.add_outgoing_branch.assert_called_once_with(branch)
        node2.add_ingoing_branch.assert_called_once_with(branch)
        self.assertEqual(graph, branch.graph)

        branch.remove()
        self.assertIsNone(branch.graph)
        node1.remove_outgoing_branch.assert_called_once_with(branch)
        node2.remove_ingoing_branch.assert_called_once_with(branch)

    def test_connect(self):
        node1 = MagicMock(Node)
        node2 = MagicMock(Node)
        graph = MagicMock(Graph)
        node1.graph = graph
        node2.graph = graph
        branch = Branch(node1, node2, "1234")
        branch.remove()

        node3 = MagicMock(Node)
        node4 = MagicMock(Node)
        node3.graph = graph
        node4.graph = graph

        branch.reconnect(node3, node4)
        self.assertEqual(graph, branch.graph)
        node3.add_outgoing_branch.assert_called_once_with(branch)
        node4.add_ingoing_branch.assert_called_once_with(branch)

    def test_nodes_from_different_graphs(self):
        node1 = MagicMock(Node)
        node2 = MagicMock(Node)
        graph = MagicMock(Graph)
        graph2 = MagicMock(Graph)
        node1.graph = graph
        node2.graph = graph2

        def create_branch():
            Branch(node1, node2, "1234")

        self.assertRaises(ValueError, create_branch)

    def test_to_dict(self):
        node1 = MagicMock(Node)
        node2 = MagicMock(Node)
        graph = MagicMock(Graph)
        node1.graph = graph
        node2.graph = graph
        hex1 = MagicMock()
        hex1.hex = '1234'
        node1.id = hex1
        hex2 = MagicMock()
        hex2.hex = '5678'
        node2.id = hex2
        branch = Branch(node1, node2, "1234")

        dict = {'id': branch.id.hex,
                'weight': '1234',
                'start': '1234',
                'end': '5678',
                }
        self.assertEqual(dict, branch.to_dict())


class TestNode(TestCase):
    def test_properties(self):
        graph = MagicMock(Graph)
        node = Node(graph)
        self.assertEqual(graph, node.graph)

        b1 = MagicMock(Branch)
        b1.graph = graph
        b1.end = node
        node.add_ingoing_branch(b1)
        self.assertIn(b1, node.ingoing)

        b2 = MagicMock(Branch)
        b2.graph = graph
        b2.start = node
        node.add_outgoing_branch(b2)
        self.assertIn(b2, node.outgoing)

        node.remove_ingoing_branch(b1)
        self.assertEqual(set(), node.ingoing)

        node.remove_outgoing_branch(b2)
        self.assertEqual(set(), node.outgoing)

    def test_to_dict(self):
        graph = MagicMock(Graph)
        node = Node(graph)
        dict = {
            'id': node.id.hex
        }

        self.assertEqual(dict, node.to_dict())

    def test_set_graph(self):
        graph = MagicMock(Graph)
        node = Node(graph)
        self.assertEqual(graph, node.graph)

        graph2 = MagicMock(Graph)

        def set_graph():
            node.graph = graph2

        self.assertRaises(ValueError, set_graph)
        node.graph = None
        self.assertIsNone(node.graph)
        node.graph = graph2
        self.assertEqual(graph2, node.graph)

    def test_add_invalid_branches(self):
        graph = MagicMock(Graph)
        graph2 = MagicMock(Graph)
        node = Node(graph)
        self.assertEqual(graph, node.graph)

        b1 = MagicMock(Branch)
        b1.graph = graph2
        b1.end = node

        def add_ingoing():
            node.add_ingoing_branch(b1)
        self.assertRaises(ValueError, add_ingoing)

        b2 = MagicMock(Branch)
        b2.graph = graph2
        b2.start = node

        def add_outgoing():
            node.add_outgoing_branch(b2)
        self.assertRaises(ValueError, add_outgoing)

        b1.graph = graph
        b1.start = MagicMock(Node)
        b1.end = MagicMock(Node)

        b2.graph = graph
        b2.start = MagicMock(Node)
        b2.end = MagicMock(Node)

        self.assertRaises(ValueError, add_ingoing)
        self.assertRaises(ValueError, add_outgoing)

        node.graph = None
        b1.start = node
        b1.end = node
        b2.start = node
        b2.end = node
        self.assertRaises(ValueError, add_ingoing)
        self.assertRaises(ValueError, add_outgoing)

        node.graph = graph
        add_ingoing()
        add_outgoing()

        self.assertRaises(ValueError, add_ingoing)
        self.assertRaises(ValueError, add_outgoing)
