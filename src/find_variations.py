import json
import openai
import ast
import textwrap
import copy
import time
import os

# custom functions
from get_examples import get_prompt
from get_lhs_vars import get_lhs_vars
from compare_ast import Compare

from helpers import get_completion, decode_response, \
    double_list, extract_code_imports, test_variations, \
    multiply_list, dedup_variations
from find_testcases import find_tests, filter_tests
import data_flow_prompt
from helpers_variations import process_variants

# from openai.api_requestor.error import RateLimitError, APIError

VARIANTS_LIMIT = 100
# TEMP = 0
compare_ast_fn = Compare().do


def find_all_lhs_vars(starting_vars):
    lhs_vars = set()
    for s in starting_vars:
        lhs_vars = lhs_vars.union(get_lhs_vars(s))
    return lhs_vars


def unwrap_asts(variations):
    for f in variations:
        if (isinstance(f['code'], ast.AST)):
            f["code"] = ast.unparse(f['code'])
        if (isinstance(f['imports'], ast.AST)):
            f["imports"] = ast.unparse(f["imports"])


# def dedup_variations(variations):
#     fv = []
#     for f in variations:
#         if all((compare_ast_fn(f["code"], f1["code"]) == False for f1 in fv)):
#             # print(f["code"])
#             fv.append(f)
#
#     return fv


def create_metadata(metadata, \
                    correct_vars, incorrect_vars, \
                    iterations, parent_depth, \
                    all_correct, all_incorrect, i_start,\
                    **kwargs):
    key = f"iteration-{iterations}"
    cv_copy = copy.deepcopy(correct_vars)
    iv_copy = copy.deepcopy(incorrect_vars)
    i_end = time.time()

    ac_copy = copy.deepcopy(all_correct)
    aic_copy = copy.deepcopy(all_incorrect)
    unwrap_asts(cv_copy)
    unwrap_asts(iv_copy)
    unwrap_asts(ac_copy)
    unwrap_asts(aic_copy)
    metadata[key] = {
        "correct-vars": cv_copy,
        "all-correct": ac_copy,
        "incorrect-vars": iv_copy,
        "all-incorrect": aic_copy,
        "depth": parent_depth + 1,
        "num-correct": len(correct_vars),
        "num-incorrect": len(incorrect_vars),
        "num-all-correct": len(all_correct),
        "num-all-incorrect": len(all_incorrect),
        "time-taken": i_end - i_start
    }
    metadata[key].update(kwargs)



"""
COllect for each iteration:
1. # of variants
    # correct each time. # incorrect each time
2. Depth
3. actual Correct and incorrect variations
"""


def get_all_variations(starting_vars,
                       temperature, variable_types=None,
                       input_and_assertions=None,
                       repeat_factor=3, max_depth=2,
                       labelled_variants = None, model='gpt-3.5-turbo'):
    start_time = time.time()

    iterations = 0
    rerun = False
    q = [
        {**extract_code_imports(ast.parse(s)), "depth": 0, "correct": True, "temperature": temperature, "iterations": 0} \
        for s in starting_vars]

    q[0]['applicable'] = True
    q[1]['applicable'] = False

    q = multiply_list(q, repeat_factor)
    incorrect = []
    final_variations = []

    lhs_vars = find_all_lhs_vars(starting_vars)
    lhs_str = starting_vars[0]

    metadata = {
        "temperature": temperature,
        "repeat_factor": repeat_factor,
        "max_depth": max_depth
    }

    while len(q):
        iterations += 1
        i_start = time.time()
        print(len(final_variations), "final variations found.")
        print(len(q), "items left in queue.")
        var = q.pop(0)
        code = ast.Module(
            body=var["imports"].body + var['code'].body,
            type_ignores=[])
        code_str = ast.unparse(code)
        print("Searching for varitions of:\n")
        print(code_str)
        print("----end of code------")

        prompt = get_prompt(code_str, lhs_vars, variable_types)
        # prompt = data_flow_prompt.get_prompt(code_str)
        api_error = False
        api_error_str = ''
        try:
            response = get_completion(prompt, temperature, model=model)
        except (openai.api_requestor.error.APIError, \
                openai.api_requestor.error.ServiceUnavailableError, \
                openai.error.APIConnectionError) as e:
            print("API request failed. Skipping")
            api_error = True
            api_error_str = f"{type(e)}: {str(e)}"
        except openai.error.RateLimitError:
            print("RateLimitError! Waiting for a 30s.")
            time.sleep(30)
            api_error = True
            api_error_str = f"{type(e)}: {str(e)}"
        except TimeoutError:
            print("Api request timed out. :/")
            api_error = True
            api_error_str = f"{type(e)}: {str(e)}"

        if api_error:
            create_metadata(metadata,\
                            [], [], \
                            iterations, var["depth"], \
                            all_correct=dedup_variations(final_variations + q),
                            all_incorrect=incorrect,
                            i_start=i_start,
                            api_error=True, api_error_str=api_error_str
                            )
            print(api_error_str)
            continue

        try:
            variations = decode_response(response)
        except:
            print("Cannot decode response, skipping")
            print(f"{response = }")
            create_metadata(metadata, \
                            [], [], \
                            iterations, var["depth"], \
                            all_correct=dedup_variations(final_variations + q),
                            all_incorrect=incorrect,
                            i_start=i_start,
                            invalid_respnse_format=True
                            )
            if (all((compare_ast_fn(code, f["code"]) == False for f in final_variations))):
                final_variations.append(var)
            continue

        print("found", len(variations), "variations.")

        correct_vars, incorrect_vars = process_variants(variations, input_and_assertions,
                                                        var['depth'], iterations, temperature,
                                                        lhs_str=lhs_str, labelled_variants=labelled_variants)
        # all((compare_ast_fn(nc['code'], f["code"])==False for f in incorrect)) and \
        for nc in correct_vars:
            if all((compare_ast_fn(nc['code'], f["code"]) == False for f in final_variations)) and \
                    all((compare_ast_fn(nc['code'], f["code"]) == False for f in q)) and \
                    compare_ast_fn(var['code'], nc['code']) == False:
                if (repeat_factor == 0):
                    final_variations.append(nc)
                else:
                    if (var['depth'] < max_depth):
                        for _ in range(repeat_factor):
                            q.append(nc)
                    else:
                        final_variations.append(nc)
        for nc in incorrect_vars:
            if all((compare_ast_fn(nc['code'], f["code"]) == False for f in incorrect)):
                incorrect.append(nc)

        if (all((compare_ast_fn(var["code"], f["code"]) == False for f in final_variations))):
            final_variations.append(var)

        create_metadata(metadata, \
                        correct_vars, incorrect_vars, \
                        iterations, var["depth"], \
                        all_correct=dedup_variations(final_variations + q),
                        all_incorrect=incorrect,
                        i_start=i_start
                        )

        if (len(final_variations) + (0 if repeat_factor == 0 else len(q) // repeat_factor) >= VARIANTS_LIMIT):
            print(f"stopping early. {VARIANTS_LIMIT} variations reached.")
            break

    final_variations += q
    final_variations = dedup_variations(final_variations)

    unwrap_asts(final_variations)
    unwrap_asts(incorrect)

    end_time = time.time()

    metadata["time-taken"] = end_time - start_time

    return final_variations, incorrect, metadata


# def find_variants(starting_vars, variable_types, temperature):
#     tests = find_tests(starting_vars[0])

#     variations = get_all_variations(starting_vars, 
#         variable_types = variable_types, 
#         input_and_assertions = tests,
#         temperature = temperature
#         )
#     return variations


def get_lhs_rhs_tests(lhs, rhs):
    tests = []
    RF = 2
    TEMP = 0.5
    for _ in range(RF):  # repeat 5 times
        t, _ = find_tests(lhs, repeat_factor=1, temperature=TEMP)
        tests += t
        # tests = filter_tests(rhs, tests)
        #
        # tests += find_tests(rhs, repeat_factor=1, temperature=TEMP)
        # tests = filter_tests(lhs, tests)

    return tests


with open("data/best_practices10.json") as f:
    best_practices = json.load(f)

model = 'gpt-4'
repeat_factor = 2
max_depth = 100
use_tests = False # use tests to guide the fix-point iteration.
variants_directory = "data/paper/RQ1/data"
labels_directory = "data/RQ2/labelled"
# variants_directory = "data/RQ2" #old directory
tests_dir = "data/RQ2/tests"
for bp in best_practices[6:]:
    # count+=1
    starting_vars = [bp['example before'], bp['example after']]
    print("code:")
    print(starting_vars[0])
    variable_types = bp.get('variable-types')
    print("variable_types---", variable_types)
    idiom = bp['idiom'].lower().replace(' ', '-')
    print(idiom)

    tests_path = f"{tests_dir}/{idiom}-test.json"
    labels_path = f"{labels_directory}/{idiom}.json"

    tests = []
    if use_tests:
        try:
            with open(tests_path) as f:
                tests = json.load(f)
            print("loaded tests from file!")
        except FileNotFoundError:
            print("Asking chatgpt for tests.")
            # tests = find_tests(starting_vars[0])
            tests = get_lhs_rhs_tests(starting_vars[0], starting_vars[1])
            with open(tests_path, "w") as f:
                json.dump(tests, f, indent=1)

        if (len(tests) == 0):
            print("Skipping. No tests.")
            continue

    try:
        with open(labels_path) as f:
            labelled_variants = json.load(f)
    except FileNotFoundError:
        labelled_variants = None

    # for t in [0, 0.3, 0.5, 0.7, 0.9, 1.2]:
    for t in [0, 0.3]:

        # variations_file = f"data/RQ2/data/{idiom}-temp-{t}.json"
        variations_file = f"{variants_directory}/{model}/{idiom}-temp-{t}-rf-{repeat_factor}.json"
        incorrect_file = f"{variants_directory}/{model}/{idiom}-incorrect-temp-{t}-rf-{repeat_factor}.json"
        metadata_file = f"{variants_directory}/{model}/{idiom}-metadata-temp-{t}-rf-{repeat_factor}.json"

        try:
            with open(metadata_file) as f:
                print("variants for this temp exists.")
            continue
        except FileNotFoundError:
            print("searching for variants!")

        variations, incorrect, metadata = get_all_variations(starting_vars,
                                                             variable_types=variable_types, temperature=t,
                                                             input_and_assertions=tests, repeat_factor=repeat_factor,
                                                             max_depth=max_depth,
                                                             labelled_variants=labelled_variants,
                                                             model=model)
        with open(variations_file, "w") as f:
            json.dump(variations, f, indent=1)
        with open(incorrect_file, "w") as f:
            json.dump(incorrect, f, indent=1)
        with open(metadata_file, "w") as f:
            json.dump(metadata, f, indent=1)
        # break
    # if(count >1):
    # break
