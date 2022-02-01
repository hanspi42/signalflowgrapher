import unittest
from signalflow_algorithms.algorithms.graph import Graph, Branch, Node
from signalflow_algorithms.algorithms.find_paths import find_paths


class TestGraph(unittest.TestCase):

    def test_find_paths_simple(self):
        graph = Graph()

        node_1 = Node(graph)
        node_2 = Node(graph)
        node_3 = Node(graph)

        branch_a = Branch(node_1, node_2, "a")
        branch_b = Branch(node_2, node_3, "b")
        branch_c = Branch(node_2, node_3, "c")

        self.assertCountEqual([[branch_a, branch_b], [branch_a, branch_c]],
                              find_paths(node_1, node_3))
        self.assertCountEqual([[branch_a]], find_paths(node_1, node_2))
        self.assertCountEqual([[branch_b], [branch_c]],
                              find_paths(node_2, node_3))

    def test_find_paths_line(self):
        graph = Graph()

        node_1 = Node(graph)
        node_2 = Node(graph)
        node_3 = Node(graph)

        branch_a = Branch(node_1, node_2, "a")
        branch_b = Branch(node_2, node_3, "b")

        self.assertCountEqual([[branch_a, branch_b]],
                              find_paths(node_1, node_3))

    def test_find_paths_self_loops(self):
        graph = Graph()

        node_1 = Node(graph)
        node_2 = Node(graph)
        node_3 = Node(graph)

        branch_a = Branch(node_1, node_2, "a")
        branch_b = Branch(node_2, node_3, "b")
        branch_c = Branch(node_2, node_3, "c")

        Branch(node_2, node_2, "d")
        branch_e = Branch(node_2, node_1, "e")
        branch_f = Branch(node_3, node_1, "f")

        self.assertCountEqual([[branch_a, branch_b], [branch_a, branch_c]],
                              find_paths(node_1, node_3))

        paths = find_paths(node_2, node_1)
        self.assertCountEqual([[branch_c, branch_f], [branch_e],
                               [branch_b, branch_f]],
                              paths)

    def test_find_paths_self_loop2(self):
        graph = Graph()

        node_1 = Node(graph)
        node_2 = Node(graph)
        node_3 = Node(graph)
        node_4 = Node(graph)

        branch_a = Branch(node_1, node_2, "a")
        branch_b = Branch(node_2, node_3, "b")
        branch_c = Branch(node_3, node_4, "c")
        Branch(node_3, node_2, "d")

        paths = find_paths(node_1, node_4)
        self.assertCountEqual([[branch_a, branch_b, branch_c]], paths)

    def test_find_paths_self_loop3(self):
        graph = Graph()

        node_1 = Node(graph)
        node_2 = Node(graph)
        node_3 = Node(graph)
        node_4 = Node(graph)
        node_5 = Node(graph)

        branch_a = Branch(node_1, node_2, "a")
        branch_b = Branch(node_2, node_3, "b")
        branch_c = Branch(node_3, node_4, "c")
        branch_d = Branch(node_4, node_5, "d")
        Branch(node_4, node_2, "e")

        paths = find_paths(node_1, node_5)
        self.assertCountEqual([[branch_a, branch_b, branch_c, branch_d]],
                              paths)

    def test_find_paths_self_loop4(self):
        graph = Graph()

        node_1 = Node(graph)
        node_2 = Node(graph)
        node_3 = Node(graph)
        node_4 = Node(graph)

        branch_a = Branch(node_1, node_2, "a")
        Branch(node_1, node_3, "b")
        Branch(node_3, node_4, "c")
        Branch(node_4, node_1, "d")

        paths = find_paths(node_1, node_2)
        self.assertCountEqual([[branch_a]], paths)

    def test_find_paths_self_loop5(self):
        graph = Graph()

        node_0 = Node(graph)
        node_1 = Node(graph)
        node_2 = Node(graph)
        node_3 = Node(graph)
        node_4 = Node(graph)

        branch_x = Branch(node_0, node_1, "x")
        branch_a = Branch(node_1, node_2, "a")
        Branch(node_1, node_3, "b")
        Branch(node_3, node_4, "c")
        Branch(node_4, node_1, "d")

        paths = find_paths(node_0, node_2)
        self.assertCountEqual([[branch_x, branch_a]], paths)

    def test_find_paths_loop_over_loop(self):
        #           <--j ------------|
        #          |         <--h----|         <--g----
        #          |        |        |        |        |
        # X --a--> 1 --b--> 2 --c--> 3 --d--> 4 --e--> 5 --f--> Z
        #          |                                   |
        #           -------------------------------k-->

        # Create graph
        graph = Graph()

        # Create nodes
        node_x = Node(graph)  # input node
        node_1 = Node(graph)
        node_2 = Node(graph)
        node_3 = Node(graph)
        node_4 = Node(graph)
        node_5 = Node(graph)
        node_z = Node(graph)  # output node

        # Create branches and connect nodes
        branch_a = Branch(node_x, node_1, "a")
        branch_b = Branch(node_1, node_2, "b")
        branch_c = Branch(node_2, node_3, "c")
        branch_d = Branch(node_3, node_4, "d")
        branch_e = Branch(node_4, node_5, "e")
        branch_f = Branch(node_5, node_z, "f")

        Branch(node_5, node_4, "g")
        Branch(node_3, node_2, "h")
        Branch(node_3, node_1, "j")
        branch_k = Branch(node_1, node_5, "k")

        # Assert
        paths = find_paths(node_x, node_z)
        self.assertCountEqual([
            [branch_a, branch_b, branch_c, branch_d, branch_e, branch_f],
            [branch_a, branch_k, branch_f]
        ], paths)
