# from lib.adt.tree import Visitor
import time
import typing
# import functools
from itertools import chain
# from typing_extensions import IntVar
import prog
import json
EXPECTED_RES_VAR = "expected_res" 


def flatten(t):
    return [item for sublist in t for item in sublist]


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
    prev_new_examples: dict		# TODO: add type hint here
    program_result: dict

    def __init__(self, tokens, prod_rules, states):
        self.tokens = tokens
        self.terminals = [t for t in tokens if Synthesizer.__ground(t)]
        self.non_terminals = [t for t in tokens if not Synthesizer.__ground(t)]
        self.prod_rules = prod_rules
        self.examples = {t: {t} for t in self.terminals} | {nt: set() for nt in self.non_terminals}
        self.states = states
        self.__generation_order = Synthesizer.__dfs_sort(self.prod_rules)
        self.prev_new_examples = {t: {t} for t in self.terminals}
        self.program_result = {}
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
    def from_files(grammar_file_path, states_file_path):
        with open(grammar_file_path, 'r') as f:
            grammar_list = f.read().split("\n")
        with open(states_file_path, 'r') as f:
            state_list = json.load(f)
        # with open(env_setting_file_path, 'r') as f:
        #     vars = list(json.load(f).keys())
        # vars.insert(0, EXPECTED_RES_VAR)
        # state_list.insert(0, vars)
        state_list[0][0] = EXPECTED_RES_VAR
        return Synthesizer.from_text(grammar_list, state_list)

    @staticmethod
    def from_folder(folder_path):
        return Synthesizer.from_files(f"{folder_path}/grammar.txt", f"{folder_path}/records.json")

    @staticmethod
    def __ground(s):
            # return s.isalnum() and not s.isupper()
            return not s.isupper()

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


    def get_program_results(self, program):
        if program in self.program_result:
            return self.program_result[program]
        program_evaluation = [eval(program, state) for state in self.states]
        self.program_result[program] = program_evaluation
        return program_evaluation

    def __grow_merge(self, merge_all_flag):
        """
        This is our try to make an efficient grow function,
        We would like to apply two techniques:
        1. Equivalent invariant elimination during synthesis
        2. ordered synthesis, where one can count only on new examples for the synthesis, and use the previuos examples where necessary
        """
        # def make_unique(examples_iterable):
        #     unique_list = []
        #     for idx, e in enumerate(examples_iterable):
        #         if is_unique(e, examples_iterable[:idx]):
        #             unique_list.append(e)
        #     return unique_list
        
        def get_new_pr_examples(pr, new_examples):          # pr stands for production rule
            if len(pr) == 0:
                raise ValueError("tried expanding empty production rule")
            first_token = pr[0]
            if len(pr) == 1:
                return new_examples[first_token] if first_token in new_examples else [], \
                   self.examples[first_token]
            
            tail_ne, tail_oe = get_new_pr_examples(pr[1:], new_examples)     # new examples and old examples
            token_ne = self.prev_new_examples[first_token] if first_token in self.prev_new_examples else []
            token_oe = self.examples[first_token]

            tail_new = ((oe + ne) for ne in tail_ne for oe in token_oe)		            # new examlpes from tail
            curr_new = ((ne + oe) for oe in tail_oe for ne in token_ne)		            # new examples from current token
            all_new = ((ne1 + ne2) for ne2 in tail_ne for ne1 in token_ne)	            # new examples from both
                
            new_programs = list(chain(tail_new, curr_new, all_new))
            old_programs = [oe1 + oe2 for oe2 in tail_oe for oe1 in token_oe]       # TODO: This is expensive, might not want to do this that way
            return new_programs, old_programs

        def is_expandable(pr):
            return any(t in self.__get_exapndable_tokens() for t in pr)

        def grow_token(t, new_examples):
            if t not in self.__get_exapndable_tokens():
                return
            new_examples[t] = flatten([(get_new_pr_examples(pr, new_examples)[0]) for pr in self.prod_rules[t] if is_expandable(pr)])
            
        # def merge_token_new_examples(token, new_examples, )

        def is_unique(example, other_examples):
            # print(f"example: {example}, other_examples: {other_examples}")
            return all((any((res_e != res_oe for res_e, res_oe in zip(self.get_program_results(example), self.get_program_results(e)))) for e in other_examples))

        new_examples = {}
        for token in self.__generation_order:
            grow_token(token, new_examples)
            # TODO: implement merge_token function that will merge expandable token's examples after generation
        
        if merge_all_flag:
            unique_examples = {t: {ne for ne in new_examples[t] if is_unique(ne, self.examples[t])} for t in new_examples}
            # print(f"unique_examples: {unique_examples}")
            # print(f"current examples: {self.examples}")
            self.prev_new_examples = unique_examples
            for t in unique_examples:
                # print(f"t = {t}")
                self.examples[t] = self.examples[t].union(unique_examples[t])
            # print(f"S examples: {self.examples['S']}")
        else:
            new_examples = {t: set(val) for t, val in new_examples.items()}
            new_examples['S'] = {ne for ne in new_examples['S'] if is_unique(ne, self.examples['S'])}
            for t in new_examples:
                # print(f"t = {t}")
                self.examples[t] = self.examples[t].union(new_examples[t])
    
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
            if visited is None:
                visited = set()
            if route is None:
                route = []
            if expanders is None:
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
    
    

    def bottom_up_optimized(self, max_depth, merge_all_flag):
        def satisfies(cond, state: dict) -> bool:
            res = eval(cond, state) 
            assert(isinstance(res, bool))
            res = res if state[EXPECTED_RES_VAR] else not res
            return res

        def satisfies_all(cond, states):
            return all((satisfies(cond, s) for s in states))

        def grow_pr(pr):
            if pr[0] in self.__get_exapndable_tokens():
                return []
            if len(pr) == 1:
                return self.examples[pr[0]]
            return [e1 + e2 for e1 in self.examples[pr[0]] for e2 in grow_pr(pr[1:])]
        

        for t in self.__generation_order:       # depth 1 exception
            if t in self.non_terminals:
                self.examples[t] = set(flatten([grow_pr(pr) for pr in self.prod_rules[t]]))
                # TODO: problem is in the line below, the rules for S after that rule are double boolops
                # self.prev_new_examples[t] = set(flatten([grow_pr(pr) for pr in self.prod_rules[t]]))
                self.prev_new_examples[t] = self.examples[t].copy()
            
        for program in self.prev_new_examples['S']:
            if satisfies_all(program, self.states):
                # print(f"program returned: {program}")
                yield program

        for i in range(1, max_depth):
            print(f"starting depth: {i+1}")
            self.__grow_merge(merge_all_flag)
            for program in self.prev_new_examples['S']:
                if satisfies_all(program, self.states):
                    # print(f"program returned: {program}")
                    yield program

        # for i in range(max_depth-1):
            
        #     for program in self.prev_new_examples['S']:
        #         if satisfies_all(program, self.states):
        #             # print(f"program returned: {program}")
        #             yield program
        #     print(f"starting depth: {i+2}")
        #     self.__grow_merge(merge_all_flag)
        
        # print(f"all S programs: {self.examples['S']}")
        # for program in self.prev_new_examples['S']:
        #     if satisfies_all(program, self.states):
        #         # print(f"program returned: {program}")
        #         yield program
        

        


if __name__ == "__main__":
    start = time.time()
    grammar = [
        "S ::=  S' | ( S BOOLOP S' )",
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
    print(set(synthesizer.bottom_up_optimized(1)))
    # print(set(synthesizer.bottom_up_enumeration(4)))
    # print(set(synthesizer.bottom_up_enumeration(4)))
    print(f"time took synthesizer: {time.time()-start} seconds")
    # TODO: something is wrong with the merge function, fix it!!!!!!
