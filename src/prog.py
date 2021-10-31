import json
import unittest
from random import choice, randint, seed
from string import ascii_letters

import std

# SEED = None
MAX_LIST_LEN = 2 ** 4
MAX_STR_LEN = 2 ** 4
MAX_INT_VAL = 2 ** 8
NUM_EXAMPLES = 2 ** 4


# standard library

def __free_list__(init_function):
    list_len = randint(0, MAX_LIST_LEN)
    d = [init_function() for _ in range(list_len)]
    return d


def __free_str__():
    str_len = randint(0, MAX_STR_LEN)
    rand_str = ""
    for i in range(str_len):
        rand_str += choice(ascii_letters)
    return rand_str


def __free_int__():
    return randint(0, MAX_INT_VAL)


# def __get_var_and_randomizer(line: str, type_str_to_randomizer: dict):
#     # print(f"current line: {line}")
#     var, var_type = [s.strip() for s in line.split(':')]
#     return var, type_str_to_randomizer[var_type]


def __get_randomized_environment(var_to_randomizer: dict):
    return {v: var_to_randomizer[v]() for v in var_to_randomizer}


def generate_examples(program: str, var_to_initializer: dict):
    # seed(SEED)
    seed()
    vars = list(var_to_initializer.keys())
    vars.insert(0, None)
    examples = [vars]       # first entry of examples is the variables' names
    for i in range(NUM_EXAMPLES):
        exec(program, __get_randomized_environment(var_to_initializer))     # this will generate positive examples using the __invariant__ call

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

def get_variable_randomizers(var_to_type_dict):
    type_str_to_randomizer = {"int": __free_int__, "str": __free_str__, "list[str]": lambda: __free_list__(__free_str__), "list[int]": lambda: __free_list__(__free_int__)}
    return dict((var, type_str_to_randomizer[var_type]) for var, var_type in var_to_type_dict.items())


def get_variable_randomizers_from_file(path):
    with open(path, 'r') as f:
        var_to_type_dict = json.load(f)
    return get_variable_randomizers(var_to_type_dict)

def generate_examples_from_files(program_path: str, env_setting_path: str):
    # TODO: make str to initializer smarter, using reg expressions
    with open(program_path, 'r') as f:
        program = f.read()
    var_to_randomizer = get_variable_randomizers_from_file(env_setting_path)

    return generate_examples(program, var_to_randomizer)


def write_recorded_states_file(record_file_path: str, vars: list[str], records = std.get_recorded_states()):
    if len(records) == 0:
        raise ValueError("States undefined, ignoring request")
    with open(record_file_path, 'w') as f:
        json.dump([vars] + records, f)


def extend_recorded_states_file(record_file_path: str, records = None):
    if not records:      # the ususal case, getting the invariants from the function
        records = std.get_recorded_states()
    elif len(records) == 0:
        # raise ValueError("States undefined, ignoring request")
        return

    with open(record_file_path, 'r') as f:
        existing_records = json.load(f)
    
    existing_records.extend(records)
    
    with open(record_file_path, 'w') as f:
        json.dump(existing_records, f)


if __name__ == "__main__":
    type_str_to_randomizer = {"int": __free_int__, "str": __free_str__, "list[str]": lambda: __free_list__(__free_str__), "list[int]": lambda: __free_list__(__free_int__)}
    program =   "\n".join(["from std import __invariant__", "x = y = 0",
                "while y < n:",
                "   __invariant__(True, x, y, n, k, d)",
                "   x += 2",
                "   y += 1"])
    # exec(program)
    var_to_type_text = "\n".join(["n : int",
                "k : str",
                "d: list[int]"])

    print(f"program = {program}")
    print(f"settings file = {var_to_type_text}")
    # var_to_randomizer = dict(__get_var_and_randomizer(line, type_str_to_randomizer) for line in var_to_type_text.splitlines())
    # print(generate_examples(program, var_to_randomizer))

# if __name__ == "__main__":
#     seed()
#     f = __free_int__
#     for i in range(10):
#         print(f"random number: {f()}")
