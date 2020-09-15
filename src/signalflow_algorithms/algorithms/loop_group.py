from typing import List
from signalflow_algorithms.algorithms.graph import Branch, Node


class LoopGroup(object):
    def __init__(self, loop_count=0, loops=list(), nodes=list()):
        self.loop_count = loop_count
        self.loops: List[List[Branch]] = loops
        self.nodes: List[Node] = nodes

    def append_loop(self, loops: List[List[Branch]], nodes: List[Node]):
        """Append new loop to LoopGroup and return new group"""
        next_loops = list(loops)
        next_loops.extend(self.loops)
        next_nodes = list(nodes)
        next_nodes.extend(self.nodes)
        return LoopGroup(self.loop_count + 1,
                         next_loops,
                         next_nodes)


def find_loop_groups(loops: List[List[Branch]]) -> List[LoopGroup]:
    """Build all groups of loops with no nodes in common"""
    return list(__find_loop_groups(LoopGroup(), loops[:]))


def __find_loop_groups(loop_group: LoopGroup,
                       available_loops: List[List[Branch]]):

    # Do not output empty results (on first call)
    if loop_group.loop_count:
        yield loop_group

    while available_loops:
        next_loop = available_loops.pop(0)

        next_loop_nodes: List[Node] = []
        for branch in next_loop:
            next_loop_nodes.append(branch.start)
            next_loop_nodes.append(branch.end)

        if len(__intersect(loop_group.nodes, next_loop_nodes)) == 0:
            yield from __find_loop_groups(
                loop_group.append_loop([next_loop], next_loop_nodes),
                available_loops[:])


def __intersect(a, b):
    if a is None or b is None:
        return list()

    return [item for item in a if item in b]
