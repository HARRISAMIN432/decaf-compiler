from collections import defaultdict

class Grammar:
    def __init__(self, rules, start_symbol):
        self.rules = rules
        self.start_symbol = start_symbol
        self.non_terminals = set(rules.keys())
        self.terminals = set()
        self._compute_terminals()
        
        self.first_sets = defaultdict(set)
        self.follow_sets = defaultdict(set)

        self.productions = []
        self.action_table = {}
        self.goto_table = {}

    def _compute_terminals(self):
        for nt, productions in self.rules.items():
            for prod in productions:
                for symbol in prod:
                    if symbol not in self.non_terminals and symbol != 'epsilon':
                        self.terminals.add(symbol)

    def compute_first(self):
        self.first_sets = {nt: set() for nt in self.non_terminals}
        for t in self.terminals:
            self.first_sets[t] = {t}
        self.first_sets['epsilon'] = {'epsilon'}

        changed = True
        while changed:
            changed = False
            for nt, productions in self.rules.items():
                for prod in productions:
                    old_len = len(self.first_sets[nt])
                    if prod[0] == 'epsilon':
                        self.first_sets[nt].add('epsilon')
                    else:
                        for symbol in prod:
                            first_of_symbol = self.first_sets.get(symbol, set())
                            self.first_sets[nt].update(first_of_symbol - {'epsilon'})
                            if 'epsilon' not in first_of_symbol:
                                break
                        else:
                            self.first_sets[nt].add('epsilon')
                    if len(self.first_sets[nt]) > old_len:
                        changed = True

    def get_first_of_sequence(self, sequence):
        res = set()
        if not sequence:
            return {'epsilon'}
        if sequence[0] == 'epsilon':
            return {'epsilon'}
            
        for symbol in sequence:
            first_of_symbol = self.first_sets.get(symbol, {symbol})
            res.update(first_of_symbol - {'epsilon'})
            if 'epsilon' not in first_of_symbol:
                break
        else:
            res.add('epsilon')
        return res

    def compute_follow(self):
        if not self.first_sets:
            self.compute_first()
            
        self.follow_sets = {nt: set() for nt in self.non_terminals}
        self.follow_sets[self.start_symbol].add('$')

        changed = True
        while changed:
            changed = False
            for nt, productions in self.rules.items():
                for prod in productions:
                    for i, symbol in enumerate(prod):
                        if symbol in self.non_terminals:
                            old_len = len(self.follow_sets[symbol])
                            rest_of_prod = prod[i+1:]
                            first_of_rest = self.get_first_of_sequence(rest_of_prod)
                            self.follow_sets[symbol].update(first_of_rest - {'epsilon'})
                            if 'epsilon' in first_of_rest or not rest_of_prod:
                                self.follow_sets[symbol].update(self.follow_sets[nt])
                            if len(self.follow_sets[symbol]) > old_len:
                                changed = True

    def build_slr_tables(self):
        aug_start = self.start_symbol + "'"
        self.productions = []
        self.productions.append((aug_start, [self.start_symbol]))
        for nt, prods in self.rules.items():
            for prod in prods:
                self.productions.append((nt, prod))

        def closure(items):
            closure_set = set(items)
            changed = True
            while changed:
                changed = False
                new_items = set()
                for prod_idx, dot_pos in closure_set:
                    nt, rhs = self.productions[prod_idx]
                    if dot_pos < len(rhs) and rhs[dot_pos] != 'epsilon':
                        B = rhs[dot_pos]
                        if B in self.non_terminals:
                            for i, (p_nt, p_rhs) in enumerate(self.productions):
                                if p_nt == B:
                                    if (i, 0) not in closure_set:
                                        new_items.add((i, 0))
                if new_items:
                    closure_set.update(new_items)
                    changed = True
            return frozenset(closure_set)

        def goto(items, X):
            goto_items = set()
            for prod_idx, dot_pos in items:
                nt, rhs = self.productions[prod_idx]
                if rhs == ['epsilon']:
                    continue
                if dot_pos < len(rhs) and rhs[dot_pos] == X:
                    goto_items.add((prod_idx, dot_pos + 1))
            return closure(goto_items)

        start_item = (0, 0)
        C = [closure({start_item})]
        transitions = {}

        changed = True
        while changed:
            changed = False
            for i, state in enumerate(C):
                symbols_after_dot = set()
                for prod_idx, dot_pos in state:
                    nt, rhs = self.productions[prod_idx]
                    if rhs != ['epsilon'] and dot_pos < len(rhs):
                        symbols_after_dot.add(rhs[dot_pos])
                for X in symbols_after_dot:
                    next_state = goto(state, X)
                    if not next_state:
                        continue
                    if next_state not in C:
                        C.append(next_state)
                        changed = True
                    j = C.index(next_state)
                    transitions[(i, X)] = j

        self.action_table = {i: {} for i in range(len(C))}
        self.goto_table = {i: {} for i in range(len(C))}

        self.compute_follow()

        for i, state in enumerate(C):
            for prod_idx, dot_pos in state:
                nt, rhs = self.productions[prod_idx]
                is_epsilon = (rhs == ['epsilon'])

                if not is_epsilon and dot_pos < len(rhs):
                    a = rhs[dot_pos]
                    if a in self.terminals:
                        j = transitions.get((i, a))
                        if j is not None:
                            self.action_table[i][a] = f"s{j}"
                else:
                    if prod_idx == 0:
                        self.action_table[i]['$'] = "Accept"
                    else:
                        for a in self.follow_sets[nt]:
                            if a in self.action_table[i] and self.action_table[i][a].startswith('s'):
                                pass # Shift-Reduce conflict: Favor Shift
                            else:
                                self.action_table[i][a] = f"r{prod_idx}"

            for A in self.non_terminals:
                j = transitions.get((i, A))
                if j is not None:
                    self.goto_table[i][A] = j

        return self.action_table, self.goto_table

def get_decaf_grammar():
    rules = {
        "Program": [["DeclList"]],
        "DeclList": [["Decl", "DeclList"], ["epsilon"]],
        "Decl": [["KEYWORD_class", "IDENT", "ClassTail"], ["VarOrFuncDecl"]],
        "ClassTail": [["KEYWORD_extends", "IDENT", "ClassBody"], ["ClassBody"]],
        "ClassBody": [["PUNCT_{", "FieldList", "PUNCT_}"]],
        "FieldList": [["Field", "FieldList"], ["epsilon"]],
        "Field": [["VarOrFuncDecl"]],
        
        "VarOrFuncDecl": [
            ["Type", "IDENT", "VarOrFuncDeclTail"],
            ["KEYWORD_void", "IDENT", "PUNCT_(", "Formals", "PUNCT_)", "StmtBlock"]
        ],
        "VarOrFuncDeclTail": [
            ["PUNCT_;"],
            ["PUNCT_(", "Formals", "PUNCT_)", "StmtBlock"]
        ],
        "Type": [["KEYWORD_int"], ["KEYWORD_double"], ["KEYWORD_bool"], ["KEYWORD_string"], ["IDENT"]],
        "Formals": [["VariableList"], ["epsilon"]],
        "VariableList": [["Type", "IDENT", "VariableListTail"]],
        "VariableListTail": [["PUNCT_,", "Type", "IDENT", "VariableListTail"], ["epsilon"]],
        
        "StmtBlock": [["PUNCT_{", "BlockItemList", "PUNCT_}"]],
        "BlockItemList": [["BlockItem", "BlockItemList"], ["epsilon"]],
        
        "BlockItem": [
            ["KEYWORD_int", "IDENT", "PUNCT_;"],
            ["KEYWORD_double", "IDENT", "PUNCT_;"],
            ["KEYWORD_bool", "IDENT", "PUNCT_;"],
            ["KEYWORD_string", "IDENT", "PUNCT_;"],
            ["IDENT", "IdentStart"],  
            ["KEYWORD_this", "IdentStartStmt", "PUNCT_;"],
            ["IfStmt"],
            ["WhileStmt"],
            ["ForStmt"],
            ["ReturnStmt"],
            ["BreakStmt"],
            ["PrintStmt"],
            ["StmtBlock"],
            ["OtherExprStart", "PUNCT_;"]
        ],
        "IdentStart": [
            ["IDENT", "PUNCT_;"], 
            ["PUNCT_.", "IDENT", "IdentExprRestMethodCall", "PUNCT_;"],
            ["PUNCT_(", "Actuals", "PUNCT_)", "IdentExprRest", "PUNCT_;"],
            ["IdentExprRest", "PUNCT_;"]
        ],
        "IdentExprRestMethodCall": [
            ["PUNCT_(", "Actuals", "PUNCT_)", "IdentExprRest"],
            ["IdentExprRest"]
        ],
        "IdentExprRest": [
            ["OP_=", "Expr"], 
            ["TermTail", "SimpleExprTail"]
        ],
        "OtherExprStart": [
            ["INT_CONST", "SimpleExprTail"],
            ["DOUBLE_CONST", "SimpleExprTail"],
            ["BOOL_CONST", "SimpleExprTail"],
            ["STRING_CONST", "SimpleExprTail"],
            ["KEYWORD_New", "PUNCT_(", "IDENT", "PUNCT_)", "SimpleExprTail"],
            ["PUNCT_(", "Expr", "PUNCT_)", "SimpleExprTail"]
        ],
        
        "IfStmt": [["KEYWORD_if", "PUNCT_(", "Expr", "PUNCT_)", "Stmt", "IfStmtTail"]],
        "IfStmtTail": [["KEYWORD_else", "Stmt"], ["epsilon"]],
        "WhileStmt": [["KEYWORD_while", "PUNCT_(", "Expr", "PUNCT_)", "Stmt"]],
        "ForStmt": [["KEYWORD_for", "PUNCT_(", "Expr", "PUNCT_;", "Expr", "PUNCT_;", "Expr", "PUNCT_)", "Stmt"]],
        "ReturnStmt": [["KEYWORD_return", "ReturnTail"]],
        "ReturnTail": [["Expr", "PUNCT_;"], ["PUNCT_;"]],
        "BreakStmt": [["KEYWORD_break", "PUNCT_;"]],
        "PrintStmt": [["KEYWORD_Print", "PUNCT_(", "ExprList", "PUNCT_)", "PUNCT_;"]],
        
        "Stmt": [
            ["IDENT", "IdentStartStmt", "PUNCT_;"],
            ["KEYWORD_this", "IdentStartStmt", "PUNCT_;"],
            ["OtherExprStart", "PUNCT_;"],
            ["IfStmt"],
            ["WhileStmt"],
            ["ForStmt"],
            ["ReturnStmt"],
            ["BreakStmt"],
            ["PrintStmt"],
            ["StmtBlock"]
        ],
        "IdentStartStmt": [
            ["PUNCT_.", "IDENT", "IdentExprRestMethodCall"],
            ["PUNCT_(", "Actuals", "PUNCT_)", "IdentExprRest"],
            ["IdentExprRest"]
        ],
        
        "ExprList": [["Expr", "ExprListTail"], ["epsilon"]],
        "ExprListTail": [["PUNCT_,", "Expr", "ExprListTail"], ["epsilon"]],
        
        "Expr": [
            ["IDENT", "IdentExprRestExpr"],
            ["KEYWORD_this", "IdentExprRestExpr"],
            ["OtherExprStart"]
        ],
        "IdentExprRestExpr": [
            ["PUNCT_.", "IDENT", "IdentExprRestMethodCall"],
            ["PUNCT_(", "Actuals", "PUNCT_)", "IdentExprRest"],
            ["IdentExprRest"]
        ],
        
        "SimpleExprTail": [
            ["OP_+", "Term", "SimpleExprTail"],
            ["OP_-", "Term", "SimpleExprTail"],
            ["OP_==", "Term", "SimpleExprTail"],
            ["OP_<", "Term", "SimpleExprTail"],
            ["OP_<=", "Term", "SimpleExprTail"],
            ["OP_>", "Term", "SimpleExprTail"],
            ["OP_>=", "Term", "SimpleExprTail"],
            ["OP_!=", "Term", "SimpleExprTail"],
            ["epsilon"]
        ],
        "Term": [
            ["Factor", "TermTail"]
        ],
        "TermTail": [
            ["OP_*", "Factor", "TermTail"],
            ["OP_/", "Factor", "TermTail"],
            ["epsilon"]
        ],
        "Factor": [
            ["IDENT", "FactorIdentSuffix"],
            ["KEYWORD_this", "FactorIdentSuffix"],
            ["INT_CONST"],
            ["DOUBLE_CONST"],
            ["BOOL_CONST"],
            ["STRING_CONST"],
            ["KEYWORD_New", "PUNCT_(", "IDENT", "PUNCT_)"],
            ["PUNCT_(", "Expr", "PUNCT_)"]
        ],
        "FactorIdentSuffix": [
            ["PUNCT_.", "IDENT", "FactorIdentSuffixCall"],
            ["PUNCT_(", "Actuals", "PUNCT_)"],
            ["epsilon"]
        ],
        "FactorIdentSuffixCall": [
            ["PUNCT_(", "Actuals", "PUNCT_)"],
            ["epsilon"]
        ],
        
        "Actuals": [
            ["ExprList"]
        ]
    }
    return Grammar(rules, "Program")
