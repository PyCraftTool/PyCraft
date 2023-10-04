import openai
import os
import json

# with open('chatgpt-key') as f:
#     openai.api_key  = f.read()

# def get_completion(prompt, model="gpt-3.5-turbo"):
#     messages = [{"role": "user", "content": prompt}]
#     response = openai.ChatCompletion.create(
#         engine=model,
#         messages=messages,
#         temperature=0, # this is the degree of randomness of the model's output
#         max_tokens = 1024,
#     )
#     return response.choices[0].message["content"]


def get_prompt(code, lhs_vars, variable_types = None):

    # code = """ 
    # a = [1,2,3,4]
    # a[2:3] = [7,9]
    # """


    # lhs_vars = "'x'"
    var_types_header = "Here are the types of variables in the code: \n"
    lhs_vars_str ="'" + "','".join(lhs_vars) + "'"
    # not_init_str = '' if no_init else "Do not add additional statement to intialise variable which are not initialised in the original code"
    prompt = f"""
Your task is to provide different examples of writing the same block of python code delimited by triple backticks. 
I will refer to this provided code as the 'original code', in the rest of the prompt.
Do not make any assumptions about how the variables in the original code are initialised. The variables in your code must be accessed in the same way. 


Your code can be better or worse than the original. Your code can be longer or shorter than the original. The structure of your example need not be the same as the original code. Provide multiple examples like a beginner, intermediate, and expert programmer. 
Provide as many examples as possible. You are allowed to use in-built python functions. You are also allowed to use any library functions such as (but not limited to): numpy, itertools, functools, math, statistics. Include import statements in your code for dependent libraries, as necessary.
Consider data-flow variants: variants following the same logical flow, but with additional temporary variables.

{var_types_header+variable_types if variable_types else ''}

Perform the task using the following steps:
1. Generate a variation of the original code, using the guidelines above.
2. Verify that the variable(s) {lhs_vars_str} take the same value in the original and your example at the end of the code.
3. Verify that any dependent libraries have been imported in the code


Format your response as  JSON list. Each element of the list should be a string containing the code example. Here is a sample response:

[
"import numpy as np\\ncount=np.sum(arr)",
"count = 0\\nfor (index, value) in enumerate(arr):\\n    count += arr[index]"
]



```
{code}
```
    """

    return prompt


# if __name__ == '__main__':
#     print(prompt)
#     response = get_completion(prompt)
#     print(response)