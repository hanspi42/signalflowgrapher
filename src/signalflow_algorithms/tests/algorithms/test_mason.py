import unittest
from signalflow_algorithms.algorithms.graph import Graph, Branch, Node
from signalflow_algorithms.algorithms.mason import loop_to_expression, mason
from sympy import Mul, Symbol, srepr


class TestMason(unittest.TestCase):
    def test_mason_1(self):
        # Create graph
        graph = Graph()

        # Add nodes
        node_x = Node(graph)  # input node
        node_1 = Node(graph)
        node_2 = Node(graph)
        node_3 = Node(graph)
        node_4 = Node(graph)
        node_5 = Node(graph)
        node_z = Node(graph)  # output node

        # Add branches
        Branch(node_x, node_1, "a")
        Branch(node_1, node_2, "b")
        Branch(node_2, node_3, "c")
        Branch(node_3, node_4, "d")
        Branch(node_4, node_5, "e")
        Branch(node_5, node_z, "f")
        Branch(node_5, node_4, "g")
        Branch(node_3, node_2, "h")
        Branch(node_3, node_1, "j")
        Branch(node_1, node_5, "k")

        # Execute
        result = mason(graph, node_x, node_z)

        # Assert
        expected = [
            "(a*b*c*d*e*f + a*f*k*(-c*h + 1))",
            "/(b*c*e*g*j - b*c*j + c*e*g*h - c*h - e*g + 1)"
        ]

        T = result.transfer_function[0][0]
        actual = T.subs(result.transfer_function) \
            .subs(result.numerator) \
            .subs(result.denominator) \
            .subs(result.determinant) \
            .subs(result.paths) \
            .subs(result.loops)

        self.assertEqual(expected[0] + expected[1], str(actual))

    # Test with minimum cycle size
    def test_loop_to_expression_1(self):
        graph = Graph()

        node_1 = Node(graph)

        branch_a = Branch(node_1, node_1, "a")

        branches = [branch_a]

        expectedExpression = Symbol(branch_a.weight)

        expression = loop_to_expression(branches)

        self.assertEqual(srepr(expression), srepr(expectedExpression))

    # Test right above minimum cycle size
    def test_loop_to_expression_2(self):
        graph = Graph()

        node_1 = Node(graph)
        node_2 = Node(graph)

        branch_a = Branch(node_1, node_2, "a")
        branch_b = Branch(node_2, node_1, "b")

        branches = [branch_a, branch_b]

        expectedExpression = Mul(Symbol(branch_a.weight),
                                 Symbol(branch_b.weight))

        expression = loop_to_expression(branches)

        self.assertEqual(srepr(expression), srepr(expectedExpression))

    # Test bigger cycle size
    def test_loop_to_expression_3(self):
        graph = Graph()

        node_1 = Node(graph)
        node_2 = Node(graph)
        node_3 = Node(graph)
        node_4 = Node(graph)
        node_5 = Node(graph)
        node_6 = Node(graph)
        node_7 = Node(graph)
        node_8 = Node(graph)
        node_9 = Node(graph)
        node_10 = Node(graph)
        node_11 = Node(graph)

        branch_a = Branch(node_1, node_2, "a")
        branch_b = Branch(node_2, node_3, "b")
        branch_c = Branch(node_3, node_4, "c")
        branch_d = Branch(node_4, node_5, "d")
        branch_e = Branch(node_5, node_6, "e")
        branch_f = Branch(node_6, node_7, "f")
        branch_g = Branch(node_7, node_8, "g")
        branch_h = Branch(node_8, node_9, "h")
        branch_j = Branch(node_9, node_10, "j")
        branch_k = Branch(node_10, node_11, "k")
        branch_l = Branch(node_11, node_1, "l")

        branches = [branch_a, branch_b, branch_c, branch_d, branch_e, branch_f,
                    branch_g, branch_h, branch_j, branch_k, branch_l]

        expectedExpression = Mul(Symbol(branch_a.weight),
                                 Symbol(branch_b.weight),
                                 Symbol(branch_c.weight),
                                 Symbol(branch_d.weight),
                                 Symbol(branch_e.weight),
                                 Symbol(branch_f.weight),
                                 Symbol(branch_g.weight),
                                 Symbol(branch_h.weight),
                                 Symbol(branch_j.weight),
                                 Symbol(branch_k.weight),
                                 Symbol(branch_l.weight))

        expression = loop_to_expression(branches)

        self.assertEqual(srepr(expression), srepr(expectedExpression))

    # Tests fix for issue #102 (internal gitlab)
    def test_mason_2(self):
        # Create graph
        graph = Graph()

        # Add nodes
        node_x = Node(graph)  # input node
        node_1 = Node(graph)
        node_2 = Node(graph)
        node_3 = Node(graph)
        node_4 = Node(graph)
        node_5 = Node(graph)
        node_z = Node(graph)  # output node

        # Add branches
        Branch(node_x, node_z, "g7")
        Branch(node_z, node_x, "h7")
        Branch(node_z, node_1, "g8")
        Branch(node_1, node_2, "g2")
        Branch(node_2, node_3, "g3")
        Branch(node_3, node_4, "g4")
        Branch(node_4, node_5, "g5")
        Branch(node_5, node_x, "g6")
        Branch(node_2, node_1, "h2")
        Branch(node_4, node_3, "h4")

        # Execute
        result = mason(graph, node_x, node_z)

        # Assert
        expected_num = "g7*(g2*g4*h2*h4 - g2*h2 - g4*h4 + 1)"

        actual_num = result.numerator[0][1] \
            .subs(result.numerator) \
            .subs(result.denominator) \
            .subs(result.determinant) \
            .subs(result.paths) \
            .subs(result.loops)

        self.assertEqual(expected_num, str(actual_num))

    # Tests fix for issue #2 on github
    def test_mason_3(self):
        # Create graph
        graph = Graph()

        # Add nodes
        node_x = Node(graph)  # input node
        node_1 = Node(graph)
        node_2 = Node(graph)
        node_3 = Node(graph)
        node_4 = Node(graph)
        node_5 = Node(graph)
        node_z = Node(graph)  # output node

        # Add branches
        Branch(node_x, node_z, "g7")
        Branch(node_z, node_x, "h7")
        Branch(node_z, node_1, "g8")
        Branch(node_1, node_2, "C")
        Branch(node_2, node_3, "g3")
        Branch(node_3, node_4, "g4")
        Branch(node_4, node_5, "g5")
        Branch(node_5, node_x, "g6")
        Branch(node_2, node_1, "h2")
        Branch(node_4, node_3, "N")

        # Execute
        result = mason(graph, node_x, node_z)

        # Assert
        expected_num = "g7*(C*N*g4*h2 - C*h2 - N*g4 + 1)"

        actual_num = result.numerator[0][1] \
            .subs(result.numerator) \
            .subs(result.denominator) \
            .subs(result.determinant) \
            .subs(result.paths) \
            .subs(result.loops)

        self.assertEqual(expected_num, str(actual_num))
