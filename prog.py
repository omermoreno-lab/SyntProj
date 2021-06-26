from random import randint, choice, seed
from string import ascii_letters

SEED = 0
MAX_LIST_LEN = 2 ** 4
MAX_STR_LEN = 2 ** 4
MAX_INT_VAL = 2 ** 8
NUM_EXAMPLES = 2 ** 12


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


def generate_examples():
    seed(SEED)

    examples = []
    while len(examples) < NUM_EXAMPLES:
        n = __free_int__()
        k = __free_str__()
        d = __free_list__()

        x = y = 0
        while y < n and len(k) == 2:
            examples.append([True, x, y, n, k, d])
            x += 2
            y += 1
        # unreachable examples
        examples.append([False, x, y, n, k, d])
    return examples
