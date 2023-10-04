import ast
import pylint
import tempfile
import json
import re

def get_undef_vars(code):
    ERR_CODE = 'E0602'

    code_file = tempfile.NamedTemporaryFile("w", prefix='code_')
    code_file.write(code)
    code_file.flush()
    pylint_out = tempfile.NamedTemporaryFile("w", prefix='pylint_')
    # pylint_out.close()
    try:
        pylint.run_pylint(["pylint", code_file.name,
                       "--errors-only", "--disable=all",
                       "--enable=E0602", "--output-format=json", f"--output={pylint_out.name}"])
    except SystemExit:
        pass

    with open(pylint_out.name) as f:
        out_data = json.loads(f.read())

    pylint_out.close()
    code_file.close()

    undef_vars = set()
    for d in out_data:
        if(d['message-id'] == ERR_CODE):
            var_name = re.findall('\'([^"]*)\'', d['message'])[0]
            undef_vars.add(var_name)

    return undef_vars


def get_lhs_vars(code):
    a = ast.parse(code)
    w = WriteVars()
    w.visit(a)

    return w.write_vars


class WriteVars(ast.NodeVisitor):

    def __init__(self):
        self.write_vars = set()
        self.lhs = False

    def visit_Assign(self, node):

        old_lhs = self.lhs

        self.lhs = True
        for t in node.targets:
            self.visit(t)
        self.lhs = False
        self.visit(node.value)

        self.lhs = old_lhs

    def visit_AnnAssign(self, node):

        old_lhs = self.lhs

        self.lhs = True
        self.visit(node.target)

        self.lhs = False
        self.visit(node.value)

        self.lhs = old_lhs

    def visit_Name(self, node):

        if (self.lhs):
            self.write_vars.add(node.id)
        self.generic_visit(node)
