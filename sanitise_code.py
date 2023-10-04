import ast

def has_input(node):
	for w in ast.walk(node):
		if (isinstance(node, ast.Call) \
			and isinstance(node.func, ast.Name) \
			and node.func.id == 'input'):
			return True
	return False


class SanitiseCode(ast.NodeTransformer):
	def visit_Call(self, node):
		self.generic_visit(node)
		if(isinstance(node.func, ast.Name)):
			if (node.func.id == 'input'):
				return ast.Constant(value = "1234")
			elif(node.func.id == 'print'):
				return None
		return node

	def visit_Expr(self, node):
		self.generic_visit(node)
		if(hasattr(node,'value')):
			return node
		return None

