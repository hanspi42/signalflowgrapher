from typing import List
from signalflow_algorithms.algorithms.graph import Node, Branch
import uuid


def find_paths(start: Node, end: Node) -> List[List[Branch]]:
    """Returns list with all simple paths \
    between start node and end node"""
    return __find_paths_inner(start, end, [])


def __find_paths_inner(start: Node,
                       end: Node,
                       visited: List[uuid.UUID]) -> List[List[Branch]]:
    results = []
    visited.append(start.id)

    for branch in start.outgoing:
        target = branch.end
        # Target found, append result
        if target.id == end.id:
            path: List[Branch] = [branch]
            results.append(path)
        else:
            if target.id not in visited:
                paths = __find_paths_inner(target, end, visited)
                # Add found paths
                for path in paths:
                    pathNew = []
                    pathNew.append(branch)
                    pathNew.extend(path)
                    results.append(pathNew)

    # Remove self from visited, to allow visit again in other path
    visited.remove(start.id)
    return results
