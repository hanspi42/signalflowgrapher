# Original version from
# https://github.com/qpwo/python-simple-cycles/blob/master/johnson.py

# A dependency-free version of networkx's implementation
# of Johnson's cycle finding algorithm
# Original implementation:
# https://github.com/networkx/networkx/blob/master/networkx/algorithms/cycles.py#L109
# Original paper: Donald B Johnson. "Finding all the elementary circuits of a
# directed graph." SIAM Journal on Computing. 1975.

from collections import defaultdict
from typing import List
from signalflow_algorithms.algorithms.graph import Graph, Branch
from signalflow_algorithms.algorithms.tarjan import (
    strongly_connected_components)


def simple_cycles(g: Graph) -> List[List[Branch]]:
    """Find all simple cycles in a graph"""
    # Make copy because the graph gets altered during the algorithm
    graph_copy = g.copy()
    branch_map = {}
    copy_result = list()

    # Create map to allow returning original branches
    for branch in g.branches:
        branch_map[branch.id] = branch

    # Yield every elementary cycle in python graph G exactly once
    # Expects a dictionary mapping from vertices to iterables of vertices
    def _unblock(thisnode, blocked, B):
        stack = set([thisnode])
        while stack:
            node = stack.pop()
            if node in blocked:
                blocked.remove(node)
                stack.update(B[node])
                B[node].clear()
    sccs = [(graph_copy, scc) for scc in
            strongly_connected_components(graph_copy)]
    while sccs:
        current_graph, scc = sccs.pop()
        startnode = scc.pop()
        path = [startnode.id]
        pathBranches = []
        blocked = set()
        closed = set()
        blocked.add(startnode.id)
        B = defaultdict(set)
        stack = [(startnode, list(startnode.outgoing))]
        while stack:
            thisnode, nbrs = stack[-1]
            if nbrs:
                branch = nbrs.pop()
                nextnode = branch.end
                if nextnode.id == startnode.id:
                    result = pathBranches[:]
                    result.append(branch)
                    copy_result.append(result)
                    closed.update(path)
                elif nextnode.id not in blocked:
                    path.append(nextnode.id)
                    pathBranches.append(branch)
                    stack.append((nextnode,
                                  list(nextnode.outgoing)))
                    closed.discard(nextnode.id)
                    blocked.add(nextnode.id)
                    continue
            if not nbrs:
                if thisnode.id in closed:
                    _unblock(thisnode.id, blocked, B)
                else:
                    for nbr in map(lambda x: x.end,
                                   thisnode.outgoing):
                        if thisnode.id not in B[nbr.id]:
                            B[nbr.id].add(thisnode.id)
                stack.pop()
                path.pop()
                if (pathBranches):
                    pathBranches.pop()
        startnode.remove()
        subgraph = current_graph.subgraph(set(scc))
        new_scc = strongly_connected_components(subgraph)
        sccs.extend([(subgraph, scc) for scc in new_scc])

    for loop in copy_result:
        yield list(map(lambda b: branch_map[b.id], loop))
