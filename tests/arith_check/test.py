from std import __invariant__
while x < y and y < n and n < k:
    __invariant__(True, x, y, n, k)
    y = x * 4
    n = y ** 2
    k = n + n
    x = x - y
