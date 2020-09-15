from typing import List
import unittest
from signalflow_algorithms.algorithms.johnson import \
    simple_cycles, strongly_connected_components
from signalflow_algorithms.algorithms.graph import Branch, Graph, Node


class TestGraph(unittest.TestCase):

    def test_johnson_1(self):
        graph = Graph()

        node_1 = Node(graph)
        node_2 = Node(graph)
        node_3 = Node(graph)

        branch_a = Branch(node_1, node_2, "a")
        branch_b = Branch(node_2, node_3, "b")
        branch_c = Branch(node_3, node_1, "c")

        cycles = [[branch.id for branch in cycle]
                  for cycle in simple_cycles(graph)]
        self.assertTrue(self.__check_loop_order(
            [[branch_a.id, branch_b.id, branch_c.id]], cycles))

    def test_johnson_2(self):
        graph = Graph()

        node_1 = Node(graph)
        node_2 = Node(graph)
        node_3 = Node(graph)
        node_4 = Node(graph)

        branch_a = Branch(node_1, node_2, "a")
        branch_b = Branch(node_2, node_1, "b")
        branch_c = Branch(node_2, node_4, "c")
        branch_d = Branch(node_4, node_3, "d")
        branch_e = Branch(node_3, node_1, "e")
        branch_f = Branch(node_1, node_3, "f")

        components = strongly_connected_components(graph)
        self.assertEqual(1, len(components))
        self.assertCountEqual([node_3, node_4, node_2, node_1], components[0])

        cycles = [[branch.id for branch in cycle]
                  for cycle in simple_cycles(graph)]

        self.assertTrue(self.__check_loop_order(
            [[branch_f.id, branch_e.id],
             [branch_a.id, branch_c.id, branch_d.id, branch_e.id],
             [branch_a.id, branch_b.id],
             ], cycles))

    def test_johnson_3(self):
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

        cycles = cycles = [[branch.id for branch in cycle]
                           for cycle in simple_cycles(graph)]

        self.assertTrue(self.__check_loop_order(
            [[branch_b.id, branch_c.id, branch_i.id],
             [branch_h.id, branch_c.id],
             [branch_e.id, branch_g.id]],
            cycles))

    def test_johnson_4(self):
        graph = Graph()
        node_a = Node(graph)
        node_b = Node(graph)
        node_c = Node(graph)
        node_d = Node(graph)

        branch_ac = Branch(node_a, node_c, "ac")
        branch_ca = Branch(node_c, node_a, "ca")
        branch_ab = Branch(node_a, node_b, "ab")
        branch_ba = Branch(node_b, node_a, "ba")
        branch_bc = Branch(node_b, node_c, "bc")
        branch_cd = Branch(node_c, node_d, "cd")
        branch_db = Branch(node_d, node_b, "db")

        actual = strongly_connected_components(graph)
        expected = [[node_a, node_b, node_c, node_d]]

        self.assertTrue(self.__check_strongly_connected_components(
            expected, actual))

        cycles = [[branch.id for branch in cycle]
                  for cycle in simple_cycles(graph)]

        self.assertTrue(
            self.__check_loop_order([[branch_ac.id, branch_ca.id],
                                     [branch_ab.id, branch_ba.id],
                                     [branch_ab.id, branch_bc.id,
                                      branch_ca.id],
                                     [branch_ac.id, branch_cd.id,
                                      branch_db.id, branch_ba.id],
                                     [branch_bc.id, branch_cd.id,
                                      branch_db.id]],
                                    cycles))

    def test_johson_multiple_scc(self):
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

        Branch(node_1, node_2, "a")
        branch_b = Branch(node_2, node_3, "b")
        branch_c = Branch(node_3, node_4, "c")
        branch_d = Branch(node_4, node_2, "d")
        branch_e = Branch(node_1, node_5, "e")
        branch_f = Branch(node_5, node_6, "f")
        branch_g = Branch(node_6, node_1, "g")
        branch_h = Branch(node_9, node_7, "h")
        branch_i = Branch(node_7, node_8, "i")
        branch_j = Branch(node_8, node_9, "j")
        Branch(node_6, node_9, "k")

        actual = strongly_connected_components(graph)
        expected = [[node_9, node_8, node_7],
                    [node_3, node_2, node_4],
                    [node_6, node_5, node_1]]

        self.assertTrue(self.__check_strongly_connected_components(
            expected, actual))

        cycles = [[branch.id for branch in cycle]
                  for cycle in simple_cycles(graph)]

        self.assertTrue(
            self.__check_loop_order([[branch_b.id, branch_c.id, branch_d.id],
                                     [branch_e.id, branch_f.id, branch_g.id],
                                     [branch_h.id, branch_i.id, branch_j.id]],
                                    cycles))

    def test_strongly_connected_components(self):
        graph = Graph()

        node_1 = Node(graph)
        node_2 = Node(graph)
        node_3 = Node(graph)

        Branch(node_1, node_2, "a")
        Branch(node_2, node_3, "b")
        Branch(node_2, node_3, "c")
        Branch(node_3, node_1, "d")

        components = strongly_connected_components(graph)
        self.assertEqual(1, len(components))
        component = components[0]
        self.assertCountEqual([node_3, node_2, node_1], component)

    def test_self_loops_1(self):
        graph = Graph()

        node_1 = Node(graph)
        node_2 = Node(graph)
        node_3 = Node(graph)

        branch_a = Branch(node_1, node_1, "a")
        branch_b = Branch(node_2, node_2, "b")
        branch_c = Branch(node_3, node_3, "c")

        cycles = [[branch.id for branch in cycle]
                  for cycle in simple_cycles(graph)]

        self.assertTrue(self.__check_loop_order(
            [[branch_a.id],
             [branch_b.id],
             [branch_c.id]], cycles))

    def test_self_loops_2(self):
        graph = Graph()

        node_1 = Node(graph)

        branch_a = Branch(node_1, node_1, "a")

        cycles = [[branch.id for branch in cycle]
                  for cycle in simple_cycles(graph)]

        self.assertCountEqual([[branch_a.id]], cycles)

        graph = Graph()

        node_1 = Node(graph)
        node_2 = Node(graph)
        node_3 = Node(graph)
        node_4 = Node(graph)

        branch_a = Branch(node_1, node_2, "a")
        branch_b = Branch(node_2, node_3, "b")
        branch_c = Branch(node_3, node_1, "c")
        Branch(node_3, node_4, "d")
        branch_e = Branch(node_1, node_1, "e")
        branch_f = Branch(node_2, node_2, "f")
        branch_g = Branch(node_3, node_3, "g")
        branch_h = Branch(node_4, node_4, "h")

        cycles = [[branch.id for branch in cycle]
                  for cycle in simple_cycles(graph)]

        self.assertTrue(self.__check_loop_order(
            [[branch_e.id],
             [branch_a.id, branch_b.id, branch_c.id],
             [branch_f.id], [branch_g.id], [branch_h.id]], cycles))

    def __check_loop_order(self, expected_loops, actual_loops):
        """ Method for comparing two lists with loops.
            Each loop must have a defined order, but the start of the loop
            is not defined and the order of the loops is also not defined
        """
        # Check if the amount of loops matches
        if (len(expected_loops) != len(actual_loops)):
            return False

        # Compare each loop with each other loop and check if it is a match
        for expected_loop in expected_loops:
            match_found = False
            for actual_loop in actual_loops:
                loop_matches = self.__check_loop(expected_loop, actual_loop)
                if (loop_matches):
                    match_found = True
                    break

            if (not match_found):
                return False
        return True

    def __check_loop(self, expected_loop, actual_loop):
        """Check if two given loops are equal
           (requires same order, but different start is allowed)
        """
        if (len(actual_loop) != len(expected_loop)):
            return False

        # Get the index of the start branch in the actual_loop
        pos = 0

        if (expected_loop[0] not in actual_loop):
            return False

        offset = actual_loop.index(expected_loop[0])
        while pos < len(expected_loop):
            expected_branch = expected_loop[pos]
            actual_branch = actual_loop[(pos + offset) % len(actual_loop)]
            if (expected_branch != actual_branch):
                return False
            pos += 1

        return True

    def __check_strongly_connected_component(
            self,
            expected: List[Node],
            actual: List[Node]) -> bool:
        expected_set = set(expected)
        actual_set = set(actual)
        intersected = expected_set.intersection(actual_set)
        return len(intersected) == len(expected)

    def __check_strongly_connected_components(
            self,
            expected: List[List[Node]],
            actual: List[List[Node]]):
        """
        Check if exactly one match for each strongly
        connected component exists.
        """

        not_matched = expected.copy()

        for scc_actual in actual:
            # Try any of the expected values
            for scc_expected in not_matched.copy():
                if self.__check_strongly_connected_component(
                        scc_expected, scc_actual):
                    # Remove after a match occured
                    not_matched.remove(scc_expected)

        # If there are no more matches left return True.
        return len(not_matched) == 0
