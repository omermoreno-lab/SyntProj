from z3 import *
import syntax
import json

I = z3.IntSort()
R = z3.RealSort()
S = z3.StringSort()
TYPE_TO_Z3 = {"int": Int, "real": Real, "str": String, "list[int]": lambda v: Array(v, I, I),
              "list[real]": lambda v: Array(v, I, R), "list[str]": lambda v: Array(v, I, S)}

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

def filter_tautologies(formulas_iter):     # input: z3 invariants generator
    return filter(lambda f: not prove(f)[0], formulas_iter)


def formulas_to_z3(formulas_iter, var_to_z3: dict):
    return map(lambda f: str_to_z3(f, var_to_z3), formulas_iter)


def convert_to_py_expr(k, e, model):
    # print(f"{k=}\n{e=}\n")
    e_str = str(e)
    
    if e_str[0] != "K":
        return eval(e_str)
    l = int(e_str.split(',')[1][:-1]) # This is very bad programming, sadly I have to finish writing this code   
    val = [model.evaluate(k[i]) for i in range(l)]
    return val

# Both inputs should be z3 formulas
def prove_properties(invariant_strings, properties: list, program_text, var_to_z3):
    proven = []
    unproven = None
    prev_unproven = properties[:]
    counter_examples = []

    for inv in invariant_strings:
        print(f"current invariant: {inv}")
        print(f"properties to prove: {properties}")
        unproven = []
        inv = syntax.PyExprParser(var_to_z3)(inv).as_z3()
        for p in prev_unproven:
            res = prove(Implies(inv, p))
            if res[0]:
                proven.append(p)
                if len(proven) == len(properties):
                    return proven 
            else:
                # TODO: add counter example as negative example in synth and in file
                counter_examples.append(res[1])                
                unproven.append(p)
        prev_unproven = unproven
    print(f"{counter_examples=}")
    counter_examples = [{str(k): convert_to_py_expr(k, ce[k], ce) for k in ce} for ce in counter_examples]
    return proven, counter_examples
