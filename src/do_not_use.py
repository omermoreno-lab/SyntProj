from os import system, path
import re
import ast 
from typing import Any
MAX_DEPTH = 5
ABSTRACT_ATTR = "abstract_code"

grammar = None

def flatten(t):
    return [item for sublist in t for item in sublist]    

"""
Base class
prod rules: list of production rules
Every rule supports get_examples method
"""
class Rule:
    def __init__(self, prod_rules):
        self.prod_rules = prod_rules

"""
Token Rule
Can be either terminal or another production rule
"""
class TokenRule(Rule):
    is_terminal: bool
    def __init__(self, prod_rules):
        Rule.__init__(self, prod_rules)
        self.is_terminal = prod_rules[0].isLower()

    def get_examples(self, depth: int) -> list[Rule]:
        return (self.prod_rules if self.is_terminal else grammar.get_rule(self.prod_rules[0]).get_conjectures(depth - 1)) if depth > 0 else []

class EnumRule(Rule):
    def __init__(self, prod_rules):
        Rule.__init__(self, prod_rules)
    def get_examples(self, depth: int) -> list[Rule]:
        return [] if depth == 0 else flatten([rule.get_conjectures(depth - 1) for rule in self.prod_rules])

"""
A term rule is a single term without | in it. 
"""        
class TermRule(Rule):
    def __init__(self, prod_rules):
        Rule.__init__(self, prod_rules)
    def get_all_combinations(l: list[list]) -> list[str]:
        if len(l) == 1:
            return l[0]
        xs = TermRule.get_all_combinations(l[1:])
        return [s1 + s2 for s2 in xs for s1 in l[0]]

    def get_examples(self, depth: int) -> list[Rule]:
        return TermRule.get_all_combinations([r.get_conjectures(depth - 1) for r in self.prod_rules])

class Grammar:
    rules: dict
    def __init__(g: list[str]):
        rules = dict()
        for rule in g:
            rule_split = map(str.strip, rule.split("::="))
            assert len(rule_split) == 2
            rule_name = rule_split[0]
            rule_cases = map(str.strip, rule_split[1].split("|"))
            rule_body = [re.sub(' +', ' ', rule_case).split(" ") for rule_case in rule_cases] 
            rules[rule_name] = EnumRule([TokenRule(s) if s.isLower() else TermRule(s) for s in rule_body])
        return rules
    
    def get_rule(self, r_name: str):
        return self.rules[r_name]

    
def print_use():
    print("Enter grammar file *.g as first argument, and program file *.py as second argument")
    exit(0)

def main():
    if any((len(system.argv) != 3 ,re.match(".g$", system.argv[1]),re.match(".py$", system.argv[2]))):
        print_use()
    try:
        f_grammar = open(system.argv[1], 'r')
        f_prog = open(system.argv[2], 'r')
    except:
        print_use()
    
    grammar = Grammar(map(lambda s : s.strip(), f_grammar.readlines()))
    invariants = grammar.get_rule("S").get_conjectures(MAX_DEPTH)

class ConverterNodeVisitor(ast.NodeVisitor):
    abstract_code = ""

    @classmethod
    def get_abstract_code(cls):
        return cls.abstract_code

    def visit_Module(self, node: ast.Module) -> Any:
        ret_val =  super().generic_visit(node)
        print("module blocks: " + str([t.abstract_code for t in node.body]))
        s =  " ; ".join([t.abstract_code for t in node.body])
        setattr(node, ABSTRACT_ATTR, s)
        self.abstract_code = s
        return ret_val

    def visit_Assign(self, node: ast.Assign) -> Any:
        ret_val = super().generic_visit(node)
        targets = [t.id for t in node.targets]
        # print("assigned arguments are: " + str(targets))
        val = node.value.abstract_code
        s = " ; ".join("".join(t, " := ", val) for t in targets)
        setattr(node, ABSTRACT_ATTR, s)
        return ret_val

    def visit_Expr(self, node: ast.Expr) -> Any:
        ret_val =  super().generic_visit(node)
        setattr(node, ABSTRACT_ATTR, getattr(node.value, ABSTRACT_ATTR))
        return ret_val
    
    # def visit_Expression(self, node: ast.Expression) -> Any:
    #     # TODO: insert code here
    #     ret_val = super().generic_visit(node)
        
    def visit_BoolOp(self, node):
        # TODO: insert code here
        ret_val = ast.NodeVisitor.generic_visit(self, node)
        op = node.op
        

    def visit_BinOp(self, node):
        # TODO: insert code here
        ast.NodeVisitor.generic_visit(self, node) 

    def visit_For(self, node):
        # TODO: insert code here
        ast.NodeVisitor.generic_visit(self, node) 

    def visit_If(self, node):
        # TODO: insert code here
        ast.NodeVisitor.generic_visit(self, node) 

    def visit_While(self, node):
        # TODO: insert code here
        ast.NodeVisitor.generic_visit(self, node) 
    
    def visit_Call(self, node):
        # TODO: insert code here
        ast.NodeVisitor.generic_visit(self, node) 

    def visit_Constant(self, node: ast.Constant) -> Any:
        # TODO: insert code here
        return super().visit_Constant(node)

    # def visit_BoolOp(self, node):
    #     # TODO: insert code here
    #     ast.NodeVisitor.generic_visit(self, node) 

    # def visit_BinOp(self, node):
    #     # TODO: insert code here
    #     ast.NodeVisitor.generic_visit(self, node) 

    
def convert_to_abstract_code(filename: str):
    out_name = path.splitext(filename)[0] + '.abs'
    cv = ConverterNodeVisitor()
    with open(filename, 'r') as source, open(out_name, 'w') as dest:
        for (i, line) in enumerate(source):
            tree = ast.parse(line)
            abs_code = cv.visit(tree).buffer
            delim = " ; " if i != 0 else ""
            dest.write(delim.concat(abs_code))


def test1():
    s = "test1.py"
    convert_to_abstract_code(s)


if __name__ == "__main__":
#    main() 
    test1()

    
