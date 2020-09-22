from typing import Set
from signalflowgrapher.model.model import Branch, Node
from signalflowgrapher.io.file import write_file, read_file
from os.path import dirname, join, isfile
from shutil import copyfile
from sympy import latex
from sympy.parsing.sympy_parser import parse_expr
from sympy.abc import _clash
import logging
logger = logging.getLogger(__name__)


class TikZExport(object):
    def __init__(self):
        super().__init__()

    def write_tikz(self, nodes: Set[Node], branches: Set[Branch], path):
        """
        Write tikz export to file at given path. All nodes and branches that
        should be exported must be included in the given sets.
        """
        tikz = self.__generate_tikz(nodes, branches)
        content = self.__get_prefix() + "\n"\
                                      + "\n".join(tikz) + "\n" \
                                      + self.__get_suffix()
        write_file(path, content)

        # Copy style to same folder if not existing
        source_path = "signalflowgrapher/ressources/tikz/sfgstyle.tex"
        target_path = join(dirname(path), "sfgstyle.tex")
        if (not isfile(target_path)):
            try:
                logger.debug("Copy file %s to %s",
                             source_path,
                             target_path)
                copyfile(source_path,
                         target_path)
            except IOError as e:
                logger.error("IO error while copying %s to %s: %s",
                             source_path,
                             target_path,
                             str(e))
                raise
            except Exception as e:
                logger.fatal("Unexpected error while copying %s to %s: %s",
                             source_path,
                             target_path,
                             str(e))
        else:
            logger.debug("File %s already existing, do not copy", target_path)

    def __get_prefix(self):
        return read_file("signalflowgrapher/ressources/tikz/prefix.tex")

    def __get_suffix(self):
        return read_file("signalflowgrapher/ressources/tikz/suffix.tex")

    def __generate_tikz(self, nodes: Set[Node], branches: Set[Branch]):
        # Generate comment headers and call export for branches and nodes
        content = []
        content.append("\n")

        content.append("%~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~")
        content.append("% Set Nodes")
        content.append("%~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~")
        content.extend(self.__get_nodes_code(nodes))
        content.append("\n")

        content.append("%~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~")
        content.append("% Set Branches")
        content.append("%~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~")
        content.extend(self.__get_branches_code(branches, nodes))
        content.append("\n")
        return content

    def __get_nodes_code(self, nodes: Set[Node]):
        # Generate TikZ code for nodes
        code = []
        for index, node in enumerate(nodes, start=1):
            code.append("\\node[Node] (N%s) at (%s, %s) {};"
                        % (index, node.x, node.y))
            code.append("\\node[NodeName] at ($ (N%s) + (%s, %s) $) {%s};\n"
                        % (index,
                           node.label_dx,
                           node.label_dy,
                           self.__latex_name(node.name)))
        return code

    def __get_branches_code(self, branches: Set[Branch], nodes: Set[Node]):
        # Generate TikZ code for branches
        code = []
        nodes_list = list(nodes)
        for index, branch in enumerate(branches, start=1):
            index_start = nodes_list.index(branch.start) + 1
            index_end = nodes_list.index(branch.end) + 1
            code.append("%%Branch from Node N%s to Node N%s"
                        % (index_start, index_end))
            code.append("\\draw [->-, Connection, MarkMiddle=%s] (N%s) .."
                        "controls(%s, %s) and (%s, %s) .. (N%s);"
                        % (index, index_start,
                           branch.spline1_x,
                           branch.spline1_y,
                           branch.spline2_x,
                           branch.spline2_y,
                           index_end))
            code.append("\\node[ArrowName] at"
                        "($ (middle_%s) + (%s, %s) $) {%s};\n"
                        % (index, branch.label_dx,
                           branch.label_dy, self.__latex_name(branch.weight)))
        return code

    def __latex_name(self, name: str) -> str:
        if name=="":
            latex_notation=""
        else:
            latex_notation = latex(parse_expr(name, local_dict=_clash),
                                       mode="inline")
        return(latex_notation)
    