import ast
import textwrap
from helpers import extract_code_imports, test_variations
from applicable_filter import compare_structures


def find_label(variant, labelled_variants):
    for l in labelled_variants:
        l_code = l['variant']
        if l_code == variant:
            return l['useful'] == 'TRUE'
    return 'unknown'


def process_variants(variations: list[str], input_and_assertions: object,
                     parent_depth: int, iterations: int, temperature: float,
                     lhs_str: str = None, labelled_variants=None) -> object:
    correct_vars = []
    incorrect_vars = []
    for c in variations:
        try:
            c_ast = ast.parse(textwrap.dedent(c))
        except Exception as e:
            print("Unable to parse. Skipping")
            print(c)
            incorrect_vars.append(
                {'code': str(c), 'imports': '', 'depth': parent_depth+1, 'iterations': iterations, 'temperature': temperature,
                 'correct': False, 'error_str': f"{type(e)}:{str(e)}", 'syntax_error': True}
            )
            continue

        nc = extract_code_imports(c_ast)
        correct = "unknown"

        nc['depth'] = parent_depth+1
        nc['iterations'] = iterations
        nc['temperature'] = temperature
        if labelled_variants:
            nc['useful'] = find_label('\n'.join([ast.unparse(nc['imports']), ast.unparse(nc['code'])]), labelled_variants)

        if(input_and_assertions):
            correct, e, *rest = test_variations(c, input_and_assertions)
            

        if(correct):
            correct_vars.append(nc)
            nc['correct'] = True
            if lhs_str:
                try:
                    app = compare_structures(lhs_str, c)
                except:
                    app = False
                nc['applicable'] = app
        else:
            incorrect_vars.append(nc)
            nc['correct'] = False
            error_str = f"{type(e)}:{str(e)}"
            nc['error_str'] = error_str
    return correct_vars, incorrect_vars