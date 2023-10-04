import json
import os
from compare_ast import Compare
import ast
compare_ast_fn = Compare().do


with open("data/RQ2/hallucinations.json") as f:
    hc = json.load(f)

metadata_files = [i for i in os.listdir("data/RQ2/data") if 'metadata' in i]
idioms = {i.split("-metadata")[0] for i in metadata_files}
correct_files = []

for file in os.listdir("data/RQ2/data"):
    if(any((i in file for i in idioms))):
        if('incorrect' in file or 'metadata' in file):
            continue
        correct_files.append(file)



for f in correct_files:
    with open(f"data/RQ2/data/{f}") as file:
        correct_vars = json.load(file)



    for c in correct_vars:
        if any((compare_ast_fn(ast.parse(c['code']), ast.parse(f)) for f in hc)):
            continue
        print("Is hallucination?")
        print(c['code'])
        ans = input("y/n")

        if(ans == 'y'):
            hc[c['code']] = True
        elif(ans == ''):
            hc[c['code']] = False
        # print(hc)
        if(ans == 'n'):
            with open("data/RQ2/hallucinations.json", "w") as file:
                json.dump(hc, file, indent=1)
            break
    # break





