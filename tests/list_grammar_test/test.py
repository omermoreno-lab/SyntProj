from std import __invariant__, __str_reverse__
i = 0
l2 = l1
while i < n:
    __invariant__(i, n, l1, l2)
    l2 = __str_reverse__(l2)
    i += 1