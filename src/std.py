import inspect
import functools
import os
from random import randint, choice, seed
from string import ascii_letters

SEED = 0
MAX_LIST_LEN = 2 ** 4
MAX_STR_LEN = 2 ** 4
MAX_INT_VAL = 2 ** 8
NUM_EXAMPLES = 2 ** 12
__INVARIANTS = []

# api for interacting with globals

def get_recorded_states():
    return __INVARIANTS

# standard library

def __invariant__(*args):
    # print(f"args: {args}")
    global __INVARIANTS
    __INVARIANTS.append(list(args))


def __str_reverse__(l):
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

def __str_reverse__(s: str):
    s = s[::-1]
    return s
