from random import randint, choice, seed
from string import ascii_letters
import unittest
import std

# SEED = None
MAX_LIST_LEN = 2 ** 4
MAX_STR_LEN = 2 ** 4
MAX_INT_VAL = 2 ** 8
NUM_EXAMPLES = 2 ** 4



# standard library

def __free_list__(init_function):
    list_len = randint(0, MAX_LIST_LEN)
    d = []
    for i in range(list_len):
        d.append(init_function())
    return d


def __free_str__():
    str_len = randint(0, MAX_STR_LEN)
    rand_str = ""
    for i in range(str_len):
        rand_str += choice(ascii_letters)
    return rand_str


def __free_int__():
    return randint(0, MAX_INT_VAL)


def __list_reverse__(l):
    l = l[:]
    l.reverse()
    return l


def __list_append__(l, e):
    l = l[:]
    l.append(e)
    return l


def __list_pop__(l):
    l = l[:]
    l.pop()
    return l


def __get_var_and_initializer(line: str, type_str_to_initializer: dict):
    # print(f"current line: {line}")
    var, var_type = list(s.strip() for s in line.split(':'))
    return var, type_str_to_initializer[var_type]


def __get_randomized_environment(var_to_initializer: dict):
    return {v: var_to_initializer[v]() for v in var_to_initializer}


def generate_examples(program: str, var_to_initializer: dict):
    # seed(SEED)
    seed()
    vars = list(var_to_initializer.keys())
    vars.insert(0, None)
    examples = [vars]       # first entry of examples is the 
    for i in range(NUM_EXAMPLES):
        exec(program, __get_randomized_environment(var_to_initializer))     # this will generate positive examples using the __inv__ call

    #     n = __free_int__()
    #     k = __free_str__()
    #     d = __free_list__()

    #     x = y = 0
    #     # while y < n and len(k) == 2:
    #     while y < n:
    #         examples.append([True, x, y, n, k, d])
    #         x += 2
    #         y += 1
    #     # unreachable examples
    #     # examples.append([False, x, y, n, k, d])
    # # examples.append([False, -1, -2, 5, 'hafhasf', [200,33]])
    examples.extend(std.get_recorded_states())
    return examples

def generate_examples_from_files(program_path: str, env_setting_path: str):
    type_str_to_initializer = {"int": __free_int__, "str": __free_str__, "list[str]": lambda: __free_list__(__free_str__), "list[int]": lambda: __free_list__(__free_int__)}
    # TODO: make str to initializer smarter, using reg expressions
    with open(program_path, 'r') as f:
        program = f.read()
    
    with open(env_setting_path, 'r') as f:
        var_to_initializer = dict(__get_var_and_initializer(line, type_str_to_initializer) for line in f.readlines())

    
    return generate_examples(program, var_to_initializer)


if __name__ == "__main__":
    type_str_to_initializer = {"int": __free_int__, "str": __free_str__, "list[str]": lambda: __free_list__(__free_str__), "list[int]": lambda: __free_list__(__free_int__)}
    program =   "\n".join(["from std import __invariant__", "x = y = 0",
                "while y < n:",
                "   __invariant__(True, x, y, n, k, d)",
                "   x += 2",
                "   y += 1"])
    # exec(program)
    var_to_initializer_text = "\n".join(["n : int",
                "k : str",
                "d: list[int]"])

    print(f"program = {program}")
    print(f"settings file = {var_to_initializer_text}")
    var_to_initializer = dict(__get_var_and_initializer(line, type_str_to_initializer) for line in var_to_initializer_text.splitlines())
    print(generate_examples(program, var_to_initializer))

# if __name__ == "__main__":
#     seed()
#     f = __free_int__
#     for i in range(10):
#         print(f"random number: {f()}")