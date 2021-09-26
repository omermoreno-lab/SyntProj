import typing
EXPECTED_RES_VAR = "expected_res" 

class InvariantConjecture(object):
    def __init__(self, val: str):
        self.val = val

    def __hash__(self):
        return hash(self.val)

    def __eq__(self, other):
        return self.val == other.val if other is InvariantConjecture else False
    
    """
    checks if the state satisfies the invariant
    this function also takes into consideration if the state is True or False
    """
    def satisfies(self, state: dict) -> bool:
        res = eval(self.val, state) 
        assert(res is bool)
        res = res if state[EXPECTED_RES_VAR] else not res
        return res


class Enumerator(object):
    states : list[dict]      # a list of all states, as dictionaries of var->val

    def __init__(self, states: list):
        vars = states[0][:]
        vars[0] = EXPECTED_RES_VAR
        self.states = [dict(zip(vars, state)) for state in states]

    def are_observational_equivalent(self, ic1: InvariantConjecture, ic2: InvariantConjecture):
        return all(ic1.satisfies(s) == ic2.satisfies(s) for s in self.states)


class Synthesizer(object):
    terminals: list
    non_terminals: list
    prod_rules: typing.Dict[str, list[str]]
    grow: typing.Generator

    def __init__(self, terminals, non_terminals, prod_rules):
        self.terminals = terminals
        self.non_terminals = non_terminals
        self.prod_rules = prod_rules
        self.grow = self._generate_grow_gen()

    def _generate_grow_gen():
        

    def bottom_up_enuemration(prod_rules, starting_terminals, spec, max_depth=4):
