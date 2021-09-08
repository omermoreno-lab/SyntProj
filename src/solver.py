from z3 import *
import itertools

RECORD_DELIM = '#'
GRAMMAR_DELIM = '|'
VAR_ROOT = 'VAR'
ASSIGNMENT_SYMBOL = '::='
"""
    gets a formula f
    if satisfiable then return True, None
    else returns False and a conuter-example
"""


class Record(object):
    var_to_type_converter: dict

    @classmethod
    def set_converter(cls, converter: dict):
        cls.var_to_type_converter = converter

    def __init__(self, records: list, vars: list):
        self.is_possible = records[0]
        assert(len(records) - 1 == len(vars))
        records = records[1:]
        self.var_vals = dict(zip(vars, records))

    @classmethod
    def from_file(cls, filename: str, vars: list):
        with open(filename, 'r') as f:
            records = [l for l in f]
        records = [Record([eval(e) for e in record.split(RECORD_DELIM)], vars) for record in records]
        return records

    def get_assignment_constraints(self):
        for var, _ in self.var_vals:
            if var not in self.var_vals:
                raise ValueError(f"{var} is not in converter dict {self.var_to_type_converter}\nmaybe dict was not set (set by calling set_converter)")
        return [self.var_to_type_converter[var](var) == val for (var, val) in self.var_vals]

    def make_implication_expr(self, example):
        return Implies(self.get_assignment_constraints(), example if self.is_possible else Not(example))


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
    is_sat = s.check() == sat,
    return is_sat, (s.model() if is_sat else None)


def get_vars_from_grammar(grammar_file):
    var_text = ""
    with open(grammar_file, 'r') as f:

        for line in f:
            line_components = [s.strip() for s in line.split(ASSIGNMENT_SYMBOL)]
            left_var, vars = line_components[0], line_components[1]
            if left_var == VAR_ROOT:
                var_text = vars
                break
        assert (var_text != "")
    vars = [s.strip() for s in var_text.split(GRAMMAR_DELIM)]
    return vars


# def get_records(record_file):
#     with open(record_file, 'r') as f:
#         records = [l for l in f]
#     records = [[eval(e) for e in record.split(RECORD_DELIM)] for record in records]
#     return records

def is_sat(f):
    return find_sat(f)[0]


def is_proven(f):
    return prove(f)[0]
#
# def is_possible(f):
#     return prove(f)[0]


def prove_conjectures(examples, record_file: str, grammar_file: str):
    vars = get_vars_from_grammar(grammar_file)
    records = Record.from_file(record_file, vars)
    Record.set_converter()          # TODO: add converter here
    conjectures = {example: [record.make_implication_expr(example) for record in records] for example in examples}

    proven = [example for example in conjectures if all([is_proven(f) and is_sat(f) for f in conjectures[example]])]
    # possible_truths = [p[0] for p in proven if p[1][0] and p[2][0]]  # these are all the conjectures where
    #                                                                  # we proved that
