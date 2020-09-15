import unittest
from signalflow_algorithms.algorithms.loop_group import find_loop_groups
from signalflow_algorithms.algorithms.graph import Graph, Branch, Node


class TestGraph(unittest.TestCase):

    def test_not_touching_loops(self):
        graph = Graph()

        node_1 = Node(graph)
        node_2 = Node(graph)
        node_3 = Node(graph)

        branch_a = Branch(node_1, node_1, "a")
        branch_b = Branch(node_2, node_2, "b")
        branch_c = Branch(node_3, node_3, "c")

        res = find_loop_groups([
            [branch_a],
            [branch_b],
            [branch_c]
        ])

        loops = [(loopGroup.loops, loopGroup.loop_count) for loopGroup
                 in res]

        expected = [
            ([[branch_a]], 1),
            ([[branch_b]], 1),
            ([[branch_c]], 1),
            ([[branch_b], [branch_a]], 2),
            ([[branch_c], [branch_b]], 2),
            ([[branch_c], [branch_a]], 2),
            ([[branch_c], [branch_b], [branch_a]], 3),
        ]

        self.assertCountEqual(expected, loops)

    def test_touching_selfloops(self):
        graph = Graph()

        node_1 = Node(graph)
        node_2 = Node(graph)

        branch_a = Branch(node_1, node_1, "a")
        branch_b = Branch(node_1, node_1, "b")
        branch_c = Branch(node_2, node_2, "c")

        res = find_loop_groups([[branch_a], [branch_b],
                                [branch_c]])

        loops = [(loopGroup.loops, loopGroup.loop_count) for loopGroup
                 in res]

        expected = [
            ([[branch_a]], 1),
            ([[branch_b]], 1),
            ([[branch_c]], 1),
            ([[branch_c], [branch_a]], 2),
            ([[branch_c], [branch_b]], 2)
        ]

        self.assertCountEqual(expected, loops)

    def test_touching_loops(self):
        graph = Graph()

        node_1 = Node(graph)
        node_2 = Node(graph)
        node_3 = Node(graph)
        node_4 = Node(graph)
        node_5 = Node(graph)
        node_6 = Node(graph)
        node_7 = Node(graph)

        Branch(node_1, node_2, "a")
        branch_b = Branch(node_2, node_3, "b")
        branch_c = Branch(node_3, node_4, "c")
        Branch(node_4, node_5, "d")
        branch_e = Branch(node_5, node_6, "e")
        Branch(node_6, node_7, "f")
        branch_g = Branch(node_6, node_5, "g")
        branch_h = Branch(node_4, node_3, "h")
        branch_i = Branch(node_4, node_2, "i")
        Branch(node_2, node_6, "j")

        res = find_loop_groups([[branch_h, branch_c], [branch_g, branch_e],
                                [branch_i, branch_b, branch_c]])

        loops = [(loopGroup.loops, loopGroup.loop_count) for loopGroup
                 in res]

        expected = [
            ([[branch_h, branch_c]], 1),
            ([[branch_g, branch_e]], 1),
            ([[branch_i, branch_b, branch_c]], 1),
            ([[branch_g, branch_e], [branch_h, branch_c]], 2),
            ([[branch_i, branch_b, branch_c], [branch_g, branch_e]], 2)
        ]

        self.assertCountEqual(expected, loops)
