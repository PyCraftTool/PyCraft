import ast
import pdb


class InsideFunction(ast.NodeVisitor):

    enclosing_types = [ast.Attribute, ast.Call]
    def __init__(self, var_name):
        super(InsideFunction).__init__()
        self.var_name = var_name
        self.import_err = False
        # self.found_name = False

    def generic_visit(self, node):
        """Called if no explicit visitor function exists for a node."""
        for field, value in ast.iter_fields(node):
            if isinstance(value, list):
                for item in value:
                    if isinstance(item, ast.AST):
                        if self.visit(item) and type(node) in InsideFunction.enclosing_types:
                            self.import_err = True

            elif isinstance(value, ast.AST):
                if self.visit(value) and type(node) in InsideFunction.enclosing_types:
                    self.import_err = True


    # def visit(self, node):
    #     fn = getattr(self, f'visit_{node.__class__.__name__}', self.generic_visit)
    #     fn(node)
    #     if self.found_name and (not isinstance(node, ast.Name)):
    #         print("here")
    #         pdb.set_trace()
    #         if isinstance(node, ast.Call) or isinstance(node, ast.Attribute):
    #             self.import_err = True
    #         self.found_name = False

    def visit_Name(self, node):
        self.generic_visit(node)
        if node.id == self.var_name:
            # print(f"found {self.var_name}")
            # self.found_name = True
            return True
        return False

def is_import_err(code_str, error_str):
    try:
        var_name = error_str.split("name '")[1].split("'")[0]
        # print(var_name)
    except:
        return False

    i = InsideFunction(var_name)
    i.visit(ast.parse(code_str))
    return i.import_err