from random import randint, choice, seed
from string import ascii_letters

SEED = 0
MAX_LIST_LEN = 2 ** 4
MAX_STR_LEN = 2 ** 4
MAX_INT_VAL = 2 ** 8
NUM_EXAMPLES = 2 ** 10


# standard library

def __free_list__():
    list_len = randint(0, MAX_LIST_LEN)
    d = []
    for i in range(list_len):
        d.append(__free_int__())
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
    var, var_type = list(s.strip() for s in line.split(':'))
    return var, type_str_to_initializer[var_type]


def __get_randomized_environment(var_to_initializer: dict):
    return {v: var_to_initializer[v]() for v in var_to_initializer}


def generate_examples(program_path: str, env_setting_path: str):
    seed(SEED)
    type_str_to_initializer = {"int": __free_int__, "str": __free_str__, "list[str]": lambda: __free_list__(__free_str__), "list[int]": lambda: __free_list__(__free_int__)}
    # TODO: make str to initializer smarter, using reg expressions
    with open(env_setting_path, 'r') as f:
        var_to_initializer = dict(__get_var_and_initializer(line, type_str_to_initializer) for line in f)

    with open(program_path, 'r') as f:
        program = f.read()

    vars = list(var_to_initializer.keys)
    vars.insert(0, None)
    examples = [vars]       # first entry of examples is the 
    while len(examples) < NUM_EXAMPLES:
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
    return examples
