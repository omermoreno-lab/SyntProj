from random import randint, choice, seed
from string import ascii_letters

# standard library

SEED = 0
MAX_LIST_LEN = 2 ** 4
MAX_STR_LEN = 2 ** 4
MAX_INT_VAL = 2 ** 8
NUM_EXAMPLES = 2 ** 12

count_examples = 0


def __inv__(reachable, *vars):
    f = open("record.txt", "a")
    f.write(str(reachable) + " ")
    for var in vars:
        f.write(str(var) + " ")
    f.write("\n")
    f.close()

    global count_examples
    count_examples += 1
    if count_examples == NUM_EXAMPLES:
        exit(0)


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


# clear record.txt
seed(SEED)
open("record.txt", "w")

# actual program
while True:
    n = __free_int__()
    k = __free_str__()
    d = __free_list__()

    x = y = 0
    while y < n and len(k) == 2:
        __inv__(True, x, y, n, k, d)
        x += 2
        y += 1
    # unreachable examples
    __inv__(False, x, y, n, k, d)