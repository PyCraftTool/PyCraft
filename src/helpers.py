import json
import time
import pdb
import openai
import ast
import copy
import errno
import os
import signal
import functools
import tiktoken
import google.generativeai as palm
import requests

from sanitise_code import SanitiseCode
from compare_ast import Compare
compare_ast_fn = Compare().do

with open('chatgpt-key') as f:
    openai.api_key = f.read()

with open('palm-key') as f:
    palm.configure(api_key=f.read())

with open('huggingface-token') as f:
    huggingface_token = f.read()

# class TimeoutError(Exception):
#     pass

def timeout(seconds=10, error_message=os.strerror(errno.ETIME)):
    def decorator(func):
        def _handle_timeout(signum, frame):
            raise TimeoutError(error_message)

        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            signal.signal(signal.SIGALRM, _handle_timeout)
            signal.alarm(seconds)
            try:
                result = func(*args, **kwargs)
            finally:
                signal.alarm(0)
            return result

        return wrapper

    return decorator


def get_completion_gpt(prompt, temperature, model):
    assert model.startswith('gpt')
    messages = [{"role": "user", "content": prompt}]

    enc = tiktoken.encoding_for_model("gpt-3.5-turbo")
    num_tokens = len(enc.encode(prompt))
    retry = 3
    while(retry):
        try:
            response = openai.ChatCompletion.create(
                model=model,
                messages=messages,
                temperature=temperature,  # this is the degree of randomness of the model's output
                max_tokens=4097 - num_tokens - 20,
            )
            retry = 0
        except openai.error.RateLimitError as e:
            # pdb.set_trace()
            print(f"Rate limited. retrying: {retry-1}")
            time.sleep(3 * (10**(3-retry)))
            retry -= 1
            if retry==0:
                raise


    return response.choices[0].message["content"]

def get_completion_palm(prompt, temperature, model):
    assert model == 'palm'
    palm_defaults = {
        'model': 'models/text-bison-001',
        'temperature': temperature,
        'candidate_count': 1,
        'top_k': 40,
        'top_p': 0.95,
        'max_output_tokens': 1024,
        'stop_sequences': [],
        'safety_settings': [{"category": "HARM_CATEGORY_DEROGATORY", "threshold": 1},
                            {"category": "HARM_CATEGORY_TOXICITY", "threshold": 1},
                            {"category": "HARM_CATEGORY_VIOLENCE", "threshold": 2},
                            {"category": "HARM_CATEGORY_SEXUAL", "threshold": 2},
                            {"category": "HARM_CATEGORY_MEDICAL", "threshold": 2},
                            {"category": "HARM_CATEGORY_DANGEROUS", "threshold": 2}],
    }

    response = palm.generate_text(
        **palm_defaults,
        prompt=prompt
    )
    return response.result


def get_completion_bloom(prompt, temperature, model):
    API_URL = "https://api-inference.huggingface.co/models/meta-llama/Llama-2-13b-chat-hf"
    headers = {"Authorization": f"Bearer {huggingface_token}"}

    payload = {
        "inputs": prompt,
    }
    response = requests.post(API_URL, headers=headers, json=payload)
    return response.json()

@timeout(5 * 60)  # 5min timeout.
def get_completion(prompt, temperature, model="gpt-3.5-turbo"):

    fn_mapping = {
        'gpt-3.5-turbo': get_completion_gpt,
        'gpt-4': get_completion_gpt,
        'palm': get_completion_palm
    }

    return fn_mapping[model](prompt, temperature, model)


def decode_response(response):
    try:
        variations = json.loads(response)
    except json.JSONDecodeError:
        variations = eval(response)

    return variations


def double_list(l1):
    new_l = copy.copy(l1)
    for i in l1:
        new_l.append(i)
    return new_l


def multiply_list(l1, factor):
    new_l = copy.copy(l1)
    for _ in range(factor):
        for i in l1:
            new_l.append(i)
    return new_l


def extract_code_imports(code_ast):
    code_ast = SanitiseCode().visit(code_ast)

    new_body = []
    imports = []
    for i in code_ast.body:
        if (isinstance(i, ast.Import) or isinstance(i, ast.ImportFrom)):
            imports.append(i)
        else:
            new_body.append(i)

    return {
        "code": ast.Module(body=new_body, type_ignores=[]),
        "imports": ast.Module(body=imports, type_ignores=[])
    }


# @timeout(60 * 5)
@timeout(15)
def run_test(variation_code, test_input, test_assert):
    exec("def input():\n    return ''", locals())
    exec(test_input, locals())
    exec(variation_code, locals())
    exec(test_assert, locals())


def test_variations(variation_code, input_and_assertions):
    for t in input_and_assertions:
        test_input, test_assert = t["init"], t["assertion"]
        try:
            # test_code = f"{test_input}\n{variation_code}\n{test_assert}"
            # exec(test_input, locals())
            # exec(variation_code, locals())
            # exec(test_assert, locals())
            run_test(variation_code, test_input, test_assert)

            if ("error" in t):
                # print("incorrect code, should've thrown error.")
                # print("code:\n", variation_code)
                # print("test->", test_input)
                return False, "should've thrown an error.", test_input, test_assert

        except Exception as e:
            if ("error" in t):
                pass
            else:

                # print("incorrect code, error:", e.__class__.__name__, str(e))
                # print("code:\n", variation_code)
                # print("test->", test_input)
                return False, e, test_input, test_assert
    return True, None, test_input, test_assert

def dedup_variations(variations):
    fv = []
    for f in variations:
        if all((compare_ast_fn(f["code"], f1["code"]) == False for f1 in fv)):
            # print(f["code"])
            fv.append(f)

    return fv