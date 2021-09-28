import re
import string
import prog

EXPECTED_RES_VAR = "expected_res" 
"""
Class storing all current programs

programs_map: mapping from  
"""
class Programs:
    def __init__(self):
        self.programs_map = dict()

    def insert(self, prog_type: string, prog_body: string):
        if prog_type not in self.programs_map:
            self.programs_map[prog_type] = set()
        self.programs_map[prog_type].add(prog_body)

    def insert_set(self, prog_type, progs: set):
        if prog_type in self.programs_map:
            self.programs_map[prog_type].update(progs)
        else:
            self.programs_map[prog_type] = progs

    def get(self, prog_type: string) -> set:
        return self.programs_map[prog_type]

    def merge(self, p_other):
        for (prog_type, progs) in p_other.programs_map.items():
            self.insert_set(prog_type, progs)


def ground(s):
    return s.isalnum() and not s.isupper()


def grow_program(prog_grow: str, programs, rules):
    progs = set()
    regex_nonterm = r"[A-Z]+"
    nonterms = set(re.findall(regex_nonterm, prog_grow))
    for nonterm in nonterms:
        for rule_body in rules[nonterm]:
            prog_replaced = prog_grow.replace(nonterm, rule_body, 1)
            progs_grown = grow_program(prog_replaced, programs, rules)
            if len(progs_grown) == 0:
                return {prog_replaced}
            progs |= progs_grown
    return progs


def grow(programs: Programs, rules):
    programs_added = Programs()
    for (rule_type, rule_bodys) in rules.items():
        for rule_body in rule_bodys:
            grow_set = grow_program(rule_body, programs, rules)
            programs_added.insert_set(rule_type, grow_set)
    return programs_added


def initial_programs(rules):
    programs = Programs()
    for (rules_type, rules_body) in rules.items():
        for rule_body in rules_body:
            if ground(rule_body):
                programs.insert(rules_type, rule_body)
    return programs


def program_sat(cond, examples):
    # expr = ""
    # for i in range(1, len(examples)):
    #     for j in range(1, len(examples[0])):
    #         expr += examples[0][j] + "="
    #         if type(examples[i][j]) == str:
    #             expr += "\"" + examples[i][j] + "\"\n"
    #         else:
    #             expr += str(examples[i][j]) + "\n"
    #     expr += "assert "
    #     if not examples[i][0]:
    #         expr += "not "
    #     expr += cond + "\n"
    # try:
    #     exec(expr)
    # except AssertionError:
    #     # print(f"expression {expr} failed {cond}")
    #     return False
    # return True
    def state_as_dictionary(variables: list, state: list):
        return dict(zip(variables, state))
    
    def satisfies(cond, state: dict) -> bool:
        res = eval(cond, state) 
        assert(isinstance(res, bool))
        res = res if state[EXPECTED_RES_VAR] else not res
        return res
    
    variables = examples[0]
    variables[0] = EXPECTED_RES_VAR
    states = [state_as_dictionary(variables, e) for e in examples[1:]]
    return all([satisfies(cond, s) for s in states])



def btm_up_enum(rules, spec, max_depth, root = "S"):
    programs = initial_programs(rules)
    invariants = []
    for i in range(max_depth):
        programs.merge(grow(programs, rules))
        # print(50 * '-' + "\nnew loop\n" + 50* '-')
        # for program in programs.get("S"):
        #     if program_sat(program, spec):
        #         yield program
    for program in programs.get(root):
        if program_sat(program, spec):
            yield program

def parse_grammar(g):
    rules = dict()
    for rule in g:
        rule_split = rule.split(" ::= ")
        assert len(rule_split) == 2
        rule_type = rule_split[0]
        rule_body = rule_split[1]
        rule_body = rule_body.split(" | ")
        rules[rule_type] = rule_body
    return rules


"""
adds logical rules to the rule set
return value: the new root of exploration tree
                this must be passed to btm_up_enum
"""
def add_logical_operator_exploration(rules) -> str:
    new_root = "LOGIC_ROOT"
    rules[new_root] = ["S", "S or S"]
    return new_root

def get_invariants(grammar, max_depth=4):
    rules = parse_grammar(grammar)
    print("parsed grammar")
    # print(rules)
    examples = prog.generate_examples()
    
    print("generated examples")
    # print(examples)
    return list(btm_up_enum(rules, examples, max_depth))

def get_property_suggestions(grammar, max_depth=4):
    rules = parse_grammar(grammar)
    examples = [p for p in prog.generate_examples() if p[0] != False]
    return list(btm_up_enum(rules, examples, max_depth))

"""
generates true invariant statements from the given already produced invariants
does so by taking the every combination of invariants and checking if the 
two ivnariants are satisfying all tests 
"""
# def generate_or_statements(candidates, states):
#     res_dict = [(candidate, [satisfies(candidate, states)]) for candidate in candidates]
#     for i, ()

if __name__ == '__main__':
    # USE S FOR STARTING SYMBOL
    # use VAR for program variables
    grammar = [
        "S ::= ( VAR RELOP VAR )",
        "VAR ::= x | y | n",
        "RELOP ::= == | != | < | <="
    ]
    print(get_invariants(grammar))


