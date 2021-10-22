from std import *
while x < n:
    __invariant__(True, x, n, lista, listb)
    lista = __list_append__(__str_reverse__(listb), x)
    listb = __list_append__(__str_reverse__(lista), n)
    lista = __list_pop__(__str_reverse__(lista))
    x = len(listb)
    n = len(lista)