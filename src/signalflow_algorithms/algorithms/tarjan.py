from typing import List
from signalflow_algorithms.algorithms.graph import Graph, Node

# EXTERNAL CODE
# Implementation from
# http://www.logarithmic.net/pfh/blog/01208083168


def strongly_connected_components(graph: Graph) -> List[List[Node]]:
    """Find and reutrn all sccs in a graph"""
    # Tarjan's algorithm for finding SCC's
    # Robert Tarjan. "Depth-first search and linear graph algorithms."
    # SIAM journal on computing. 1972.
    # Code by Dries Verdegem, November 2012
    # Downloaded from http://www.logarithmic.net/pfh/blog/01208083168

    index_counter = [0]
    stack = []
    lowlink = {}
    index = {}
    result = []

    def _strong_connect(node: Node):
        index[node] = index_counter[0]
        lowlink[node] = index_counter[0]
        index_counter[0] += 1
        stack.append(node)

        successors = node.outgoing
        for successor in successors:
            if successor.end not in index:
                _strong_connect(successor.end)
                lowlink[node] = min(lowlink[node], lowlink[successor.end])
            elif successor.end in stack:
                lowlink[node] = min(lowlink[node], index[successor.end])

        if lowlink[node] == index[node]:
            connected_component = []

            while True:
                successor = stack.pop()
                connected_component.append(successor)
                if successor == node:
                    break
            result.append(connected_component[:])

    for node in graph.nodes:
        if node not in index:
            _strong_connect(node)

    return result
