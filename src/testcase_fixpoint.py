import copy
import json
import os
import ast

import helpers, helpers_variations
import find_testcases
from compare_ast import Compare

compare_ast_fn = Compare().do
TEMP_VALUES = [0, 0.3, 0.5, 0.7, 0.9, 1.2]

variants_directory = "data/RQ2/old/data"
testcase_directory = "data/paper/RQ2"



class UnmatchedPattern(Exception):
    pass


def dedup_variations(variations):
    fv = []
    for f in variations:
        try:
            f_ast = ast.parse(f["code"])
        except:
            continue
        if all((compare_ast_fn(
                f_ast, ast.parse(f1["code"])
        ) == False for f1 in fv)):
            # print(f["code"])
            fv.append(f)

    return fv


def get_lhs_rhs(idiom):
    with open("data/best_practices.json") as f:
        bp = json.load(f)

    i = bp.get(idiom)
    if (i is None):
        raise Exception("Idiom doesn't exist")
    return i["example before"], i["example after"]


def dedup_tests(tests):
    new_tests = []
    for t in tests:
        if (any((t['init'] == nt['init'] and t['assertion'] == nt['assertion']
                 for nt in new_tests))):
            continue
        new_tests.append(t)
    return new_tests


def unwrap_ast(variants):
    new_vars = []
    for f in variants:
        nf = copy.copy(f)
        if (isinstance(f['code'], ast.AST)):
            nf["code"] = ast.unparse(f['code'])
        if (isinstance(f['imports'], ast.AST)):
            nf["imports"] = ast.unparse(f["imports"])
        new_vars.append(nf)

    return new_vars


def test_case_fix_point(idiom, all_variants, lhs, rhs, model='gpt-3.5-turbo'):
    MAX_CHANCES = 3
    # lhs, rhs = get_lhs_rhs(idiom)

    temps = TEMP_VALUES
    for temp in temps:
        tests = []
        metadata = {"temperature": temp}
        count = 1
        mt_file = f"{testcase_directory}/{model}/{idiom}-test-meta-{temp}.json"
        chances = MAX_CHANCES
        changed = True
        num_correct = len(all_variants) + 1
        conflicting_tests = []
        try:
            with open(mt_file) as f:
                print("file exists, skipping.")
                continue
        except FileNotFoundError:
            pass
        while changed or chances:
            print(f"Searching for tests ({count} time).")
            changed = False
            # for code_str in [lhs]:
            new_tests, test_metadata = find_testcases.find_tests(lhs, repeat_factor=1, temperature=temp, model=model)
            tests += new_tests
            print(f"{len(new_tests)=}")

            tests = dedup_tests(tests)

            # f_tests = []
            # for t in tests:
            #     if not helpers.test_variations(lhs, [t])[0]:
            #         # raise UnmatchedPattern("Test failed for LHS")
            #         print("Skipping test. Fails on LHS.")
            #         conflicting_tests.append(t)
            #     elif not helpers.test_variations(rhs, [t])[0]:
            #         print("Skipping test. Fails on RHS.")
            #         conflicting_tests.append(t)
            #     else:
            #         f_tests.append(t)
            # tests = f_tests

            correct_vars, incorrect_vars = helpers_variations.process_variants(all_variants,
                                                                               input_and_assertions=tests,
                                                                               temperature=0, iterations=0,
                                                                               # these params do not matter
                                                                               parent_depth=0)

            print(f"{len(tests)=}")
            print(f"{len(correct_vars) = }")
            print(f"{len(incorrect_vars) = }")
            if len(correct_vars) < num_correct:
                num_correct = len(correct_vars)
                changed = True
                chances = MAX_CHANCES
            elif chances > 0:
                chances -= 1

            metadata[f"iteration-{count}"] = {
                "num-tests": len(tests),
                "num-correct": len(correct_vars),
                "num-incorrect": len(incorrect_vars),
                "num-conflict-tests": len(conflicting_tests),
                "tests": copy.copy(tests),
                "conflict-tests": copy.copy(conflicting_tests),
                "correct_vars": unwrap_ast(correct_vars),
                "incorrect_vars": unwrap_ast(incorrect_vars),
                "metadata": copy.copy(test_metadata)
            }
            count += 1

        with open(mt_file, "w") as f:
            json.dump(metadata, f, indent=1)





if __name__ == '__main__':

    model = 'gpt-3.5-turbo'

    # ignored_idioms = ['tuple-unpacking', 'set-union', 'numpy-sum',
    #                   'multiple-variables-assignment', 'dict-update',
    #                   'conditional-assignment', 'assign-to-slice',
    #                   'assign-to-slice', 'catch-all-unpacking',
    #                   'assign-multiple-targets', 'set-intersection', 'swapping-variables',
    #                   'combined-comparison', 'zip-traversing',
    #                   'unzipping-sequence', 'building-dictionaries', 'truth-value-test',
    #                   'collections-defaultdict', 'collections-counter',
    #                   'any-func', 'getattr', 'hasattr']

    ignored_idioms = ['swapping-variables', 'combined-comparison']
    with open("data/best_practices10.json") as f:
        best_practices = json.load(f)

    variant_files = os.listdir(variants_directory)
    testcase_files = os.listdir(f"{testcase_directory}/{model}")

    for bp in best_practices:
        idiom = bp['idiom'].replace(' ', '-').lower()

        m_files = [f"{idiom}-test-meta-{temp}.json" for temp in TEMP_VALUES]
        if (all((m in testcase_files for m in m_files))):
            print(f"All files found. {idiom}")
            print([i for i in testcase_files if i in m_files])
            continue
        if idiom in ignored_idioms:
            print(f"Skipping; {idiom}")
            continue
        print(f"IDIOM: {idiom}")

        lhs, rhs = bp['example before'], bp['example after']
        idiom_variants = [i for i in variant_files if idiom in i and 'metadata' not in i]
        print(f"{len(idiom_variants) = }")

        incorrect_v_files = [i for i in idiom_variants if 'incorrect' in i]
        correct_v_files = [i for i in idiom_variants if i not in incorrect_v_files]

        all_correct = []
        for cf in correct_v_files:
            with open(f"{variants_directory}/{cf}") as f:
                c_vars = json.load(f)
                all_correct += c_vars
        all_correct = dedup_variations(all_correct)
        all_correct = ["\n".join([i['imports'], i['code']]) for i in all_correct]

        all_incorrect = []
        for cf in incorrect_v_files:
            with open(f"{variants_directory}/{cf}") as f:
                ic_vars = json.load(f)
                all_incorrect += ic_vars
        all_incorrect = dedup_variations(all_incorrect)
        all_incorrect = ["\n".join([i['imports'], i['code']]) for i in all_incorrect]

        try:
            test_case_fix_point(idiom, all_correct + all_incorrect, lhs, rhs, model = model)
        except UnmatchedPattern:
            ignored_idioms.append(idiom)
