import argparse
import functools
import time
from pathlib import Path

import z3

import solver
import syntax
import prog
import json
from synthesizer import Synthesizer

def simple_check():
    # These are parameters that should be given by the user
    start = time.time()
    grammar = [
    "S ::= ( S BOOLOP S' ) | S'",
    "S' ::= ( VAR RELOP VAR )",
    "BOOLOP ::= and | or",
    "VAR ::= x | y | n",
    "RELOP ::= == | != | < | <="
    ]
    var_to_z3 = {"x": z3.Int("x"), "y": z3.Int("y"), "n": z3.Int("n")}
    properties_str = ["x > 0"]    
    
    expr_parser = syntax.PyExprParser(var_to_z3)
    
    invariants_str = synth.get_invariants(grammar)
    invariants = [expr_parser(e).as_z3() for e in invariants_str]
    properties = [expr_parser(p).as_z3() for p in properties_str]
    non_obvious_invariants = solver.filter_tautologies(invariants)
    print(f"invariants found: {non_obvious_invariants}")
    proven_properties = solver.prove_properties(non_obvious_invariants, properties)
    print(f"proven properties using simple tactic: {proven_properties}")
    combined_invariants = [functools.reduce(z3.And, non_obvious_invariants)]
    proven_using_and_operator = solver.prove_properties(combined_invariants, properties)
    print(f"proven using and tactic: {proven_using_and_operator}")
    suggested_properties = [expr_parser(sp).as_z3() for sp in synth.get_property_suggestions(grammar)]
    print(f"suggested properties: {solver.filter_tautologies(suggested_properties)}")
    print(f"time took: {time.time()-start} seconds")

def harder_check():
    import prog
    examples = prog.generate_examples_from_files("D:/Technion_Homework/Semester 6/Software Synthesis/SyntProj/tests/harder_check/test.py")
    prog.write_recorded_states_file("D:/Technion_Homework/Semester 6/Software Synthesis/SyntProj/tests/harder_check/records.json")
    start = time.time()
    grammar = [
        "S ::= ( S LOGOP S ) | ( VAR RELOP VAR ) | ( VAR RELOP VAL ) ",
        "LOGOP ::= and | or",
        "VAL ::= 0 | 1",
        "VAR ::= x | y | n",
        "RELOP ::= == | != | < | <="
    ]
    var_to_z3 = {"x": z3.Int("x"), "y": z3.Int("y"), "n": z3.Int("n")}
    properties_str = ["x > 0"]    
    
    expr_parser = syntax.PyExprParser(var_to_z3)
    synthesizer = Synthesizer.from_folder("D:/Technion_Homework/Semester 6/Software Synthesis/SyntProj/tests/harder_check")
    # for inv in synthesizer.bottom_up_optimized(2):
    #     print(f"inv: {inv}")
    invariants_str = list(synthesizer.bottom_up_optimized(2))
    invariants = [expr_parser(e) for e in invariants_str]
    properties = [expr_parser(p) for p in properties_str]
    non_obvious_invariants = solver.filter_tautologies(invariants)
    print(f"invariants found: {non_obvious_invariants}")
    proven_properties = solver.prove_properties(non_obvious_invariants, properties)
    print(f"proven properties using simple tactic: {proven_properties}")
    combined_invariants = [functools.reduce(z3.And, non_obvious_invariants)]
    proven_using_and_operator = solver.prove_properties(combined_invariants, properties)
    print(f"proven using and tactic: {proven_using_and_operator}")
    suggested_properties = [expr_parser(sp) for sp in synth.get_property_suggestions(grammar)]
    print(f"suggested properties: {solver.filter_tautologies(suggested_properties)}")
    print(f"time took: {time.time()-start} seconds")

# if __name__ == "__main__":
#     harder_check()

def __get_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("source", type=str, help="The source folder from which all files should be pulled")
    parser.add_argument("tactic", type=str, choices=["simple", "cond-extraction", "logical-and-adder"], help="The tactic used by the synthesizer when producing the invariant")
    parser.add_argument("-d", "--dest", dest="dest", nargs=1, type=str, help="Choose the destination of the result file, default is <source>/res.json")
    parser.add_argument("-ge", "--generate-examples", dest="generate_examples", action="store_true", help="Generate examples randomly")
    parser.add_argument("-md", "--max-depth", nargs=1, dest="max_depth", type=int, default=[2], help="Set max depth for the synthesizer, default=2")
    parser.add_argument("-ft", "--filter-tautologies", dest="filter_tau", action="store_true", help="Filter tautologies using the solver")
    # parser.add_argument("-ma", "--merge-all", dest="merge_all_flag", action="store_true", help="Merge all subprograms, default is merge only root program")

    args = parser.parse_args()
    args.max_depth = args.max_depth[0]
    args.dest = args.dest[0] if args.dest else None
    print(args)
    return args

def get_invariants_by_tactic(synth: Synthesizer, tactic, max_depth: int):
    if tactic == "simple":
        return synth.bottom_up_optimized(max_depth)
        # return synth.bottom_up_enumeration(4)
    elif tactic == "cond-extraction":
        pass
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
    
    invariant_strings = get_invariants_by_tactic(synth, args.tactic, args.max_depth)
    invariants_iter = solver.formulas_to_z3(invariant_strings, var_to_z3)
    if args.filter_tau:
        invariants_iter = solver.filter_tautologies(invariants_iter)
    
    proven = solver.prove_properties(invariants_iter, properties)
    print(f"proven properties: {proven}")
    


