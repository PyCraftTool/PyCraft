# from helpers import run_test, get_completion
import ast
import copy

import helpers
import helpers_variations
from get_lhs_vars import get_undef_vars
from collections import namedtuple

TestMetadata = {
    # 'unparseable_responses': [], # response is not parseable. ex invalid json
    #  'unparseable_response_count': 0,
    'invalid_format': [],  # parseable response. response format unexpected. Ex: string instead of list
    'invalid_format_count': 0,
    'syntax_err_tests': [],  # syntax err in test case
    'syntax_err_count': 0,
    'invalid_tests': [],  # test has invalid assertion. ex: assert sum([1,2,3]) == 1
    'invalid_test_count': 0,
    'uninitialised_vars': [],  # test has some uninitialised variables, which should have been initialised
    'uninitialised_vars_count': 0,
    'proper_test_count': 0}


def get_prompt(code_str, variable_types=None, rhs_vars=None):
    r_str = f' {",".join(rhs_vars)}' if rhs_vars else ''
    types_str = f"Here are the types of the variables in the code:\n{variable_types}\n" \
        if variable_types else ''

    p = """Provide edge-cases. Consider using edge values like: [], '', None, 7.375, '    example-string    '."""
    prompt = f"""
Your task is to provide test-cases for the python code-block delimited by triple backticks. Provide edge-cases(like empty lists, empty string, strings with spaces, None, floats, float as a string, etc). Provide some cases in which the code must throw an error. Provide <=10 test-cases.
Make sure that all variables used on the right-hand side of the program are initialised.
{types_str}
Respond with two components of the test case. 
   a. Initialisation statements: Python code to initialise the variables(s) {r_str}. These must be valid python statements. 
   b. Assertion statements: Python assertion statement(s) to validate the correctness of the code. In case the test case must throw an error, respond with the string "error" here.

Format your response in JSON. Use the keys: "init", "assertions". 

Here is an example for how to perform your task:

Code-block:
value = my_dict[key]

Response:
[
    {{
       "init": "my_dict = {{'a': 1, 'b': 2, 'c': 3.125, 'e': ['1.125', '3.5', '6.75', '5.9']}}\\nkey = 'b'",
       "assertions": ["assert value == 2"]
    }},
    {{
        "init": "my_dict = {{'a': 1, 'b': 2, 'c': [None, None]}}\\nkey = 'd'",
        "assertions": "error"
    }},
    {{
        "init":"my_dict = {{1: '', 2: 'b', None: '  string  '}}\\nkey = None",
        "assertions": ["assert value == '  string  '"]
    }},
    .
    .
    .
]
   
   
```
{code_str}
```
    """

    return prompt


class BadTest(Exception):
    pass


def all_vars_exist(my_locals, vars):
    return all((v in my_locals for v in vars))


def check_testcases(code_str, input_and_assertions, rhs_vars=[]):
    metadata = copy.deepcopy(TestMetadata)

    final_tests = []
    if not isinstance(input_and_assertions, list):
        metadata['invalid_format_count'] += 1
        metadata['invalid_format'].append(input_and_assertions)
        return []

    for test in input_and_assertions:

        if not isinstance(test, dict):
            metadata['invalid_format_count'] += 1
            metadata['invalid_format'].append(test)
            continue
        ip = test.get('init')
        asserts = test.get('assertions')
        if ip is None or asserts is None:
            metadata['invalid_format_count'] += 1
            metadata['invalid_format'].append(test)
            continue
        # print(f"{ip=}")
        my_locals = {}
        try:
            ast.parse(ip)
        except:
            metadata['syntax_err_count'] += 1
            metadata['syntax_err_tests'].append(test)
            continue

        try:
            # print(f"Running {ip}")
            exec(ip, my_locals)
            # print(locals())
        except:
            print("Initialisation code is incorrect. Skipping test")
            metadata['invalid_test_count'] += 1
            metadata['invalid_tests'].append(test)
            continue

        # Check if all rhs variables have been initialised.
        if not all_vars_exist(my_locals, rhs_vars):
            print("Some variables are not initialized.")
            print(test)
            metadata['uninitialised_vars_count'] += 1
            metadata['uninitialised_vars'].append(test)
            continue

        try:
            exec(code_str, my_locals)
        except Exception as e:
            print("Code failed, normal execution. It's a failing test-case.")
            print(e)
            if (asserts != 'error'):
                metadata['invalid_test_count'] += 1
                metadata['invalid_tests'].append(test)
            else:
                metadata['proper_test_count'] += 1
            # print(locals())
            final_tests.append({
                "init": ip,
                "assertion": "assert 1==1",
                "error": True
            })
            continue

        final_asserts = []
        if asserts == 'error':
            print("skipping error test-case. Should have already thrown an error.")
            metadata['invalid_test_count'] += 1
            metadata['invalid_tests'].append(test)
            continue

        syntax_err = False
        invalid_test = False
        for a in asserts:
            # print(f"checking assertion: {a}")
            try:
                abody = ast.parse(a)
            except:
                syntax_err = True
                continue
            try:
                if (isinstance(abody.body[0], ast.Assert)):
                    exec(a, my_locals)
                    final_asserts.append(a)
                else:
                    invalid_test = True
                    continue
            except AssertionError:
                print("assertion failed, for correct code.")
                print(f"skipping assertion: {a}")
                invalid_test = True
                # raise BadTest()
            except Exception as e:
                print("assert failed for: ", str(e))
                print(a)
                invalid_test = True

                # print(locals())

        if invalid_test:
            metadata['invalid_test_count'] += 1
            metadata['invalid_tests'].append(test)
        elif syntax_err:
            metadata['syntax_err_count'] += 1
            metadata['syntax_err_tests'].append(test)
        else:
            metadata['proper_test_count'] += 1

        if (len(final_asserts) == 0):
            print("No assertions were correct. Skipping test-case.")
            print(test)
            continue
        final_tests.append({
            "init": ip,
            "assertion": "\n".join(final_asserts)
        })

    return final_tests, metadata


def find_tests(code_str, repeat_factor=2, temperature=0.5, model='gpt-3.5-turbo'):
    rhs_vars = get_undef_vars(code_str)

    tests = []
    m = {'unparseable_response_count': 0, 'unparseable_responses': []}
    for i in range(repeat_factor):
        response = None
        try:
            response = helpers.get_completion(get_prompt(code_str, rhs_vars=rhs_vars), temperature, model=model)
            tests += eval(response)
        except Exception as e:
            print(f"Failed to find tests({i}th time). ")
            print(e)
            m['unparseable_response_count'] += 1
            if response is not None:
                m['unparseable_responses'].append(response)

    checked_tests, metadata = check_testcases(code_str, tests, rhs_vars=rhs_vars)
    metadata = {**m, **metadata}
    return checked_tests, metadata


def filter_tests(code_str, tests):
    final_tests = []
    for t in tests:
        if helpers.test_variations(code_str, [t])[0]:
            final_tests.append(t)

    return final_tests

# all_tests = {}
# for c in codes:
#     print("code:")
#     print(c)
#     response = helpers.get_completion(get_prompt(c), 0.5)
#     tests = eval(response)
#     # print(tests)

#     checked_tests = check_testcases(c, tests)
#     print(checked_tests)
#     all_tests[c] = checked_tests
#     print("---end---")
