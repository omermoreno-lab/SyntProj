import prog


def ground(s):
    return not s.isupper()


def split_mid(s, delim):
    ss = s.split(delim)
    assert len(ss) == 2
    return ss[0], ss[1]


def initial_programs(rules):
    P = {}
    for rule in rules:
        non_term, term = split_mid(rule, "::=")
        if not ground(term):
            continue
        if non_term in P:
            P[non_term].append(term)
        else:
            P[non_term] = [term]
    return P


def prog_sat_examples(prog, examples):
    for example in examples:



def btm_up_enum(terms, non_terms, rules, term_init, examples):
    P = initial_programs(rules)
    while True:
        # P += grow(P, rules)
        for p in P:
            if prog_sat_examples(p, examples):
                return p


if __name__ == '__main__':
    examples = prog.generate_examples()
    pvars = {"a", "b", "x", "y", "z"}

    grammar = "LEXPR  ::=  ( VAR RELOP VAR )\n" \
              "VAR  ::=  a | b | x | y | z\n" \
              "RELOP  ::=  == | != | < | <="
