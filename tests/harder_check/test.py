from std import __invariant__
# print(f"program env: {globals()}")
x = 1
while y < n:
    __invariant__(True, x, y, n, k, d)
    x = x + 2
    y = y + 1