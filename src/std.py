import inspect
import functools
import os
from random import randint, choice, seed
from string import ascii_letters

rec_files = {}
SEED = 0
MAX_LIST_LEN = 2 ** 4
MAX_STR_LEN = 2 ** 4
MAX_INT_VAL = 2 ** 8
NUM_EXAMPLES = 2 ** 12

# standard library

def __invariant__(*args):
    frame = inspect.stack()[1]
    module = inspect.getmodule(frame[0])
    rec_name = os.path.splitext(module.__file__)[0] + '.record'
    # print("filename is",rec_name)
    line = " ".join([str(arg) for arg in args])
    if (rec_name not in rec_files):
        rec_files[rec_name] = open(rec_name, 'w')
    
    f = rec_files[rec_name]
    f.write(line + "\n")


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


def test():
    __invariant__(1, "hello", 5.364)
    __invariant__(2)
    __invariant__("check")
    __invariant__(45, "asf", "asfkjasf")

if __name__ == "__main__":
   test() 

