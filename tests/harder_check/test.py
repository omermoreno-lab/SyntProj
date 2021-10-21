from std import __invariant__
# print(f"program env: {globals()}")
while y < n:
    __invariant__(True, x, y, n, k, d)
    x += 2
    y += 1
