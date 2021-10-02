import argparse
import functools
import time

import z3

import solver
import syntax
import synth
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

def harder_check():
    start = time.time()
    grammar = [
        "S ::= ( S LOGOP S ) | ( VAR RELOP VAR ) | ( VAR RELOP VAL ) ",
        "LOGOP ::= and | or",
        "VAL ::= 0 | 1 | -1",
        "VAR ::= x | y | n",
        "RELOP ::= == | != | < | <="
    ]
    var_to_z3 = {"x": z3.Int("x"), "y": z3.Int("y"), "n": z3.Int("n")}
    properties_str = ["x > 0"]    
    
    expr_parser = syntax.PyExprParser(var_to_z3)
    syhnthesizer = Synthesizer.from_text()
    invariants_str = synth.get_invariants(grammar)
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

if __name__ == "__main__":
    harder_check()