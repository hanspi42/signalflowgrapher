from typing import Set, List
from signalflow_algorithms.algorithms.graph import Node, Branch
from signalflow_algorithms.algorithms.johnson import simple_cycles
import sympy.simplify as simplify
from sympy import Mul, Add, Pow, Integer
from signalflow_algorithms.common.utils import parse_weight, parse_factor


class ChainingOperation(object):
    def __init__(self):
        super().__init__()

    def get_nodes_in_order(self, branch_1: Branch, branch_2: Branch) -> (
            Node, Node, Node):
        """
        Get the involved nodes in the right order
        returns the three nodes, the middle node should be removed,
        after that, a new branch from the first to the last should be
        created
        """
        if (branch_1.end == branch_2.start):
            middle_node = branch_1.end
            start_node = branch_1.start
            end_node = branch_2.end
        elif (branch_2.end == branch_1.start):
            middle_node = branch_2.end
            start_node = branch_2.start
            end_node = branch_1.end
        else:
            return None

        if len(middle_node.ingoing) != 1 \
           or len(middle_node.outgoing) != 1:
            return None

        return start_node, middle_node, end_node

    def get_new_weight(self, branch_1: Branch, branch_2: Branch) -> str:
        """
        Get the new weight of two branches after applying
        the chainging operation
        """
        return str(simplify(Mul(parse_weight(branch_1.weight,
                                           branch_1),
                                parse_weight(branch_2.weight,
                                           branch_2))))


class CombineParallelOperation(object):
    def __init__(self):
        super().__init__()

    def combinable(self, branch_1: Branch, branch_2: Branch) -> bool:
        """ Returns true, if the two given branches are parallel
        and are combinable
        """
        return (branch_1.start == branch_2.start) \
            and (branch_1.end == branch_2.end)

    def get_new_weight(self, branch_1: Branch, branch_2: Branch) -> str:
        """ Get the new weight of two branches after applying the
        combine parallel operation
        """
        return str(simplify(Add(parse_weight(branch_1.weight,
                                           branch_1),
                                parse_weight(branch_2.weight,
                                           branch_2))))


class EliminateNodeOperation(object):
    def __init__(self):
        super().__init__()

    def get_self_loops(self,
                       node_to_eliminate: Node) -> Set:
        """
        Get the weights of the self loops that has to be created
        after removal of a node within one or multiple loops.
        Returns set of tuples with each tuple containing the target node
        and the weight for the self loop.
        """
        results = set()

        # Find all cycles that contain the given nodes
        for loop in simple_cycles(node_to_eliminate.graph):
            loop_nodes = [branch.start for branch in loop]

            if len(loop) == 2:
                if node_to_eliminate.id in map(lambda n: n.id, loop_nodes):
                    # Get target for self loop
                    target = loop_nodes[0]
                    if target is node_to_eliminate:
                        target = loop_nodes[1]

                    # Build self loop weight
                    weight = str(simplify(Mul(parse_weight(loop[0].weight,
                                                         loop[0]),
                                              parse_weight(loop[1].weight,
                                                         loop[1]))))
                    results.add((target, weight))

        return results

    def get_new_paths(self, node_to_eliminate: Node) -> Set:
        """
        Get all paths that have to be created after removal of the node.
        Returns a set of tuples containing start, end and weigth of the branch.
        """
        paths = set()
        chaining_op = ChainingOperation()

        # Find all paths that pass over the node
        for ingoing in node_to_eliminate.ingoing:
            for outgoing in node_to_eliminate.outgoing:
                start, end = ingoing.start, outgoing.end
                if start is not end:
                    weight = chaining_op.get_new_weight(ingoing, outgoing)
                    paths.add((start, end, weight))

        return paths


class EliminateSelfLoopOperation(object):
    def __init__(self):
        super().__init__()

    def is_self_loop(self, self_loop: Branch) -> bool:
        """Returns true if the given loop is a self loop"""
        return self_loop.start is self_loop.end

    def get_affected_branches(self, self_loop: Branch) -> Set[Branch]:
        """Get branches which are effected when removing the given loop"""
        affected = self_loop.start.ingoing.copy()
        affected.remove(self_loop)
        return affected

    def get_new_affected_branch_weight(self,
                                       self_loop: Branch,
                                       target: Branch) -> str:
        """
        Get new weight that has to be applied to the affected branch after
        remove of the self loop.
        """
        denominator = Add(Integer(1),
                          Mul(parse_weight(self_loop.weight, self_loop),
                              Integer(-1)))
        return str(simplify(
            Mul(parse_weight(target.weight, target),
                Pow(denominator, Integer(-1)))))


class InvertPathOperation(object):
    def __init__(self):
        super().__init__()

    def start_is_independent_var(self, path: List[Branch]) -> bool:
        """
        Returns true if the given branch originates
        in an independent variable.
        """
        if len(path) > 0:
            return len(path[0].start.ingoing) == 0

        return False

    def get_new_branch_weight(self, branch_to_invert: Branch) -> str:
        """Get the new weight to invert a branch."""
        denominator = parse_weight(branch_to_invert.weight, branch_to_invert)
        return str(simplify(Mul(Integer(1), Pow(denominator, Integer(-1)))))

    def get_new_affected_branch_weight(
            self,
            branch_to_invert: Branch,
            affected_branch: Branch) -> str:
        """
        Get the new weight for branch that is affected by the branch inversion.
        """
        return str(simplify(
            Mul(Mul(Integer(-1), parse_weight(affected_branch.weight,
                                            affected_branch)),
                parse_weight(self.get_new_branch_weight(branch_to_invert),
                           branch_to_invert))))

    def get_affected_branches(self, branch_to_invert: Branch) -> Set[Branch]:
        """
        Get all branches that must be reconnected to the
        inverted branch end after the inversion and for which
        the weight must be adjusted accordingly.
        """
        affected = branch_to_invert.end.ingoing.copy()
        affected.remove(branch_to_invert)
        return affected


class ScalePathOperation(object):
    def __init__(self):
        super().__init__()

    def scalable(self, node: Node) -> bool:
        """Returns true if the given node is scalable"""
        if len(node.ingoing) > 0 and len(node.outgoing) > 0:
            return True

        return False

    def get_ingoing_branch_weight(self, branch: Branch, factor: str) -> str:
        """Get scaled weight of ingoing branch"""
        # Divide by factor
        return str(simplify(Mul(Pow(parse_factor(factor),
                                    Integer(-1)),
                                parse_weight(branch.weight, branch))))

    def get_outgoing_branch_weight(self, branch: Branch, factor: str) -> str:
        """Get scaled weight of outgoing branch"""
        # Multiply with factor
        return str(simplify(Mul(parse_factor(factor),
                                parse_weight(branch.weight, branch))))
