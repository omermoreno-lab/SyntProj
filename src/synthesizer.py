# from lib.adt.tree import Visitor
import time
import typing
from itertools import chain
import prog
import json
import enum
import itertools
EXPECTED_RES_VAR = "expected_res" 


def flatten(t):
    return [item for sublist in t for item in sublist]

def safe_evaluate(program, state):
            try:
                return eval(program, state)
            except BaseException as e:
                return str(e)

"""
a class used for comfortability only, in case eval() does not return a result and one still wants to insert it into the results list
used for example in case "<" and ">" will try to be merged because they are not valid expressions
"""
class NoEqual:
    def __init__(self):
        pass

    def __eq__(self, other):
        return False


class MergeOptimizationType(enum.Enum):
    NO_OPT = 0
    BOOL_OPT = 1
    HASH_OPT = 2


class ExplorationOptType(enum.Enum):
    NO_OPT = enum.auto()
    INV_PATTERN_OPT = enum.auto()
    AND_OPT = enum.auto()



class Synthesizer(object):
    prod_rules: typing.Dict[str, list[list[str]]]         # token -> production rules dictionary
    examples: typing.Dict[str, typing.Set[str]]           # token -> generated program examples of this token. for example, examples["Var"] = [x, y, z]
    terminals: list
    non_terminals: list[str]
    states: list[dict]
    tokens: list[str]
    prev_new_examples: dict		# TODO: add type hint here
    program_result: dict
    encoding_to_example: dict
    example_to_encoding: dict

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
        self.encoding_to_example = {}
        self.example_to_encoding = {}
        print(f"Synth init:\n\
            tokens = {self.tokens}\n\
            terminals = {self.terminals}\n\
            non_terminals = {self.non_terminals}\n\
            prod_rules = {self.prod_rules}\n\
            examples = {self.examples}\n\
            generation_order = {self.__generation_order}\n\
            expandable_tokens = {self.__get_exapndable_tokens()}")

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
    def from_files(grammar_file_path, states_file_path):
        with open(grammar_file_path, 'r') as f:
            grammar_list = f.read().split("\n")
        with open(states_file_path, 'r') as f:
            state_list = json.load(f)
        state_list[0][0] = EXPECTED_RES_VAR
        return Synthesizer.from_text(grammar_list, state_list)

    @staticmethod
    def from_folder(folder_path):
        return Synthesizer.from_files(f"{folder_path}/grammar.txt", f"{folder_path}/records.json")

    @staticmethod
    def __ground(s):
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
        program_evaluation = [safe_evaluate(program, state) for state in self.states]
        self.program_result[program] = program_evaluation
        return program_evaluation

    def get_results_encoding(self, program):
        if program in self.example_to_encoding:
            return self.example_to_encoding[program]

        encoding = 0
        assert(type(self.get_program_results(program)[0]) == bool)
        for idx, flag in enumerate(reversed(self.get_program_results(program))):
            encoding ^=  flag << idx
        return encoding

    @staticmethod
    def hash_results(to_hash):
        cls = type(to_hash)
        if cls in (int, str, bool):
            return hash(to_hash)
        if cls == list:
            return hash(tuple([Synthesizer.hash_results(v) for v in to_hash]))
        raise TypeError(f"Current type is not supported, type is {cls}")

    def get_results_hash(self, program):
        if program in self.example_to_encoding:
            return self.example_to_encoding[program]

        return Synthesizer.hash_results(self.get_program_results(program))

    def __grow_merge(self, optimization_type: MergeOptimizationType):
        """
        This is our try to make an efficient grow function,
        We would like to apply two techniques:
        1. Equivalent invariant elimination during synthesis
        2. ordered synthesis, where one can count only on new examples for the synthesis, and use the previuos examples where necessary
        """
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

            # This is the right way to do the generation if we were using generators
            # tail_new = ((oe + ne) for ne in tail_ne for oe in token_oe)		            # new examlpes from tail
            # curr_new = ((ne + oe) for oe in tail_oe for ne in token_ne)		            # new examples from current token
            # all_new = ((ne1 + ne2) for ne2 in tail_ne for ne1 in token_ne)	            # new examples from both

            if len(token_ne) != 0:
                tail_oe = list(tail_oe)                                                     # evaluate the rest of the examples if we need to pass on them for more than once

            # This is the order we do the generation to give preference to the first tokens in examples
            tail_new = ((oe + ne) for oe in token_oe for ne in tail_ne)		                # new examlpes from tail
            curr_new = ((ne + oe) for ne in token_ne for oe in tail_oe)		                # new examples from current token
            all_new = ((ne1 + ne2) for ne1 in token_ne for ne2 in tail_ne)	                # new examples from both

            new_programs = list(chain(tail_new, curr_new, all_new))
            old_programs = (oe1 + oe2 for oe1 in token_oe for oe2 in tail_oe)               
                                                                                            
            return new_programs, old_programs

        def is_expandable(pr):
            return any(t in self.__get_exapndable_tokens() for t in pr)

        def grow_token(t, new_examples):
            if t not in self.__get_exapndable_tokens():
                return
            new_examples[t] = flatten([(get_new_pr_examples(pr, new_examples)[0]) for pr in self.prod_rules[t] if is_expandable(pr)])
            
        def is_unique_default(example, other_examples):
            return all((any((res_e != res_oe for res_e, res_oe in zip(self.get_program_results(example), self.get_program_results(e)))) for e in other_examples))

        def make_unique_default(examples_iterable):
            unique_list = []
            for idx, e in enumerate(examples_iterable):
                if is_unique_default(e, examples_iterable[:idx]):
                    unique_list.append(e)
            unique_in_all_examples = [e for e in unique_list if is_unique_default(e, self.examples[token])]
            return unique_in_all_examples

        def make_unique_by_encoding(examples_iterable, encode_type: MergeOptimizationType):
            unique_dict = {}
            for e in examples_iterable:
                example_encoding = self.get_results_encoding(e) if encode_type == MergeOptimizationType.BOOL_OPT else self.get_results_hash(e)
                if example_encoding not in unique_dict:
                    unique_dict[example_encoding] = e
            return [example for encoding, example in unique_dict.items() if encoding not in self.encoding_to_example] 

        def make_unique(examples_iterable, optimization_type = MergeOptimizationType.HASH_OPT):
            if optimization_type == MergeOptimizationType.NO_OPT:
                return make_unique_default(examples_iterable)
            return make_unique_by_encoding(examples_iterable, optimization_type)

        new_examples = {}
        for token in self.__generation_order:
            if token not in self.__get_exapndable_tokens():
                continue
            grow_token(token, new_examples)
            is_root, new_token_examples = token == "S", new_examples[token]
            if optimization_type == MergeOptimizationType.BOOL_OPT:
                token_new_unique_examples = make_unique(new_token_examples, MergeOptimizationType.BOOL_OPT if is_root else MergeOptimizationType.NO_OPT)
            else:
                token_new_unique_examples = make_unique(new_token_examples, optimization_type)
            new_examples[token] = token_new_unique_examples
        
        self.prev_new_examples = {k: set(v) for k,v in new_examples.items()}
        # TODO: might be smart to also add the evaluation of programs only if they are added as examples
        print(f"new root examples: {new_examples['S']}")
        for example in new_examples['S']:
            encoding = self.get_results_hash(example) if optimization_type == MergeOptimizationType.HASH_OPT else self.get_results_encoding(example)
            self.encoding_to_example[encoding] = example
            self.example_to_encoding[example] = encoding
    
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
                return expanders                # nothing new found here
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
    
    def bottom_up_optimized(self, 
    max_depth, 
    merge_opt=MergeOptimizationType.HASH_OPT, 
    exp_opt=ExplorationOptType.NO_OPT,
    invariant_extension_format = "{}"):
        def satisfies(cond, state: dict) -> bool:
            try:
                res = eval(cond, state)
            except:
                res = False
            assert(isinstance(res, bool))
            res = res if state[EXPECTED_RES_VAR] else not res
            return res

        def satisfies_all(cond, states):
            return all((satisfies(cond, s) for s in states))

        def satisifies_positives(cond, states):
            return all((satisfies(cond, s) for s in states if s[EXPECTED_RES_VAR]))

        def grow_pr(pr):
            if pr[0] in self.__get_exapndable_tokens():
                return []
            if len(pr) == 1:
                return self.examples[pr[0]]
            return [e1 + e2 for e1 in self.examples[pr[0]] for e2 in grow_pr(pr[1:])]
        
        def init_graph():    
            for t in self.__generation_order:       # depth 1 exception
                if t in self.non_terminals:
                    self.examples[t] = set(flatten([grow_pr(pr) for pr in self.prod_rules[t]]))
                    # TODO: problem is in the line below, the rules for S after that rule are double boolops
                    self.prev_new_examples[t] = self.examples[t].copy()
            print(f"depth 1 root examples: {self.prev_new_examples['S']}")

        def format_invariant(inv):
            return invariant_extension_format.format(inv)

        def get_new_invariant_examples():
            return map(format_invariant, self.prev_new_examples['S'])

        for i in range(max_depth):
            print(f"starting depth: {i+1}")
            if i == 0:
                init_graph()        # This grows the synth depth by 1
            else:
                self.__grow_merge(merge_opt)
            invariant_candidates = list(get_new_invariant_examples())
            print(f"new invariant candidates: {invariant_candidates}")
            for program in invariant_candidates:
                if satisfies_all(program, self.states):
                    yield program
        
        if True:
            print("trying to produce and operator combinations")
            pos_sat_progs = [prog for prog in get_new_invariant_examples() if satisifies_positives(prog, self.states)]
            print(f"programs that satisfy the positive examples: {pos_sat_progs}")
            for L in range(2, len(pos_sat_progs)+1):
                for programs in itertools.combinations(pos_sat_progs, L):
                    program = " and ".join(programs)
                    if satisfies_all(program, self.states):     # TODO: if this affects performance this can be changed to satisfies_negatives
                        yield program


if __name__ == "__main__":
    start = time.time()
    grammar = [
        "S ::=  S' | ( S BOOLOP S' )",
        "S' ::= ( VAR RELOP VAR )",
        "BOOLOP ::= and | or",
        "VAR ::= x | y | n",
        "RELOP ::= == | != | < | <="
    ]

    start_gen = time.time()
    states = prog.generate_examples()
    print(f"time took start_gen: {time.time() - start_gen}")
    synthesizer = Synthesizer.from_text(grammar, states)
    print(set(synthesizer.bottom_up_optimized(1)))
    print(f"time took synthesizer: {time.time()-start} seconds")
