import typing
import functools
# from typing_extensions import IntVar
import prog
EXPECTED_RES_VAR = "expected_res" 

# class InvariantConjecture(object):
#     def __init__(self, val: str):
#         self.val = val

#     def __hash__(self):
#         return hash(self.val)

#     def __eq__(self, other):
#         return self.val == other.val if other is InvariantConjecture else False
    
#     """
#     checks if the state satisfies the invariant
#     this function also takes into consideration if the state is True or False
#     """
#     def satisfies(self, state: dict) -> bool:
#         res = eval(self.val, state) 
#         assert(isinstance(res, bool))
#         res = res if state[EXPECTED_RES_VAR] else not res
#         return res




# class Enumerator(object):
#     states : list[dict]      # a list of all states, as dictionaries of var->val

#     def __init__(self, states: list):
#         vars = states[0][:]
#         vars[0] = EXPECTED_RES_VAR
#         self.states = [dict(zip(vars, state)) for state in states]

# def satisfies(invariant, state: dict) -> bool:
#     res = eval(invariant, state) 
#     assert(isinstance(res, bool))
#     return res


# def are_observational_equivalent(ic1, ic2, states):
#     return all(ic1.satisfies(s) == ic2.satisfies(s) for s in states)


def flatten(t):
    return [item for sublist in t for item in sublist]

# def parse_grammar(g):
#     rules = dict()
#     tokens = {}
#     for rule in g:
#         rule_split = rule.split(" ::= ")
#         assert len(rule_split) == 2
#         rule_type = rule_split[0]
#         rule_body = rule_split[1]
#         rule_body = rule_body.split(" | ")
#         rules[rule_type] = rule_body
#     return rules

"""
a class used for comfortability only, in case eval() does not return a result and one still wants to insert it into the results list
used for example in case "<" and ">" will try to be merged because they are not valid expressions
"""
class NoEqual:
    def __init__(self):
        pass

    def __eq__(self, other):
        return False


class Synthesizer(object):
    prod_rules: typing.Dict[str, list[list[str]]]   # token -> production rules dictionary
    examples: typing.Dict[str, typing.Set[str]]           # token -> generated program examples of this token. for example, examples["Var"] = [x, y, z]
    terminals: list
    non_terminals: list[str]
    states: list[dict]

    def __init__(self, tokens, prod_rules, states):
        def ground(s):
            # return s.isalnum() and not s.isupper()
            return not s.isupper()
            
        self.tokens = tokens
        self.terminals = [t for t in tokens if ground(t)]
        self.non_terminals = [t for t in tokens if not ground(t)]
        self.prod_rules = prod_rules
        self.examples = {t: {t} for t in self.terminals} | {nt: {} for nt in self.non_terminals}
        self.states = states
        print(f"Synth init:\n\
            tokens = {self.tokens}\n\
            terminals = {self.terminals}\n\
            non_terminals = {self.non_terminals}\n\
            prod_rules = {self.prod_rules}\n\
            examples = {self.examples}")

    @staticmethod
    def from_text(grammar_list, states_list):
        def parse_grammar(g):
            rules = dict()
            tokens = set()
            for rule in g:
                rule_split = rule.split(" ::= ")
                assert len(rule_split) == 2
                rule_type = rule_split[0]
                rule_body = rule_split[1]
                rule_body = [r.split(" ") for r in rule_body.split(" | ")]
                rules[rule_type] = rule_body
                tokens.add(rule_type)
                for r in rule_body:
                    for t in r:
                        tokens.add(t)
            return rules, tokens

        def get_states(examples):
            def state_as_dictionary(variables: list, state: list):
                return dict(zip(variables, state))   
            variables = examples[0]
            variables[0] = EXPECTED_RES_VAR
            states = [state_as_dictionary(variables, e) for e in examples[1:]]
            return states

        prod_rules, tokens = parse_grammar(grammar_list)
        states = get_states(states_list)
        return Synthesizer(tokens, prod_rules, states)


    @staticmethod
    def from_files(grammar_file, state_file):
        with open(grammar_file, 'r') as f:
            grammar_list = f.readlines()
        with open(state_file, 'r') as f:
            state_list = f.readlines()
        return Synthesizer.from_text(grammar_file, state_list)

    # def grow_advanced(self):
    #     # NOTICE: I think this funciton might be wrong but I forgot why, probably want to review the code before using
    #     def _grow(token, visited):
    #         if token in visited or token not in self.non_terminals:
    #             return self.examples[token]
    #         visited.append(token)
    #         self.examples[token] = ["".join([self.grow(t, visited) for t in pr]) for pr in self.prod_rules[token]]      # gets all the examples currenlty available for this token
    #         return self.examples[token]
    #     visited = []
    #     for nt in self.non_terminals:
    #         _grow(self, nt, visited)
    #     return
    
    def __grow(self):
        # def _get_examples(token, made_examples):
        #     return set((example.concat(token_example) for token_example
        #                 in self.examples[token] for example in made_examples))

        # # TODO: Need to take a look at this function
        # def _grow_var(token):
        #     return functools.reduce(_get_examples, self.prod_rules[token]) \
        #         if token in self.non_terminals else self.examples[token]
        
        def grow_var(t):
            def grow_production_rule(pr):
                first_token_examples = self.examples[pr[0]]
                if len(pr) == 1:
                    return first_token_examples
                return set((e + pr_tail_example for e in first_token_examples for pr_tail_example in grow_production_rule(pr[1:])))
            # return flatten(map(grow_production_rule(pr) for pr in self.examples[t]))
            return flatten((grow_production_rule(pr) for pr in self.prod_rules[t]))
        # return {t: _grow_var(t) for t in self.tokens}
        self.examples |= {t: grow_var(t) for t in self.non_terminals}

    # # TODO: grow does not support the result of merge_invariants yet, add support quickly!
    # # removed this function for now as __merge is the more robust of the two
    # def __merge_invariants(self, states):
    #     def get_results_list(invariant_example, states):
    #         return [satisfies(invariant_example, state) for state in states]
        
    #     """
    #     takes a list of booleans (based on true/ false evaluation) and gives an int, which the i-th bit is 1 if evaluated to true
    #     """
    #     def convert_results_to_int(res_list):
    #         res = 0
    #         for i, b in res_list:
    #             res = res | (int(b) << i)
    #         return res 
        
    #     invariant_examples = self.examples["S"]
    #     example_to_int = {}
    #     int_to_example = {}
    #     for example in invariant_examples:
    #         example_success_flags = convert_results_to_int(get_results_list(example, states))
    #         example_to_int[example] = example_success_flags
    #         if example_success_flags not in int_to_example:
    #             int_to_example[example_success_flags] = example
        
    #     self.examples["S"] = int_to_example.values[:]
    
    def __merge(self):
        def safe_evaluate(program, state):
            try:
                return eval(program, state)
            except:
                return NoEqual()
        def equal_results(res1, res2):
            return all((r1 == r2 for r1,r2 in zip(res1, res2)))

        def get_equal_examples(token_examples, program_equality_dict):
            return set((program_equality_dict[e] for e in token_examples))

        programs = set(flatten(self.examples.values()))
        results = {program: [safe_evaluate(program, state) for state in self.states] for program in programs}
        program_equality_dict = {p: p for p in programs}
        program_keys = list(results.keys())
        for i, p1 in enumerate(program_keys):
            for p2 in program_keys[i+1:]:
                if equal_results(results[p1], results[p2]):
                    program_equality_dict[p2] = p1
        
        new_examples = {p: get_equal_examples(self.examples[p], program_equality_dict) for p in self.examples}
        self.examples |= new_examples
    
    def bottom_up_enumeration(self, max_depth=4):
        def satisfies(cond, state: dict) -> bool:
            res = eval(cond, state) 
            assert(isinstance(res, bool))
            res = res if state[EXPECTED_RES_VAR] else not res
            return res

        def satisfies_all(cond, states):
            return all((satisfies(cond, s) for s in states))

        for i in range(max_depth):
            self.__grow()
            self.__merge()
        for program in self.examples["S"]:
            if satisfies_all(program, self.states):
                yield program

if __name__ == "__main__":
    grammar = [
        "S ::= ( S BOOLOP S' ) | S'",
        "S' ::= ( VAR RELOP VAR )",
        "BOOLOP ::= and | or",
        "VAR ::= x | y | n",
        "RELOP ::= == | != | < | <="
    ]
    states = prog.generate_examples()
    synthesizer = Synthesizer.from_text(grammar, states)
    print(set(synthesizer.bottom_up_enumeration(4)))