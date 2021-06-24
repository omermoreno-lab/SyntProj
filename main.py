if __name__ == '__main__':
    # generate examples
    f_prog = open("prog.py", "r")
    prog = f_prog.read()
    exec(prog)

    grammar = "LEXPR  ::=  ( VAR RELOP VAR )\n" \
              "VAR  ::=  a | b | x | y | z\n" \
              "RELOP  ::=  == | != | < | <="
