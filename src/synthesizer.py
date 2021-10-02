# from lib.adt.tree import Visitor
import time
import typing
import functools
from itertools import chain
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
    tokens: list[str]
    


    def __init__(self, tokens, prod_rules, states):
        self.tokens = tokens
        self.terminals = [t for t in tokens if Synthesizer.__ground(t)]
        self.non_terminals = [t for t in tokens if not Synthesizer.__ground(t)]
        self.prod_rules = prod_rules
        self.examples = {t: {t} for t in self.terminals} | {nt: set() for nt in self.non_terminals}
        self.states = states
        self.__generation_order = Synthesizer.__dfs_sort(self.prod_rules)
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
        # print("sorted production rules: ", Synthesizer.__dfs_sort(prod_rules))
        states = get_states(states_list)
        return Synthesizer(tokens, prod_rules, states)

    @staticmethod
    def from_files(grammar_file, state_file):
        with open(grammar_file, 'r') as f:
            grammar_list = f.readlines()
        with open(state_file, 'r') as f:
            state_list = f.readlines()
        return Synthesizer.from_text(grammar_file, state_list)

    @staticmethod
    def __ground(s):
            # return s.isalnum() and not s.isupper()
            return not s.isupper()

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

    def __grow_merge(self):
        """
        This is my try to make an efficient grow function,
        I would like to apply two techniques:
        1. Equivalent invariant elimination during synthesis
        2. ordered synthesis, where one can count only on new examples for the synthesis, and use the previuos examples where necessary
        """

        # THIS MIGHT NOT BE THE BEST OPTION TO DO THIS, DUE TO EFFICIENCY REASONS,
        # another option is to build all the possible expressions with the expandable tokens in them and then use replace
        def get_new_pr_examples(pr, new_examples):
            if len(pr) == 1:
                return [ne for ne in new_examples[pr[0]]] if pr[0] in new_examples else [], self.examples[pr[0]]
            tail_ne, tail_oe = get_new_pr_examples(pr[1:], new_examples)     # new examples and old examples
            token_new_examples = new_examples[pr[0]] if pr[0] in new_examples else []
            
            prev_new = ((oe + ne) for ne in tail_ne for oe in self.examples[pr[0]])
            curr_new = ((ne + oe) for oe in tail_oe for ne in token_new_examples)
            all_new = ((ne1 + ne2) for ne2 in tail_ne for ne1 in token_new_examples)
            
            new_programs = list(chain(prev_new, curr_new, all_new))
            old_programs = [oe1 + oe2 for oe2 in tail_oe for oe1 in self.examples[pr[0]]]
            print(f"new examples: {new_examples}")
            return new_programs, old_programs


        def is_expandable(pr):
            return any(t in self.__get_exapndable_tokens() for t in pr)

        def grow_token(t, new_examples):
            if t not in self.__get_exapndable_tokens():
                return
            new_examples[t] = flatten([(get_new_pr_examples(pr, new_examples)[0]) for pr in self.prod_rules[t] if is_expandable(pr)])
        
        def is_unique(example, other_examples):
            print(f"example: {example}, other_examples: {other_examples}")
            return all((any((eval(example, state) != eval(e, state) for state in self.states)) for e in other_examples))

        new_examples = {}
        for token in self.__generation_order:
            grow_token(token, new_examples)
        unique_examples = {t: {ne for ne in new_examples[t] if is_unique(ne, self.examples[t])} for t in new_examples}
        print(unique_examples)
        print(f"current examples: {self.examples}")
        for t in unique_examples:
            # print(f"t = {t}")
            print(f"current token: {t}, examples: {self.examples[t]}")
            self.examples[t].union(set(unique_examples[t]))      


    @staticmethod
    def __dfs_sort(prod_rules):
        def __sort_inner(token, visited = None, order = None):
            if visited == None:
                visited = set()
            if order == None:
                order = []
            if token in visited:
                return order

            visited.add(token)
            if Synthesizer.__ground(token):
                order.append(token)
                return order

            for pr in prod_rules[token]:
                for t in pr:
                    __sort_inner(t, visited, order)
            order.append(token)
            return order
        return __sort_inner("S")
            
    def __evaluate_once(f):
        def wrapper(*args, **kwargs):
            if not wrapper.has_run:
                wrapper.has_run = True
                wrapper.value = f(*args, **kwargs)
            return wrapper.value
        wrapper.has_run = False
        return wrapper

    @__evaluate_once
    def __get_exapndable_tokens(self):
        """
        returns the non terminals that have no fixed size
        """
        def expanders_inner(token, visited = None, route = None, expanders = None):
            if visited == None:
                visited = set()
            if route == None:
                route = []
            if expanders == None:
                expanders = []
            if token in visited:
                if token in route or token in expanders:
                    expanders.extend(route)     # the complete route from the root are variables that expand on each iteration, so return all of them
                return expanders         # noting new found here
            route.append(token)
            visited.add(token)
            for pr in self.prod_rules[token]:
                for t in pr:
                    if t not in self.terminals:
                        expanders_inner(t, visited, route, expanders)
            route.pop()
            return expanders
        
        return set(expanders_inner("S"))

    @__evaluate_once
    def __get_expander_rules(self):
        expandables = self.__get_exapndable_tokens()
        expander_rules = []
        for t in expandables:
            for pr in self.prod_rules[t]:
                if any((t in expandables for t in pr)):
                    expander_rules.append(pr)
        return expander_rules
        # return set((pr for pr in (self.prod_rules[e] for e in expandables) if any((t in expandables for t in pr))))



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
                # test
                # if p1 == "((x==x)or(y!=y))" and p2 == "((y!=y)or(x==x))":
                #     print("did not merge right... This is problematic")
                # end of test
                if equal_results(results[p1], results[p2]):
                    print(f"merged {p1} and {p2}")
                    program_equality_dict[p2] = p1
        
        new_examples = {p: get_equal_examples(self.examples[p], program_equality_dict) for p in self.examples}
        self.examples = new_examples
    
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

    def bottom_up_optimized(self, max_depth=4):
        def satisfies(cond, state: dict) -> bool:
            res = eval(cond, state) 
            assert(isinstance(res, bool))
            res = res if state[EXPECTED_RES_VAR] else not res
            return res

        def satisfies_all(cond, states):
            return all((satisfies(cond, s) for s in states))

        def grow_pr(pr):
            if len(pr) == 1:
                return self.examples[pr[0]]
            return [e1 + e2 for e1 in self.examples[pr[0]] for e2 in grow_pr(pr[1:])]

        for t in self.__generation_order:
            if t in self.non_terminals:
                self.examples[t] = set(flatten([grow_pr(pr) for pr in self.prod_rules[t]]))

        for i in range(max_depth):
            self.__grow_merge()
        for program in self.examples["S"]:
            if satisfies_all(program, self.states):
                yield program

if __name__ == "__main__":
    start = time.time()
    grammar = [
        "S ::= ( S BOOLOP S' ) | S'",
        "S' ::= ( VAR RELOP VAR )",
        "BOOLOP ::= and | or",
        "VAR ::= x | y | n",
        "RELOP ::= == | != | < | <="
    ]
    # grammar = [
    #     "S ::= ( S BOOLOP ( VAR RELOP VAR ) ) | ( VAR RELOP VAR )",
    #     "BOOLOP ::= and | or",
    #     "VAR ::= x | y | n",
    #     "RELOP ::= == | != | < | <="
    # ]
    start_gen = time.time()
    states = prog.generate_examples()
    print(f"time took start_gen: {time.time() - start_gen}")
    synthesizer = Synthesizer.from_text(grammar, states)
    # print(f"expanders are: {synthesizer.__get_exapndable_tokens()}")
    print(set(synthesizer.bottom_up_optimized(3)))
    # print(set(synthesizer.bottom_up_enumeration(4)))
    print(f"time took synthesizer: {time.time()-start} seconds")
    # TODO: something is wrong with the merge function, fix it!!!!!!