# PyCraft
PyCraft is a tool that refactors python code

## Tool Pipeline
![Schematic Diagram](diagram.png?raw=true "Schematic Diagram")

1. To extract CPATs, we use [R-CPATMiner](https://github.com/maldil/R-CPATMiner)
2. The code in this repository leverages LLMs to generate variants 
3. To Synthesise and apply tranformation rules, we utilise [PyEvolve](https://github.com/maldil/PyEvolve/) 

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

