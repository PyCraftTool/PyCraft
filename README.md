# PyCraft
PyCraft is a tool that refactors python code

![Schematic Diagram](diagram.png?raw=true "Schematic Diagram")

## Requirements
1. Python 3+
2. API key to your preferred LLM

- GPT: https://platform.openai.com/account/api-keys
- PALM: https://makersuite.google.com/app/apikey

## Installation

1. Install dependencies 

    `pip install -r requirements.txt`

## Usage

### Configure PyCraft
1. Configure the LLM that you would like to use:

   ```
   python pycraft configure llm \
         --name gpt-3.5-turbo \
         --key <your-api-key-here>
   ```
2. Configure the CPAT(LHS, RHS) to generate variants for

   ```
   python pycraft configure cpat \
         --name numpy-sum \
         --lhs "count = 0
   for i in int_list:
       count +=i" \
         --rhs "import numpy as np
   count = np.sum(int_list)"
   ```

### Generating Variants
Run the fetch-variants command
```
python pycraft fetch-variants
```

