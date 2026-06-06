class LL1Parser:
    def __init__(self, grammar, tokens):
        self.grammar = grammar
        self.tokens = tokens
        self.parse_table = {}
        self.build_parse_table()
        self.errors = []
        self.trace = []

    def get_token_symbol(self, token):
        if token.type == "EOF":
            return "$"
        if token.type == "KEYWORD":
            return f"KEYWORD_{token.value}"
        if token.type == "IDENT":
            return "IDENT"
        if token.type == "OP":
            return f"OP_{token.value}"
        if token.type == "PUNCT":
            return f"PUNCT_{token.value}"
        if token.type == "INT_CONST":
            return "INT_CONST"
        if token.type == "DOUBLE_CONST":
            return "DOUBLE_CONST"
        if token.type == "BOOL_CONST":
            return "BOOL_CONST"
        if token.type == "STRING_CONST":
            return "STRING_CONST"
        return token.type

    def build_parse_table(self):
        for nt, productions in self.grammar.rules.items():
            self.parse_table[nt] = {}
            for prod in productions:
                first_of_prod = self.grammar.get_first_of_sequence(prod)
                
                for terminal in first_of_prod:
                    if terminal != 'epsilon':
                        self.parse_table[nt][terminal] = prod
                
                if 'epsilon' in first_of_prod:
                    for terminal in self.grammar.follow_sets[nt]:
                        # Favor shift over epsilon to resolve dangling-else conflict
                        if terminal not in self.parse_table[nt]:
                            self.parse_table[nt][terminal] = prod

    def parse(self):
        stack = ['$', self.grammar.start_symbol]
        idx = 0
        
        while len(stack) > 0:
            top = stack[-1]
            if idx < len(self.tokens):
                current_token = self.tokens[idx]
                token_sym = self.get_token_symbol(current_token)
            else:
                current_token = None
                token_sym = "$"

            self.trace.append({
                "stack": list(stack),
                "input": token_sym,
                "action": ""
            })

            if top == '$' and token_sym == '$':
                self.trace[-1]["action"] = "Accept"
                break
                
            if top == token_sym:
                stack.pop()
                idx += 1
                self.trace[-1]["action"] = f"Match {top}"
            elif top in self.grammar.terminals or top == '$':
                err_msg = f"Syntax Error: Expected {top}, found {token_sym} at line {current_token.line if current_token else 'EOF'}"
                self.errors.append(err_msg)
                self.trace[-1]["action"] = "Error"
                break # Basic error recovery: just break for now
            else:
                # It's a non-terminal
                if top in self.parse_table and token_sym in self.parse_table[top]:
                    prod = self.parse_table[top][token_sym]
                    stack.pop()
                    self.trace[-1]["action"] = f"Predict {top} -> {' '.join(prod)}"
                    if prod != ['epsilon']:
                        for sym in reversed(prod):
                            stack.append(sym)
                else:
                    err_msg = f"Syntax Error: Unexpected token {token_sym} at line {current_token.line if current_token else 'EOF'}. Expected one of {list(self.parse_table.get(top, {}).keys())}"
                    self.errors.append(err_msg)
                    self.trace[-1]["action"] = "Error"
                    break

        return {
            "trace": self.trace,
            "errors": self.errors,
            "table": self.parse_table
        }
