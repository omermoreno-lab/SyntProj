import copy
import weakref


class Path(list):
    start = property(lambda self: self[0]())
    end = property(lambda self: self[-1]())

    nnodes = property(len)

    def __init__(self, list_of_tree_nodes=()):
        super(Path, self).__init__(map(weakref.ref, list_of_tree_nodes))

    def node_at(self, i):
        return self[i]()

    def __add__(self, cont):
        plus = copy.copy(self)
        plus += cont
        return plus

    def __iadd__(self, cont):
        if not isinstance(cont, Path):
            cont = Path(cont)
        return super(Path, self).__iadd__(cont)

    # using python3 slices https://docs.python.org/2/reference/datamodel.html#object.__getitem__
    # k is either a key or a slice object
    def __getitem__(self, k):
        p = Path()
        p.extend(super(Path, self).__getitem__(k))
        return p

    def up(self):
        return self[:-1]

    def goes_through(self, node):
        for path_node in self:
            if path_node() is node:
                return True
        else:
            return False

    def startswith(self, other_path):
        if len(other_path) > len(self):
            return False
        else:
            for i in range(len(other_path)):
                if self[i]() is not other_path[i]():
                    return False
            else:
                return True

    def __eq__(self, other):
        if isinstance(other, Path):
            return len(self) == len(other) and self.startswith(other)
        else:
            return NotImplemented

    def __repr__(self):
        return ' -> '.join(repr(x()) for x in self)


if __name__ == '__main__':
    class N(int):
        pass


    n1 = N(1)
    n2 = N(2)
    print(Path([n1, n2]) + [n2])
