
code = """ 
if c < 20 and c >15:
    x = 1
else:
    x = 2
"""


lhs_vars = "'x'"

prompt = f"""
Your task is to provide different examples of writing the same block of python code delimited by triple backticks. 
Do not make any assumptions about how the variables in the code are initialised. The variables must be accessed in the same way. 

The output code can be better or worse than the original. Provide examples like a novice, intermediate and advanced programmer. 
Provide as many examples as possible. You are allowed to use in-built python functions.

Perform the task using the following steps:
1. Generate a variation of the original code, using the guidelines above.
2. Verify that the variable(s) {lhs_vars} take the same value in the original and your variation at the end of the code.


Format your response as  JSON list. Each element of the list should be a string containing the code example. Here is a sample response:

["
<example-python-code-here>
"]



```{code}```
"""


if __name__ == '__main__':
    print(prompt)
    response = get_completion(prompt)
    print(response)