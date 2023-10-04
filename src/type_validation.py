import json

import helpers

def get_prompt(code_str):
    prompt = f"""
Your task is to provide the types of the variables in the code encoded by triple backticks.
Respond in the form of a JSON list. Each element in the list has 'variable' and 'type' keys.

Here is an example execution of this task: 

Code:
count = 0
for i in range(len(int_list)):
    count = count + int_list[i]

Response:
[
    {{
        "variable": "count",
        "type": "int"
    }},
    {{
        "variable": "int_list",
        "type": "list[int]"
    }}
]


```
{code_str}
```
"""
    return prompt

def get_prompt_clarify(code_str, varname, type_name):
    prompt = f"""
    Your task is to provide the types of the members in the {type_name} '{varname}', as seen in the code encoded by triple backticks.
    
    Respond only with the python type for '{varname}'. 
    
    Here is an example execution of this task:
    
    Variable: int_list
    
    Code:
    count = 0
    for i in range(len(int_list)):
        count = count + int_list[i]
        
    Response: 
    {{"type":"list[int]"}}
    
    ```
    {code_str}
    ```
    """

    return prompt


def get_prompt_unkown_type(code_str, varname, type_name):
    prompt = f"""
    Your task is to provide the types of the variable '{varname}', as seen in the code encoded by triple backticks.

    Respond only with the python type for '{varname}'. 

    Here is an example execution of this task:

    Variable: iterable

    Code:
    t = []
    for i in iterable:
        if cond(i):
            t.append(i)

    Response: 
    {{"type":"list"}}

    ```
    {code_str}
    ```
    """

    return prompt


def get_types(code_str):
    response = helpers.get_completion(get_prompt(code_str), 0.5)
    try:
        result = json.loads(response)
    except:
        print("Json decode-error(while looking for types)!")
        result = []
    return result

def clarify_type(code_str, var_name, type_name):
    if(type_name in ['unknown', 'iterable']):
        prompt_fn = get_prompt_unkown_type
    else:
        prompt_fn = get_prompt_clarify

    response = helpers.get_completion(prompt_fn(code_str, var_name, type_name), 0.5, model='gpt-4')
    try:
        new_type = json.loads(response)['type']
    except:
        print("Failed to parse clarification response")
        print(response)
        new_type = type_name

    return new_type


if __name__ == '__main__':
    # code_str = """
    # count = 0
    # for i in range(len(int_list)):
    #     count += int_list[i]"""
    #
    #
    # response = helpers.get_completion(get_prompt(code_str), 0.5)
    # for row in json.loads(response):
    #     print(row['variable'], ':', row['type'])
    pass