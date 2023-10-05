import yaml
import click
import os
from pathlib import Path
import json
import sys

sys.path.append(str(Path(__file__).parents[1]))
os.chdir(Path(__file__).parents[1])
from pycraft.find_variations import get_all_variations
from pycraft.find_testcases import find_tests

defaults_file = "defaults.yaml"
template_file = "src/defaults-template.yaml"

cpat_file = "cpat.yaml"
cpat_template = "src/cpat-template.yaml"

try:
    with open(defaults_file) as f:
        defaults = yaml.safe_load(f)
except FileNotFoundError:
    with open(template_file) as f:
        defaults = yaml.safe_load(f)

try:
    with open(cpat_file) as f:
        cpat_config = yaml.safe_load(f)
except FileNotFoundError:
    with open(cpat_template) as f:
        cpat_config = yaml.safe_load(f)


@click.group()
def cli():
    pass


@cli.group()
def configure():
    pass


@configure.command()
@click.option('--name', type=click.Choice(['gpt-3.5-turbo', 'gpt-4', 'palm']),
              required=True)
@click.option('--key', required=True)
def llm(name, key):
    print(name)
    print(key)
    print(defaults)
    defaults['model']['name'] = name
    defaults['model']['key'] = key

    with open(defaults_file, 'w') as f:
        yaml.dump(defaults, f)


@configure.command()
@click.option('--name', required=True)
@click.option('--lhs', required=True)
@click.option('--rhs', required=True)
def cpat(name, lhs, rhs):
    cpat_config['name'] = name
    cpat_config['LHS'] = lhs
    cpat_config['RHS'] = rhs
    with open(cpat_file, 'w') as f:
        yaml.dump(cpat_config, f)


@configure.command()
@click.option('--directory', required=False)
@click.option('--temperature', required=False)
@click.option('--iterations', required=False)
def testcases(directory, temperature, iterations):
    # defaults['testcases']['directory'] = directory
    pass


def get_testcases():
    tests_dir = defaults['testcases']['directory']
    try:
        os.makedirs(tests_dir)
    except:
        pass
    cpat_name = cpat_config['name']
    tests_path = f"{tests_dir}/{cpat_name}-test.json"
    meta_path = f"{tests_dir}/{cpat_name}-meta.json"

    try:
        with open(tests_path) as f:
            tests = json.load(f)
    except FileNotFoundError:
        click.echo("Asking LLM for tests.")
        tests, metadata = find_tests(
            cpat_config['LHS'],
            repeat_factor=defaults['testcases']['iterations'],
            temperature=defaults['testcases']['temperature'],
            model=defaults['model']['name'],
            key=defaults['model']['key']
        )
        with open(tests_path, 'w') as f:
            json.dump(tests, f, indent=1)
        with open(meta_path, 'w') as f:
            json.dump(metadata, f, indent=1)

    return tests


@cli.command()
def fetch_variants():
    tests = get_testcases()
    final_variations, incorrect, metadata = get_all_variations(
        starting_vars=[
            cpat_config['LHS'], cpat_config['RHS']
        ],
        temperature=defaults['variants']['temperature'],
        input_and_assertions=tests,
        repeat_factor=defaults['variants']['prompt_iterations'],
        max_depth=defaults['variants']['max_depth'],
        model=defaults['model']['name'],
        key=defaults['model']['key']
    )

    dest_dir = defaults['output']['destination']
    try:
        os.makedirs(dest_dir)
    except:
        pass

    cpat_name = cpat_config['name']
    variants_path = f"{dest_dir}/{cpat_name}-variants.json"

    with open(variants_path, 'w') as f:
        json.dump(final_variations, f, indent=1)
    click.echo(f"Variants written to {variants_path}")


if __name__ == '__main__':
    cli()
