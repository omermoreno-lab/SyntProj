import re
import string
import prog


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


def grow_program(prog_grow: string, programs, rules):
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
    expr = ""
    for i in range(1, len(examples)):
        for j in range(1, len(examples[0])):
            expr += examples[0][j] + "="
            if type(examples[i][j]) == str:
                expr += "\"" + examples[i][j] + "\"\n"
            else:
                expr += str(examples[i][j]) + "\n"
        expr += "assert "
        if not examples[i][0]:
            expr += "not "
        expr += cond + "\n"
    try:
        exec(expr)
    except AssertionError:
        return False
    return True


def btm_up_enum(rules, spec):
    programs = initial_programs(rules)
    while True:
        programs.merge(grow(programs, rules))
        for program in programs.get("S"):
            if program_sat(program, spec):
                return program


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


def get_conjectures(grammar):
    rules = parse_grammar(grammar)
    examples = prog.generate_examples()
    return btm_up_enum(rules, examples)



if __name__ == '__main__':
    # USE S FOR STARTING SYMBOL
    # use VAR for program variables
    grammar = [
        "S ::= ( VAR RELOP VAR )",
        "VAR ::= x | y | n",
        "RELOP ::= == | != | < | <="
    ]
    get_conjectures(grammar)
