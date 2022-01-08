import argparse
import functools
from pathlib import Path

import solver
import prog
import json
from synthesizer import Synthesizer

def __get_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("source", type=str, help="The source folder from which all files should be pulled")
    parser.add_argument("tactic", type=str, choices=["simple", "cond-extraction"], help="The tactic used by the synthesizer when producing the invariant")
    parser.add_argument("-d", "--dest", dest="dest", nargs=1, type=str, help="Choose the destination of the result file, default is <source>/res.json")
    parser.add_argument("-ge", "--generate-examples", dest="generate_examples", action="store_true", help="Generate examples randomly")
    parser.add_argument("-md", "--max-depth", nargs=1, dest="max_depth", type=int, default=[2], help="Set max depth for the synthesizer, default=2")
    parser.add_argument("-ft", "--filter-tautologies", dest="filter_tau", action="store_true", help="Filter tautologies using the solver")

    args = parser.parse_args()
    args.max_depth = args.max_depth[0]
    args.dest = args.dest[0] if args.dest else None
    print(args)
    return args

def get_invariants_by_tactic(synth: Synthesizer, tactic, max_depth: int, program_text: str):
    if tactic == "simple":
        return synth.bottom_up_optimized(max_depth)
    elif tactic == "cond-extraction":
        while_lines = [line for line in program_text.split("\n") if "while" in line]
        if len(while_lines) == 1:
           while_line = while_lines[0]
           expr = while_line[len("while"): -1]      # stripping the line from "while" and ":"
           cond = "((" + expr + ")" + " or {})"
           return synth.bottom_up_optimized(max_depth, invariant_extension_format=cond)
        else:
            if len(while_lines) == 0:
                print("No while loops in program")
            else:
                print("multiple while loops in program")
    else:
        invariants = synth.bottom_up_optimized(max_depth)
        return [functools.reduce(lambda a,b: f"({a} and {b})", invariants)]


if __name__ == "__main__":
    args = __get_args()

    # setting path variables
    folder_path = args.source
    # TODO: add support for different tactics
    root_dir = str(Path(__file__).parent.parent)
    test_folder = "\\".join([root_dir, "tests", args.source])

    prog_path = "\\".join([test_folder, "test.py"])
    grammar_path = "\\".join([test_folder, "grammar.txt"])
    records_path = "\\".join([test_folder, "records.json"])
    properties_path = "\\".join([test_folder, "properties.json"])
    dest_path = "\\".join([root_dir, args.dest[0]]) if args.dest else "\\".join([test_folder, "res.json"])
    env_path = "\\".join([root_dir, args.dest[0]]) if args.dest else "\\".join([test_folder, "env.json"])
    
    # reading from files using the different paths
    var_to_z3 = solver.var_to_z3_from_config(env_path)
    print(f"var_to_z3: {var_to_z3}")
    with open(properties_path, 'r') as f:
        properties = list(solver.formulas_to_z3(json.load(f), var_to_z3))
    
    if args.generate_examples:
        examples = prog.generate_examples_from_files(prog_path, env_path)
        with open(records_path, 'w+') as f:
            json.dump(examples, f)
    else:
        with open(records_path, 'r') as f:
            examples = json.load(f)

    synth = Synthesizer.from_folder(test_folder)
    with open(prog_path, 'r') as f:
        program_text = f.read()
    invariant_strings = get_invariants_by_tactic(synth, args.tactic, args.max_depth, program_text)
    
    proven, counter_examples = solver.prove_properties(invariant_strings, properties, program_text, var_to_z3)
    print(f"proven properties: {proven}")
    print(f"new produced counter-examples {counter_examples}")
    with open(records_path, 'r') as f:
        states = json.load(f)
    variables = states[0][1:]
    var_to_randomizer = prog.get_variable_randomizers_from_file(env_path)
    counter_examples = [[False] + [ce[v] if v in ce else var_to_randomizer[v]() for v in variables] for ce in counter_examples]
    states += counter_examples
    with open(records_path, 'w+') as f:
        json.dump(states, f)


