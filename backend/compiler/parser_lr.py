class LRParser:
    def __init__(self, grammar, tokens):
        self.grammar = grammar
        self.tokens = tokens
        self.action_table = grammar.action_table
        self.goto_table = grammar.goto_table
        self.productions = grammar.productions
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

    def parse(self):
        stack = [0] # Stack of states
        symbol_stack = []
        idx = 0
        
        max_steps = 10000
        step = 0
        
        while step < max_steps:
            step += 1
            state = stack[-1]
            if idx < len(self.tokens):
                current_token = self.tokens[idx]
                token_sym = self.get_token_symbol(current_token)
            else:
                current_token = None
                token_sym = "$"

            self.trace.append({
                "stack": list(stack),
                "symbols": list(symbol_stack),
                "input": token_sym,
                "action": ""
            })

            if state in self.action_table and token_sym in self.action_table[state]:
                action = self.action_table[state][token_sym]
                if action.startswith("s"):
                    # Shift
                    next_state = int(action[1:])
                    stack.append(next_state)
                    symbol_stack.append(token_sym)
                    idx += 1
                    self.trace[-1]["action"] = f"Shift {next_state}"
                elif action.startswith("r"):
                    # Reduce
                    prod_idx = int(action[1:])
                    nt, rhs = self.productions[prod_idx]
                    
                    # Pop 2*|rhs| items in a real stack (if keeping states and symbols interleaved)
                    # We just keep separate stacks.
                    if rhs != ['epsilon']:
                        for _ in range(len(rhs)):
                            stack.pop()
                            if symbol_stack:
                                symbol_stack.pop()
                                
                    new_state = stack[-1]
                    if nt in self.goto_table[new_state]:
                        stack.append(self.goto_table[new_state][nt])
                        symbol_stack.append(nt)
                        self.trace[-1]["action"] = f"Reduce {nt} -> {' '.join(rhs)}"
                    else:
                        self.errors.append(f"GOTO Error: Missing transition for {nt} from state {new_state}")
                        self.trace[-1]["action"] = "Error"
                        break
                elif action == "Accept":
                    self.trace[-1]["action"] = "Accept"
                    break
            else:
                self.errors.append(f"Syntax Error at {token_sym} (line {current_token.line if current_token else 'EOF'}) in state {state}")
                self.trace[-1]["action"] = "Error"
                
                # Basic Panic Mode Recovery for LR
                # We skip tokens until we find one that is in the action table for the current state
                recovered = False
                while idx < len(self.tokens):
                    idx += 1
                    if idx < len(self.tokens):
                        next_tok = self.get_token_symbol(self.tokens[idx])
                        if next_tok in self.action_table[state]:
                            self.errors.append(f"Recovered at token {next_tok}")
                            recovered = True
                            break
                if not recovered:
                    break

        return {
            "trace": self.trace,
            "errors": self.errors
        }
