import os
import sys
sys.path.insert(1, os.path.abspath(""))
sys.path.insert(1, os.path.abspath("lib/"))

from z3.z3 import *
from lib.adt.tree import Tree
from lib.parsing.earley.earley import Grammar, Parser, ParseTrees
from lib.parsing.silly import SillyLexer
import operator
import z3

import unittest

OP = {'+': operator.add, '-': operator.sub,
      '*': operator.mul, '/': operator.floordiv,
      '!=': operator.ne, '>': operator.gt, '<': operator.lt,
      '<=': operator.le, '>=': operator.ge, '=': operator.eq,
      "==": operator.eq, "and": And, "or": Or, "not": Not, "in": Contains}
SUPPORTED_FUNCTIONS = {"len": z3.Length}
# I currently dithced this part, maybe later
# class SimplePyParser(object):

#     TOKENS = r"if else while for in and or lambda (?P<bool>True|False) (?P<lb>\n) (?P<id>[^\W\d]\w*)  " \
#              r" (?P<string>\"[^\"]*\") (?P<num>[+\-]?\d+) (?P<op_assign>[+-]=)  (?P<op>[!<>=]=|([+\-*/<>])) " \
#              r"(?P<lparen>\() (?P<rparen>\)) (?P<lbrace>\{) (?P<rbrace>\}) (?P<colon>:) " \
#              r"(?P<lbracket>\[) (?P<rbracket>\]) (?P<assign>=) (?P<comma>,)".split()
#     GRAMMAR = r"""
#     S   ->   S1 | S1 lb | S1 lb S
#     S1  ->   ASSIGN | OP_ASSIGN | FOR | WHILE | IF | IF_ELSE | FUNC_CALL
#     ASSIGN -> id assign E | id assign ASSIGN
#     OP_ASSIGN -> id op_assign E
#     E   ->   E0   |  E0 op E
#     E0 -> id | num | bool | string | FUNC_CALL | LAMBDA | LIST | LIST_MEMBER
#     LIST_MEMBER -> id lbracket E rbracket
#     FOR -> for id in id colon BLOCK
#     WHILE -> while E colon BLOCK
#     IF -> if E colon BLOCK
#     IF_ELSE -> if E colon BLOCK LBS else colon BLOCK
#     FUNC_CALL -> id lparen LIST_CONT rparen
#     LAMBDA -> lambda ARGS_LIST colon E
#     LIST -> lbracket LIST_CONT rbracket
#     LIST_CONT -> LIST_INTER | TERMINATOR
#     LIST_INTER -> E | E comma LIST_INTER
#     ARGS_LIST -> id | id comma ARGS_LIST
#     BLOCK -> lb lbrace lb S LBS rbrace
#     LBS -> lb LBS | TERMINATOR
#     TERMINATOR -> 
    
#     """
#     # S1 -> ASSIGN    |   IF_ELSE   |   IF   |    WHILE    |    FOR
#     # IF_ELSE -> if E colon BLOCK else colon BLOCK
#     # BLOCK -> lb
#     # lbrace
#     # S
#     # lb
#     # rbrace
#     # IF -> if E colon BLOCK
#     # WHILE -> while E colon BLOCK
#     # FOR -> for id in ITER colon BLOCK
#     # E0  ->   id | id lbracket NUM rbracket | id lparen NUM rparen | LIST | TUPLE | num | bool
#     # E0  ->   lparen E rparen
#     # ITER -> id | LIST | TUPLE
#     # LIST ->   lbracket ITER_CONT rbracket | lbracket rbracket
#     # TUPLE -> lparen ITER_CONT rparen | lparen rparen
#     # ITER_CONT -> E0 | E0 comma ITER_CONT
#     # NUM ->   id | num

#     # TODO: add function use in parser

#     def __init__(self):
#         self.tokenizer = SillyLexer(self.TOKENS)
#         self.grammar = Grammar.from_string(self.GRAMMAR)

#     def __call__(self, program_text):
#         def add_braces(t):
#             lines = t.split('\n')
#             prev_level = 0
#             new_lines = []
#             for line in lines:
#                 level = 0
#                 if line and line[0] == ' ':
#                     level = (len(line) - len(line.lstrip(' '))) // 4
#                 elif line and line[1] == '\t':
#                     level = (len(line) - len(line.lstrip('\t')))
#                 new_line = ((level-prev_level)* '{\n') + ((prev_level-level)* '}\n') + line.lstrip('\t')
#                 new_lines.append(new_line)
#                 prev_level = level
#             new_lines.append(prev_level*"}")
#             return "\n".join(new_lines)

#         program_text = add_braces(program_text)
#         tokens = list(self.tokenizer(program_text))
#         # print(f"Code with added braces:\n{program_text}")
#         # print(50*'-')
#         # print(f"Program Tokens: {tokens}")
#         earley = Parser(grammar=self.grammar, sentence=tokens, debug=False)      # TODO: change to False when not testing
#         earley.parse()
        
#         if earley.is_valid_sentence():
#             # print("Program is valid, please ignore other prints")
#             trees = ParseTrees(earley)
#             print(50 * '-')
#             # print(trees)
#             assert(len(trees) == 1)
#             return self.postprocess(trees.nodes[0])
#         else:
#             return None

#     def postprocess(self, t):
#         def get_last_assign(t: Tree):
#             return t.subtrees[2] if t.subtrees[2].root == "E" else get_last_assign(t.subtrees[2])
#         if t.root == "S":
#             print("S rule")
#             return self.postprocess(t.subtrees[1]) + ("\n" + self.postprocess(t.subtrees[2]) if len(t.subtrees) == 3 else "")
#         elif t.root == "S1":
#             print("S1 rule")
#             return self.postprocess(t.subtrees[0])
#             # return self.postprocess(t.subtrees[0]) + ("" if len(t.subtrees) == 1 else t.subtrees[2].concat(self.postprocess(t.subtrees[3])))
#         elif t.root == "ASSIGN":
#             id = t.subtrees[0].subtrees[0].root
#             expr_node = get_last_assign(t)
#             return id + " := " + self.postprocess(expr_node)
#         elif t.root == "E0":
#             print("E0 rule")

#         elif t.root == "NUM":
#             print("NUM rule")
#         elif t.root == "SPACES":
#             print("SPACES rule")

#     def to_z3(self, expr: Tree):
#         # TODO: define a var_to_type dictionary
#         if expr.root == "E":
#             ret_val = self.to_z3(expr.subtrees[0])
#             if len(expr.subtrees) == 3:
#                 ret_val = OP[expr.subtrees[1].root](ret_val, self.to_z3(expr.subtrees[2]))
#             return ret_val
#         elif expr.root == "E0":
#             return self.to_z3(expr.subtrees[0])
#         elif expr.root == "id":
#             pass
#             # return var_to_z3[expr.subtrees[0].root]
#         elif expr.root == "num":
#             # TODO: add functionality for floats
#             return int(expr.subtrees[0].root)
#         elif expr.root == "bool":
#             return bool(expr.subtrees[0].root)
#         elif expr.root == "string":
#             return expr.subtrees[0].root
#         # elif expr.root == "FUNC_CALL":
#         #     pass
#         # elif expr.root == "LAMBDA":
#         #     pass
#         # elif expr.root == "LIST":
#         #     pass
#         # elif expr.root == "LIST_MEMBER":
#         #     pass



class PyExprParserError(Exception):
    """Exception raised for errors in the expression parser.

    Attributes:
        expression -- input expression in which the error occurred
        message -- explanation of the error
    """

    pass


class PostProcessError(PyExprParserError):
    def __init__(self, tree):
        self.tree = tree
        self.message = f"No right rule found when exploring {tree.root} node"


class PyExprParser(object):
    TOKENS = r"if else while for in lambda and or not (?P<bool>True|False) (?P<lb>\n) (?P<id>[^\W\d]\w*)  " \
             r" (?P<string>\"[^\"]*\") (?P<num>[+\-]?\d+) (?P<op_assign>[+-]=)  (?P<op>[!<>=]=|([+\-*/<>])) " \
             r"(?P<lparen>\() (?P<rparen>\)) (?P<lbrace>\{) (?P<rbrace>\}) (?P<colon>:) " \
             r"(?P<lbracket>\[) (?P<rbracket>\]) (?P<assign>=) (?P<comma>,)".split()
    GRAMMAR = r"""
        E   ->   E0  |  lparen E rparen  |  E0 op E  |  E or E  |  E and E  |  not E  |  E in E
        E0 -> id | num | bool | string | FUNC_CALL | LAMBDA | LIST | ITERABLE_MEMBER
        ITERABLE_MEMBER -> id lbracket E rbracket
        FUNC_CALL -> id lparen LIST_CONT rparen
        LAMBDA -> lambda id colon E
        LIST -> lbracket LIST_CONT rbracket
        LIST_CONT -> LIST_INTER | TERMINATOR
        LIST_INTER -> E | E comma LIST_INTER
        ARGS_LIST -> id | id comma ARGS_LIST
        TERMINATOR -> 
        """
    var_to_z3: dict[str:z3.ExprRef]
    lambda_count = 0
    list_count = 0

    @staticmethod
    def generate_lambda():
        PyExprParser.lambda_count += 1
        return f"lambda_{PyExprParser.lambda_count - 1}"

    @staticmethod
    def generate_list():
        PyExprParser.list_count += 1
        return f"list_{PyExprParser.list_count - 1}"

    def __init__(self, var_to_z3):
        self.tokenizer = SillyLexer(self.TOKENS)
        self.grammar = Grammar.from_string(self.GRAMMAR)
        self.var_to_z3 = var_to_z3

    def __call__(self, program_text):
        tokens = list(self.tokenizer(program_text))
        # print(f"Program Tokens: {tokens}")
        earley = Parser(grammar=self.grammar, sentence=tokens, debug=False)  # TODO: change to False when not testing
        earley.parse()

        if earley.is_valid_sentence():
            # print("Program is valid, please ignore other prints")
            trees = ParseTrees(earley)
            # print(50 * '-')
            # print(trees)
            assert (len(trees) == 1)
            return self.postprocess(trees.nodes[0])
        else:
            return None

    def postprocess(self, t: Tree, constraints=None):
        # TODO: change from if-else to dictionary-based matching
        if constraints is None:
            constraints = []
        if t.root == "γ":
            return self.postprocess(t.subtrees[0])
        elif t.root == "E":
            if len(t.subtrees) == 1:
                return self.postprocess(t.subtrees[0], constraints)
            elif len(t.subtrees) == 2:
                operand = self.postprocess(t.subtrees[1], constraints)
                operation = OP[t.subtrees[0].root]
                return operation(operand)
            elif len(t.subtrees) == 3:
                if t.subtrees[0].root == "lparen":
                    return self.postprocess(t.subtrees[1])
                else:
                    left_operand = self.postprocess(t.subtrees[0], constraints)
                    right_operand = self.postprocess(t.subtrees[2], constraints)
                    operation = OP[t.subtrees[1].subtrees[0].root] if t.subtrees[1].root == "op" else OP[t.subtrees[1].root]
                    if operation == "in":
                        left_operand, right_operand = right_operand, left_operand
                    return operation(left_operand, right_operand)
            else:
                raise ValueError("provided E with an invalid number of subtrees")
        elif t.root == "E0":
            return self.postprocess(t.subtrees[0], constraints)
        # bool | string | FUNC_CALL | LAMBDA | LIST | ITERABLE_MEMBER
        elif t.root == "id":
            return self.var_to_z3[t.subtrees[0].root]
        elif t.root == "num":
            return int(t.subtrees[0].root)
        elif t.root == "bool":
            return bool(t.subtrees[0].root)
        elif t.root == "string":
            return t.subtrees[0].root
        elif t.root == "ITERABLE_MEMBER":
            typed_id = self.postprocess(t.subtrees[0], constraints)
            idx = self.postprocess(t.subtrees[2], constraints)
            return typed_id[idx]
        elif t.root == "FUNC_CALL":
            # id lparen LIST_CONT rparen
            func_name = t.subtrees[0].subtrees[0].root
            if func_name not in SUPPORTED_FUNCTIONS:
                raise PostProcessError(t)
            f = SUPPORTED_FUNCTIONS[func_name]
            arguments = self.postprocess(t.subtrees[2])
            return f(arguments)
        elif t.root == "LIST_CONT":
        #   LIST_CONT -> LIST_INTER | TERMINATOR
        #   LIST_INTER -> E | E comma LIST_INTER
            return self.postprocess(t.subtrees[0])
        elif t.root == "TERMINATOR":
            return []
        elif t.root == "LIST_INTER":
            curr = [self.postprocess(t.subtrees[0])]
            tail = self.postprocess(t.subtrees[2]) if len(t.subtrees) == 3 else []
            return curr + tail
        raise PostProcessError(t)

        # elif t.root == "FUNC_CALL":
        #     # id lparen LIST_CONT rparen
        #     f = t.subtrees[0].subtrees[0].root
        #     cont = PyExprParser.get_list_cont(t.subtrees[2])
        #     return eval(f"f[{','.join(cont)}]")
        # elif t.root == "LAMBDA":
        #     # TODO: this option must support type inference in order to work, so meanwhile don't use it
        #     #  I'm adding code for how it should look like
        #     arg = t.subtrees[1].subtrees[0].root
        #     id = PyExprParser.generate_lambda()
        #     expr = self.postprocess(t.subtrees[3], constraints)
        #     # declare lambda as function
        #     # add constraint forall x: f(x) = (expression inside lambda)
        # elif t.root == "LIST":
        #     # currently supporting only lists of ints
        #     l_name = PyExprParser.generate_list()


def prove(f):
    s = Solver()
    s.add(Not(f))
    if s.check() == unsat:
        return True, None
    else:
        return False, s.model()


def run_test(tester, cond, vars, expected):
    parser = PyExprParser(vars)
    try:
        res = parser(cond)
    except PyExprParserError as e:
        raise e
    # tester.assertEqual(cond, str(res))
    
    check = And(Implies(res, expected), Implies(expected,res))
    tester.assertTrue(prove(check)[0])


class TestPyExprParser(unittest.TestCase):
    
    def test_simple_ints(self):
        vars = {"x": z3.Int("x"), "y": z3.Int("y")}
        cond = "x < y"
        expected = vars["x"] < vars["y"]
        run_test(self, cond, vars, expected)

    def test_simple_num(self):
        vars = {"x": z3.Int("x"), "y": z3.Int("y")}
        cond = "x < 1"
        expected = vars["x"] < 1
        run_test(self, cond, vars, expected)

    def test_and_operator(self):
        vars = {"x": z3.Int("x"), "y": z3.Int("y")}
        cond = "x < y and y < 1"
        expected = And(vars["x"] < vars["y"], vars["y"] < 1)
        run_test(self, cond, vars, expected)

    def test_or_operator(self):
        vars = {"x": z3.Int("x"), "y": z3.Int("y")}
        cond = "x <= y or not y >= -1025"
        expected = Or(vars["x"] <= vars["y"], Not(vars["y"] >= -1025))
        run_test(self, cond, vars, expected)


if __name__ == '__main__':
    unittest.main()

# if __name__ == '__main__':
#     with open('./src/test1.py', 'r') as f:
#         text = f.read()
#     ast = SimplePyParser()(text)
    
#     if ast:
#         print(">> Valid program.")
#         print(ast)
#     else:
#         print(">> Invalid program.")


