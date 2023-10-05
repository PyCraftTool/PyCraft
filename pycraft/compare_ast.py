from itertools import zip_longest
from typing import Union
import ast
import pdb
import pdb
class Compare:
    def __init__(self):
        self.inside_func = False
        self.mapped_funcs = {}

    def __do(self, node1: Union[ast.expr, list[ast.expr]], node2: Union[ast.expr, list[ast.expr]]):
        if type(node1) is not type(node2):
            return False

        if not self.inside_func:
            if isinstance(node1, ast.Name) and isinstance(node2, ast.Name):
                return True
        else:
            if isinstance(node1, ast.Name) and isinstance(node2, ast.Name):
                return node1.id == node2.id or\
                        self.mapped_funcs.get(node1.id) == node2.id or \
                        self.mapped_funcs.get(node2.id) == node1.id
        if isinstance(node1, ast.AST):
            # print(f"{len(vars(node1).items()) = }")
            for k, v in vars(node1).items():
                if k in {"lineno", "end_lineno", "col_offset", "end_col_offset", "ctx", "parent", "name"}:
                    continue
                # pdb.set_trace()
                self.inside_func = False
                if(isinstance(node1, ast.Call) and k=='func'):
                    self.inside_func = True
                if not self.__do(v, getattr(node2, k)):
                    return False
            if isinstance(node1, ast.FunctionDef):
                self.mapped_funcs[node1.name] = node2.name
            return True

        elif isinstance(node1, list) and isinstance(node2, list):
            return all(self.__do(n1, n2) for n1, n2 in zip_longest(node1, node2))
        else:
            return node1 == node2
    def do(self, node1: Union[ast.expr, list[ast.expr]], node2: Union[ast.expr, list[ast.expr]]) -> bool:
        self.mapped_funcs = {}
        return self.__do(node1, node2)