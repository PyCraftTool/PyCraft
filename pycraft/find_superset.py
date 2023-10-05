import json
import openai
import ast
import textwrap
import copy
import os

#custom functions
from get_examples import get_prompt
from get_lhs_vars import get_lhs_vars
from compare_ast import Compare

# from openai.api_requestor.error import RateLimitError, APIError
from helpers import get_completion, decode_response, double_list, extract_code_imports, test_variations
from helpers_variations import process_variants


VARIATS_LIMIT = 100
# TEMP = 0
compare_ast_fn = Compare().do




def augment_superset(correct_vars, superset):
    new_variations = False
    for nc in correct_vars:
        if all((compare_ast_fn(nc['code'], f["code"])==False for f in superset)):
            nc['correct'] = True
            nc['depth'] = 1
            # nc['temperature'] = temperature
            superset.append(nc)
            new_variations = True

    return superset, new_variations


def refine_intersection(correct_vars, intersection):
    # print(f"{intersection = }")
    if intersection is None:
        return copy.copy(correct_vars)

    new_int = []
    for i in intersection:
        if any((compare_ast_fn(i['code'], f["code"]) for f in correct_vars)):
            new_int.append(i)
    # print(f"{new_int = }")
    return new_int



def get_superset(code_str, temperature, variable_types = None, input_and_assertions = None, no_init = True):

    q = {**extract_code_imports(ast.parse(code_str)), "depth":0, "correct":True, "temperature":temperature}
    incorrect = []
    lhs_vars = get_lhs_vars(code_str)
    superset = [q]
    intersection = None
    new_variations = False
    MIN_ATTEMPTS = 3
    attempts = 1
    fix_point_reached = True


    metadata = {}
    while attempts <=3 or new_variations:
        new_variations = False
        error = False
        fix_point_reached = True
        print(f"{len(superset)=}")
        print("Searching for varitions of:\n")
        print(code_str)
        print("----end of code------")
        
        prompt = get_prompt(code_str, lhs_vars, variable_types)
        response = get_completion(prompt, temperature, key='1234')
        
        variations = []
        try:
            variations = decode_response(response)
        except:
            print("Cannot decode response, skipping")
            print(f"{response = }")
            error = True
            fix_point_reached = False
        
        # print("found", len(variations), "variations.") # add to metadata

        correct_vars, incorrect_vars = process_variants(variations, input_and_assertions,
                                                        parent_depth=0, iterations=attempts, temperature=temperature)
        superset, new_variations = augment_superset(correct_vars, superset)
        # print(f"{correct_vars =}")
        intersection = refine_intersection(correct_vars, intersection)

        key = f"run-{attempts}"
        metadata[key] = {
            "num-correct":len(correct_vars),
            "num-incorrect":len(incorrect_vars),
            "total-vars":len(correct_vars) + len(incorrect_vars),
            "union-size":len(superset),
            "intersection-size":len(intersection),
            "error":error
        }



        if(len(superset) >= VARIATS_LIMIT):
            print(f"stopping early. {VARIATS_LIMIT} variations reached.")
            fix_point_reached = False
            break

        # metadata[attempts] = len(superset)
        attempts += 1
    metadata["fix-point"] = fix_point_reached

    for f in superset:
        try:
            f["code"] = ast.unparse(f['code'])
        except AttributeError:
            print("coduln't unparse")
            print(ast.dump(f['code'], indent = 1))

        f["imports"] = ast.unparse(f["imports"])
    
    # print(f"{intersection =}")
    for f in intersection:
        if isinstance(f['code'], ast.AST):
            f["code"] = ast.unparse(f['code'])
        if isinstance(f['imports'], ast.AST):
            f["imports"] = ast.unparse(f["imports"])

    return superset, intersection, metadata





def run_all_supersets(best_practices):
    """
    collect:
    1. Intersection data.
    2. Union data.
    3. # of variants each time the question is asked.
        # correct each time. # incorrect each time
    4. size of union at each iteration.
    5. size of intersection at each iteration.
    """
    data = []
    # temps = [0, 0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1, 1.1, 1.2]
    # temps  = [0, 0.3, 0.5, 0.7, 0.9, 1]
    # temps = [0, 0.3]
    temps  = [0, 0.3, 0.5, 0.7, 0.9, 1.2]
    for i in best_practices:

        idiom = i['idiom'].lower().replace(" ", '-')
        with open(f"data/RQ2/tests/{idiom}-test.json") as f:
            tests = json.load(f)

        variable_types = i.get('variable-types')
        try:
            os.makedirs(f"data/RQ1/data/{idiom}")
        except FileExistsError:
            pass


        for t in temps:
            # TEMP = t
            t_str = str(t).replace('.', '-')
            print(f"setting temp to: {t}")
            lhs_file = f"data/RQ1/data/{idiom}/lhs-{t_str}.json"

            done = False
            try:
                with open(lhs_file) as f:
                    print("already done")
                    done = True
            except FileNotFoundError:
                done = False

            if not done:
                failed = False
                try:
                    superset, intersection, metadata = get_superset(i['example before'], t, variable_types = variable_types, input_and_assertions = tests)
                # except AttributeError:
                #     raise
                except Exception as e:
                    print(f"failed to find superset for:\n {i['example before']}")
                    print(e)
                    failed = True

                if not failed:
                    with open(lhs_file, "w") as f:
                        json.dump({\
                            "code":i['example before'], \
                            "superset": superset, \
                            "intersection": intersection, \
                            "metadata": metadata, \
                            "temperature": t \
                        }, f, indent = 1)
            

            rhs_file = f"data/RQ1/data/{idiom}/rhs-{t_str}.json"
            done = False
            try:
                with open(rhs_file) as f:
                    print("already done")
                    done = True
            except FileNotFoundError:
                done = False

            if not done:
                failed = False
                try:
                    superset, intersection, metadata = get_superset(i['example after'], t, variable_types = variable_types, input_and_assertions = tests)
                # except AttributeError:
                #     raise
                except Exception as e:
                    print(f"failed to find superset for:\n {i['example after']}")
                    print(e)
                    failed = True
                
                if not failed:
                    with open(rhs_file, "w") as f:
                        json.dump(
                            {
                                "code":i['example after'],
                                "superset": superset,
                                "intersection": intersection,
                                "metadata": metadata,
                                "temperature": t}, f, indent = 1)

            # with open("data/RQ1/superset_data.json", "w") as f:
            #     json.dump(data, f, indent = 1)


