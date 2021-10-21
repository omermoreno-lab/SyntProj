from std import *
while x < len(sa) and x > len(sb):
    __invariant__(True, x, sa, sb)
    sa = sa + sb
    x = len(sa) * len(sb)