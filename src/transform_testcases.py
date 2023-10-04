import json
import os
import textwrap
import subprocess

def get_func_str(func_name, init, lhs, assertions):
    init_str = textwrap.indent(init, ' '*4)
    lhs_str = textwrap.indent(lhs, ' ' * 4)
    assertions_str = textwrap.indent(assertions, ' ' * 4)

    return f"""
def {func_name}():
{init_str}
{lhs_str}
{assertions_str}
"""

def get_func_str_error(func_name, init, lhs, assertions):
    init_str = textwrap.indent(init, ' '*4)
    lhs_str = textwrap.indent(lhs, ' ' * 8)
    assertions_str = textwrap.indent(assertions, ' ' * 8)

    return f"""
def {func_name}():
{init_str}
    try:
{lhs_str}
    except:
{assertions_str}
    else:
        raise Exception("test should have failed.")
"""


def get_lhs_func(lhs):
    pass

def get_test_funcs(tests):
    test_funcs = []
    for i, t in enumerate(tests):
        func = get_func_str
        if (t.get('error')):
            func = get_func_str_error
        test_funcs.append(
            func(
                f"test_{i}",
                t['init'],
                lhs_call,
                t['assertion']
            )
        )
    return test_funcs


def skip_test(code, func_name):
    code_split = code.split(f"def {func_name}()")
    if(len(code_split)!=2):
        return code
    return f"""
{code_split[0]}
@pytest.mark.skip(reason="no way of currently testing this")
def {func_name}(){code_split[1]}
"""


if __name__ == '__main__':
    with open("data/best_practices20.json") as f:
        best_practices = json.load(f)

    cwd = os.getcwd()
    mutation_failed = []

    # tests_dir = "data/RQ3/"
    model = 'gpt-3.5-turbo'
    tests_dir = f"data/paper/RQ2/{model}"
    test_meta_files = os.listdir(tests_dir)

    for bp in best_practices:
        lhs_func, lhs_call = bp['idiom'].replace('-', '_'), bp['lhs_call']
        init_code = ["import pytest", f"from {lhs_func} import {lhs_func}"]

        idiom = bp['idiom']
        test_files = [i for i in test_meta_files if idiom in i]

        os.chdir(cwd)

        for testf in test_files:
            os.chdir(cwd)
            with open(f"{tests_dir}/{testf}") as f:
                ti = json.load(f)
            iteration_keys = [i for i in ti.keys() if i.startswith("iteration-")]
            for it in iteration_keys:
                code_arr = init_code + get_test_funcs(ti[it]['tests'])

                os.chdir(cwd)
                with open(f"{tests_dir}/pytest_files/{lhs_func}/test_{lhs_func}.py", "w") as f:
                    f.write(
                        "\n\n".join(code_arr)
                    )
                idiom_lower = bp['idiom'].replace('-', '_')
                os.chdir(f"{tests_dir}/pytest_files/{idiom_lower}/")
                try:
                    os.remove(".mutmut-cache")
                except FileNotFoundError:
                    pass

                test_baseline = subprocess.run(["pytest", "--quiet"], stdout=subprocess.PIPE)
                if test_baseline.returncode != 0:
                    out_str = test_baseline.stdout.decode('utf-8')
                    if("no tests ran" not in out_str):
                        failed_str = out_str.split("short test summary info")[1].split("FAILED")[1:]
                        failed_funcs = [i.split('::')[1].split()[0] for i in failed_str]

                        with open(f"test_{idiom_lower}.py") as f:
                            test_code = f.read()

                        for ff in failed_funcs:
                            test_code = skip_test(test_code, ff)
                        with open(f"test_{idiom_lower}.py", "w") as f:
                            f.write(test_code)

                result = subprocess.run(["mutmut", "run",
                                         "--paths-to-mutate", f"{idiom_lower}.py",
                                         "--tests-dir", f"test_{idiom_lower}.py", "--CI",
                                         "--swallow-output"])
                if (result.returncode != 0):
                    # raise Exception("mutation testing failed")
                    ti[it]["mutations-survived"] = True
                    mutation_failed.append(idiom)
                else:
                    ti[it]["mutations-survived"] = False
            os.chdir(cwd)
            with open(f"data/RQ3/{testf}", "w") as f:
                json.dump(ti, f, indent=1)





# for bp in best_practices:
#     os.chdir(cwd)
#     idiom_lower = bp['idiom'].replace('-', '_')
#     print(idiom_lower)
#     os.chdir(f"data/RQ3/pytest_files/{idiom_lower}/")
#     try:
#         os.remove(".mutmut-cache")
#     except FileNotFoundError:
#         pass
#
#     test_baseline = subprocess.run(["pytest", "--quiet"], stdout=subprocess.PIPE)
#     if test_baseline.returncode!=0:
#         out_str = test_baseline.stdout.decode('utf-8')
#         failed_str = out_str.split("short test summary info")[1].split("FAILED")[1:]
#         failed_funcs = [i.split('::')[1].split()[0] for i in failed_str]
#
#         with open(f"test_{idiom_lower}.py") as f:
#             test_code = f.read()
#
#         for ff in failed_funcs:
#             test_code = skip_test(test_code, ff)
#         with open(f"test_{idiom_lower}.py", "w") as f:
#             f.write(test_code)
#
#
#     result = subprocess.run(["mutmut", "run",
#                              "--paths-to-mutate", f"{idiom_lower}.py",
#                              "--tests-dir", f"test_{idiom_lower}.py", "--CI",
#                              "--swallow-output"])
#     if(result.returncode != 0):
#         # raise Exception("mutation testing failed")
#         mutation_failed.append(idiom_lower)