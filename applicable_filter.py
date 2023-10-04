import ast
from _ast import If, While, For
from typing import Any


class ControlNodes(ast.NodeVisitor):
    # comps = [ast.ListComp, ast.GeneratorExp, ast.DictComp, ast.SetComp]
    comps = [ast.comprehension]
    for_nodes = [ast.For, ast.While] + comps
    if_nodes = [ast.If, ast.IfExp]

    def __init__(self):
        self.for_count = 0
        self.if_count = 0

    def visit(self, node):
        if any((isinstance(node, ft) for ft in ControlNodes.for_nodes)):
            self.for_count += 1

        if any((isinstance(node, inode) for inode in ControlNodes.if_nodes)):
            self.if_count += 1

        if isinstance(node, ast.comprehension) and len(node.ifs):
            self.if_count += 1
        super().visit(node)


def compare_structures(lhs_str, code_str):
    ast1 = ast.parse(lhs_str)
    ast2 = ast.parse(code_str)

    cn1 = ControlNodes()
    cn1.visit(ast1)
    cn2 = ControlNodes()
    cn2.visit(ast2)

    return cn1.if_count <= cn2.if_count and cn1.for_count <= cn2.for_count
