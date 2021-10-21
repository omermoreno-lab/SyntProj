from std import *
while x < n:
    __invariant__(True, x, n, s, strlista, strlistb)
    strlista = __list_reverse__(__list_append__(strlista, s))
    strlistb = __list_pop__(strlistb)
    x = len(strlista)
    n = len(strlistb)