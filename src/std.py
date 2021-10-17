import inspect
import functools
import os
import json
from random import randint, choice, seed
from string import ascii_letters

SEED = 0
MAX_LIST_LEN = 2 ** 4
MAX_STR_LEN = 2 ** 4
MAX_INT_VAL = 2 ** 8
NUM_EXAMPLES = 2 ** 12
__INVARIANTS = []
# standard library

# def __invariant__(*args):
#     frame = inspect.stack()[1]
#     module = inspect.getmodule(frame[0])
#     rec_name = os.path.splitext(module.__file__)[0] + '.record'
#     # print("filename is",rec_name)
#     line = " ".join([str(arg) for arg in args])
#     if (rec_name not in rec_files):
#         rec_files[rec_name] = open(rec_name, 'w')
    
#     f = rec_files[rec_name]
#     f.write(line + "\n")

def __invariant__(*args):
    # print(f"args: {args}")
    __INVARIANTS.append(list(args))

def get_recorded_states():
    return __INVARIANTS

def dump_recorded_states_to_file(file_path: str, invariants = __INVARIANTS):
    with open(file_path, 'w') as f:
        json.dump(invariants, f)

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


# def test():
#     __invariant__(1, "hello", 5.364)
#     __invariant__(2)
#     __invariant__("check")
#     __invariant__(45, "asf", "asfkjasf")

# if __name__ == "__main__":
#    test() 

