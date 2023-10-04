
code = """ 
t = []
for i in range(100):
  if(t%2==1):
     t.append(i)
"""


lhs_vars = "'count'"
"""
Follow these steps to perform your task:
1. Generate a variant using the above guidelines
2. Verify that the control flow of the variant and the original are the same.
"""
", removing, or moving"

def get_prompt(code):
    
    prompt = f"""
Your task is to provide data-flow variants of the code delimited by triple backticks. 
Perform your task by following the same logical flow and adding temporary variables. Provide as many examples as you can.

Format your response as JSON list. Each element of the list should be a string containing the code example. Here is a sample response:

[
"value = my_dict.get(key)\\nif value is None:\\n    value = 0\\n",
"temp_value = my_dict.get(key)\\nif temp_value is None:\\n    value = 0\nelse:\n    value = temp_value\\n"
...
]


```
{code}
```
    """

    return prompt

# q = [ast.parse(i) for i in starting_vars]
# final_variations = []
# while(q):

#     print(len(final_variations), "final variations found.")
#     print(len(q), "items left in queue.")

#     code = q.pop(0)
#     code_str = ast.unparse(code)
#     print("searching for data-flow variants of:")
#     print(code_str)
#     print("---end---")

#     response = get_completion(get_prompt(code_str))
#     try:
#         variations = json.loads(response)
#     except json.JSONDecodeError:
#         try:
#             variations = eval(response)
#         except:
#             print("Cannot decode response, skipping")
#             print(f"{response = }")
#             final_variations.append(code)
#             continue

#     for c in variations:
#         try:
#             c_ast = ast.parse(textwrap.dedent(c))
#         except:
#             print("Unable to parse. Skipping")
#             print(c)
#             continue

#         if all((compare_ast_fn(c_ast, f)==False for f in final_variations)) and \
#             all((compare_ast_fn(c_ast, f)==False for f in q)) and \
#             compare_ast_fn(code, c_ast)==False:
#             q.append(c_ast)

#     final_variations.append(code)

#     if(len(final_variations) + len(q) >= VARIATS_LIMIT):
#         print(f"stopping early. {VARIATS_LIMIT} variations reached.")
#         break





# if __name__ == '__main__':
#     print(prompt)
#     response = get_completion(prompt)
#     print(response)