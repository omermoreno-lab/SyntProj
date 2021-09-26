from z3 import *
import unittest
import synth

def prove(f):
    s = Solver()
    s.add(Not(f))
    if s.check() == unsat:
        return True, None
    else:
        return False, s.model()


def prove_properties(invariant, properties):
    conjectures = [Implies(invariant, p) for p in properties]
    results = list(map(lambda c: (c, prove(c)), conjectures))
    verified = list(map(lambda r: r[0],filter(lambda r: r[1][0], results)))
    counter_examples = dict(map(lambda r: (str(r[0]),r[1][1]), filter(lambda r: not r[1][0], results)))
    return verified, counter_examples


class TestPropertiesMethods(unittest.TestCase):
    def test_int_invariant(self):
        x = Int('x')
        y = Int('y')
        invariant = And(x < y, x >= 0)
        properties = [y > 0, y < -1, y >= 4]
        v, ce = prove_properties(invariant, properties)
        print(v)
        print(ce)
        assert(len(v) == 1)
        assert(len(ce) == 2)

if __name__ == "__main__":
    # grammar = [
    #     "S ::= ( VAR RELOP VAR )",
    #     "VAR ::= x | y | n",
    #     "RELOP ::= == | != | < | <="
    # ]
    # invariants = synth.get_invariants(grammar)
    # # TODO: find out why the new definitions in prog
    # #        make no variant valid
    # print(invariants)
    unittest.main()


