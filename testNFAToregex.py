from parse import Lexer, Parser, Token, State, NFA, Handler, HandlerTree, NFATreeNode


#from regex github project
def compile(p, debug = False):
    
    def print_tokens(tokens):
        for t in tokens:
            print(t)

    lexer = Lexer(p)
    parser = Parser(lexer)
    tokens = parser.parse()

    handler = Handler()
    
    if debug:
        print_tokens(tokens) 

    nfa_stack = []
    
    for t in tokens:
        handler.handlers[t.name](t, nfa_stack)
    
    assert len(nfa_stack) == 1
    return nfa_stack.pop() 


if __name__ == "__main__":
    reg = "auc/be*/chose/dee"
    print("Expression régulière:", reg)
    print("NFA:  -----    ")
    NFA1 = compile(reg)
    NFA1.uglyprint()
    print("-------------------------")
    print("DFA:    ")
    DFA = NFA1.toDFA()
    DFA.uglyprint()
    print("Renommage: ----")
    DFA.renameStates()
    DFA.uglyprint()
    print("Decomposition:")
    decomp = DFA.decomposePaths()
    print("=========-----******************------===========")
    for k in decomp:
        s1, s2, r = decomp[k]
        print(s1.name,s2.name, r)
    