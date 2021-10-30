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




class PyExprParserError(Exception):
    """Exception raised for errors in the expression parser.

    Attributes:
        expression -- input expression in which the error occurred
        message -- explanation of the error
    """

    pass


class SimplePyParserError(Exception):
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
    root = None
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
        self.root = None

    def with_var_to_z3(self, var_to_z3):
        self.var_to_z3 = var_to_z3
        return self

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
            self.root = trees.nodes[0]
            return self
        else:
            raise ValueError(f"Expression parser failed, got an invalid sentence {program_text}")


    def as_z3(self):
        return self._as_z3_inner(self.root)


    def _as_z3_inner(self, t: Tree, constraints=None):
        # TODO: change from if-else to dictionary-based matching
        if constraints is None:
            constraints = []
        if t.root == "γ":
            return self._as_z3_inner(t.subtrees[0])
        elif t.root == "E":
            if len(t.subtrees) == 1:
                return self._as_z3_inner(t.subtrees[0], constraints)
            elif len(t.subtrees) == 2:
                operand = self._as_z3_inner(t.subtrees[1], constraints)
                operation = OP[t.subtrees[0].root]
                return operation(operand)
            elif len(t.subtrees) == 3:
                if t.subtrees[0].root == "lparen":
                    return self._as_z3_inner(t.subtrees[1])
                else:
                    left_operand = self._as_z3_inner(t.subtrees[0], constraints)
                    right_operand = self._as_z3_inner(t.subtrees[2], constraints)
                    operation = OP[t.subtrees[1].subtrees[0].root] if t.subtrees[1].root == "op" else OP[t.subtrees[1].root]
                    if operation == "in":
                        left_operand, right_operand = right_operand, left_operand
                    return operation(left_operand, right_operand)
            else:
                raise ValueError("provided E with an invalid number of subtrees")
        elif t.root == "E0":
            return self._as_z3_inner(t.subtrees[0], constraints)
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
            typed_id = self._as_z3_inner(t.subtrees[0], constraints)
            idx = self._as_z3_inner(t.subtrees[2], constraints)
            return typed_id[idx]
        elif t.root == "FUNC_CALL":
            # id lparen LIST_CONT rparen
            func_name = t.subtrees[0].subtrees[0].root
            if func_name not in SUPPORTED_FUNCTIONS:
                raise PostProcessError(t)
            f = SUPPORTED_FUNCTIONS[func_name]
            arguments = self._as_z3_inner(t.subtrees[2])
            return f(arguments)
        elif t.root == "LIST_CONT":
        #   LIST_CONT -> LIST_INTER | TERMINATOR
        #   LIST_INTER -> E | E comma LIST_INTER
            return self._as_z3_inner(t.subtrees[0])
        elif t.root == "TERMINATOR":
            return []
        elif t.root == "LIST_INTER":
            curr = [self._as_z3_inner(t.subtrees[0])]
            tail = self._as_z3_inner(t.subtrees[2]) if len(t.subtrees) == 3 else []
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


class SimplePyParser(object):

    TOKENS = r"if else while for in (?P<lb>\n) (?P<id>[^\W\d]\w*)  " \
             r"(?P<colon>:) (?P<lbrace>\{) (?P<rbrace>\}) (?P<assign>=) (?P<expr>.*)".split()
    GRAMMAR = r"""
    S   ->   S1 | S1 lb | S1 lb S
    # S1  ->   ASSIGN | OP_ASSIGN | FOR | WHILE | IF | IF_ELSE | FUNC_CALL
    S1  ->   ASSIGN | FOR | WHILE | IF | IF_ELSE | FUNC_CALL
    # ASSIGN -> id assign expr | id assign ASSIGN
    ASSIGN -> id assign expr
    # OP_ASSIGN -> id op_assign expr
    FOR -> for id in id colon BLOCK
    WHILE -> while expr colon BLOCK
    IF -> if expr colon BLOCK
    IF_ELSE -> if expr colon BLOCK LBS else colon BLOCK
    BLOCK -> lb lbrace lb S LBS rbrace
    LBS -> lb LBS | TERMINATOR
    TERMINATOR -> 
    """


    # TODO: add function use in parser

    def __init__(self):
        self.tokenizer = SillyLexer(self.TOKENS)
        self.grammar = Grammar.from_string(self.GRAMMAR)
        self.root = None
    
    
    def __call__(self, program_text):
        def add_braces(t):
            lines = t.split('\n')
            prev_level = 0
            new_lines = []
            for line in lines:
                level = 0
                if line and line[0] == ' ':
                    level = (len(line) - len(line.lstrip(' '))) // 4
                elif line and line[1] == '\t':
                    level = (len(line) - len(line.lstrip('\t')))
                new_line = ((level-prev_level)* '{\n') + ((prev_level-level)* '}\n') + line.lstrip('\t')
                new_lines.append(new_line)
                prev_level = level
            new_lines.append(prev_level*"}")
            return "\n".join(new_lines)

        program_text = add_braces(program_text)
        tokens = list(self.tokenizer(program_text))
        # print(f"Code with added braces:\n{program_text}")
        # print(50*'-')
        # print(f"Program Tokens: {tokens}")
        earley = Parser(grammar=self.grammar, sentence=tokens, debug=False)      # TODO: change to False when not testing
        earley.parse()
        
        if earley.is_valid_sentence():
            # print("Program is valid, please ignore other prints")
            trees = ParseTrees(earley)
            print(50 * '-')
            # print(trees)
            assert(len(trees) == 1)
            self.root = trees.nodes[0]
            return self
        else:
            raise ValueError(f"SimplePyParser could not process the program {program_text}")


    def _extract_while_condition(self, t: Tree):
        if t.root == "γ":
            return self._extract_while_condition(t.subtrees[0])
        if t.root == "S":
            if len(t.subtrees) < 3:
                return self._extract_while_condition(t.subtrees[0])
            else:
                res = self._extract_while_condition(t.subtrees[0])
                return res if res != None else self._extract_while_condition(t.subtrees[2])
        if t.root == "S1":
            return self.extract_while_condition(t.subtrees[0]) if  t.subtrees[0].root == "WHILE" else None
        if t.root == "WHILE":
            return t.subtrees[1].subtrees[0].root       # TODO: check that the right value is returned
    
    
    def extract_while_condition(self):
        return self._extract_while_condition(self.root)


        
    def weakest_precond(self, postcondition, var_to_z3: dict, invariant_as_z3):
        def upd(d, k, v):
            d = d.copy()
            d[k] = v
            return d
        
        def _weakest_precond(t: Tree, Q, var_to_z3):
            if t.root == "γ":
                return self._weakest_precond(t.subtrees[0], Q, var_to_z3)
            if t.root == "S":
                if len(t.subtrees) < 3:
                    return self._weakest_precond(t.subtrees[0], Q, var_to_z3)
                else:
                    wp_inner = lambda env: self._weakest_precond(t.subtrees[2], Q, var_to_z3)(env)
                    return lambda env: self._weakest_precond(t.subtrees[0], wp_inner, var_to_z3)(env)
            if t.root == "S1":
                return self._weakest_precond(t.subtrees[0], Q, var_to_z3)
             
            # ASSIGN -> id assign expr
            if t.root == "ASSIGN":
                var = t.subtrees[0].subtrees[0].root
                expr_text = t.subtrees[2].subtrees[0].root 
                expr_as_z3 = lambda env: PyExprParser(env)(expr_text).as_z3()
                Q_sub = lambda env: Q(upd(env, var, expr_as_z3(env)))
                return Q_sub

            if t.root in ("IF", "IF_ELSE"):
                condition_text = t.subtrees[1].subtrees[0].root
                b = lambda env: PyExprParser(env)(condition_text).as_z3()
                b_neg = lambda env: Not(PyExprParser(env)(condition_text).as_z3())
                block1 = t.subtrees[3]
                block1_code = block1.subtrees[3]
                wp_inner1 = _weakest_precond(block1_code, Q, var_to_z3)
                if t.root == "IF":
                    wp_inner2 = Q
                else:
                    block2 = t.subtrees[7]
                    block2_code = block2.subtrees[3]
                    wp_inner2 = _weakest_precond(block2_code, Q, var_to_z3)
                return lambda env: Or(And(wp_inner1(env), b(env)), And(wp_inner2(env), b_neg(env)))
            
            if t.root == "WHILE":
                P = lambda env: env["linv"]
                b = lambda env: PyExprParser(env)(t.subtrees[1].subtrees[0].root).as_z3()
                b_neg = lambda env: Not(b(env))
                code = t.subtrees[3].subtrees[3]
                forall_expr = lambda env:ForAll([var_to_z3[v] for v in var_to_z3 if v != "linv"],
                                         And(Implies(And(var_to_z3['linv'](var_to_z3), b(var_to_z3)), _weakest_precond(code, var_to_z3['linv'], var_to_z3)(var_to_z3)),
                                             Implies(And(var_to_z3['linv'](var_to_z3), b_neg(var_to_z3)), Q(var_to_z3)))) 
                return lambda env: And(var_to_z3['linv'](env), forall_expr(env))
            
            raise SimplePyParserError(f"tried to extract weakest precondition from {t}")
        var_to_z3 = var_to_z3.copy()
        var_to_z3["linv"] = invariant_as_z3
        expr_parser = PyExprParser(var_to_z3)
        return _weakest_precond(self.root, postcondition, var_to_z3, expr_parser)

    @staticmethod
    def get_wp(safety_property, program_text, loop_invariant: str, var_to_z3):
        program_lines = program_text.split("\n")
        # for i, _ in enumerate(program_lines):
        #     if "while" in program_lines:
        #         break
        # program_lines = program_lines[i:]       # removing all lines that come before the loop
        program_lines = [line for line in program_lines if "import" not in line and "__inv__" not in line]
        program_text = "\n".join(program_lines)
        loop_invariant_as_z3 = lambda env: PyExprParser(env)(loop_invariant).as_z3()
        return SimplePyParser()(program_text).weakest_precond(safety_property, var_to_z3, loop_invariant_as_z3)(var_to_z3)



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


