# import z3
from z3 import *
import syntax
import json
# from enum import Enum
# import itertools
# import typing
# import unittest

# RECORD_DELIM = '#'
# GRAMMAR_DELIM = '|'
# VAR_ROOT = 'VAR'
# ASSIGNMENT_SYMBOL = '::='
I = z3.IntSort()
R = z3.RealSort()
S = z3.StringSort()
TYPE_TO_Z3 = {"int": Int, "real": Real, "str": String, "list[int]": lambda v: Array(v, I, I),
              "list[real]": lambda v: Array(v, I, R), "list[str]": lambda v: Array(v, I, S)}


# class Record(object):
#     def __init__(self, vals: list, vars: list):
#         self.is_possible = vals[0]
#         assert (len(vals) - 1 == len(vars))
#         vals = vals[1:]
#         self.val_map = dict(zip(vars, vals))

#     @classmethod
#     def from_file(cls, filename: str, vars: list):
#         with open(filename, 'r') as f:
#             records = [l for l in f]
#         records = [Record([eval(expr) for expr in record.split(RECORD_DELIM)], vars) for record in records]
#         return records

#     def get_assignments_in_z3(self, var_to_z3: dict):
#         for var, _ in self.val_map:
#             if var not in var_to_z3:
#                 raise ValueError(f"{var} is not in converter dict {var_to_z3}\n")
#         return [var_to_z3[var] == val for (var, val) in self.val_map]

#     def make_implication_expr(self, conjecture, var_to_z3):
#         return Implies(self.get_assignments_in_z3(var_to_z3), conjecture if self.is_possible else Not(conjecture))



# def is_sat(f):
#     return find_sat(f)[0]


# def is_proven(f):
#     return prove(f)[0]


# def get_vars_from_grammar(grammar_file: str):
#     var_text = ""
#     with open(grammar_file, 'r') as f:
#         for line in f:
#             line_components = [s.strip() for s in line.split(ASSIGNMENT_SYMBOL)]
#             left_var, vars = line_components[0], line_components[1]
#             if left_var == VAR_ROOT:
#                 var_text = vars
#                 break
#         assert (var_text != "")
#     vars = [s.strip() for s in var_text.split(GRAMMAR_DELIM)]
#     return vars



# def prove_conjectures(conjectures: list[str], record_file: str, grammar_file: str, config_file: str):
#     # vars = get_vars_from_grammar(grammar_file)
#     vars_to_z3 = var_to_z3_from_config(config_file)
#     records = Record.from_file(record_file, list(vars_to_z3.keys()))
#     # TODO: I removed the converter and added the dictionary vars_to_z3, check if it is implemented right in all the code
#     # TODO: add support for maps, and maybe strings
#     conjectures = {conjecture: [record.make_implication_expr(conjecture, vars_to_z3) for record in records] for
#                    conjecture in conjectures}
#     proven = [example for example in conjectures if all([is_proven(f) and is_sat(f) for f in conjectures[example]])]

#     print("conjectures:", "\n".join(map(lambda x: '\t' + str(x), conjectures)))
#     print("Valid and satisfiable:", "\n".join(map(lambda x: '\t' + str(x), proven)))
#     # print("\n".join([f"{str(p)} is both satisfiable and proven" for p in proven]))
#     # possible_truths = [p[0] for p in proven if p[1][0] and p[2][0]]  # these are all the conjectures where
#     #                                                                  # we proved that



def prove(f):
    s = Solver()
    s.add(Not(f))
    if s.check() == unsat:
        return True, None
    else:
        return False, s.model()


def find_sat(f):
    s = Solver()
    s.add(f)
    is_sat = s.check() == sat
    return is_sat, (s.model() if is_sat else None)


def var_to_z3_from_config(config_file: str):
    def safe_conversion(var_t: str):
        if var_t not in TYPE_TO_Z3:
            raise ValueError(f"{var_t} in file {config_file} is invalid because the type is not supported."
                             f" The supported types are {TYPE_TO_Z3.keys()}")
        return TYPE_TO_Z3[var_t]

    with open(config_file, 'r') as f:
        env_dict = json.load(f)
        return {var: safe_conversion(var_t)(var) for var, var_t in env_dict.items()}


def str_to_z3(expr: str, var_to_z3: dict):
    parser = syntax.PyExprParser(var_to_z3)
    return parser(expr).as_z3()

# def filter_tautologies(invariants):
#     return [invariant for invariant in invariants if not prove(invariant)[0]]       # filter all invariants that are fundementally true, aka tautologies

def filter_tautologies(formulas_iter):     # input: z3 invariants generator
    return filter(lambda f: not prove(f)[0], formulas_iter)


def formulas_to_z3(formulas_iter, var_to_z3: dict):
    return map(lambda f: str_to_z3(f, var_to_z3), formulas_iter)


# def prove_properties(invariants, properties):       # returns the invariants that have at least one invariant that satisfies them
#     def prove_property(invariants, prop):
#         return any((prove(Implies(invariant, prop))[0] for invariant in invariants))
    
#     proven = [p for p in properties if prove_property(invariants, p)]
#     return proven

# Both inputs should be z3 formulas
def prove_properties(invariants_iter, properties: list):
    proven = []
    unproven = None
    prev_unproven = properties[:]

    for inv in invariants_iter:
        print(f"current invariant: {inv}")
        print(f"properties to prove: {properties}")
        unproven = []
        for p in prev_unproven:
            res = prove(Implies(inv, p))
            if res[0]:
                proven.append(p)
                if len(proven) == len(properties):
                    return proven 
            else:
                # TODO: add counter example as negative example in synth and in file
                unproven.append(p)
        prev_unproven = unproven
    return proven
