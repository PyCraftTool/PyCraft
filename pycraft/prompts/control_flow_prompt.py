code = """
count = 0
for (i, num) in enumerate(int_list):
    count += num
"""



def get_prompt(code_str):
    prompt = f"""
Your task is to provide variations of the code delimited by triple backticks. To perform your task, only add statements(1 or more) to the code that a developer may write. 
Added statements should not change the intent of the code.

```
{code_str}
```
"""

    return prompt

