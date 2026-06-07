class LL1Parser:
    def __init__(self, grammar, tokens, error_handler=None):
        self.grammar = grammar
        self.tokens = tokens
        self.error_handler = error_handler
        self.parse_table = {}
        self.errors = []
        self.trace = []
        self.build_parse_table()

    def get_token_symbol(self, token):
        if token.type == "EOF":           return "$"
        if token.type == "KEYWORD":       return f"KEYWORD_{token.value}"
        if token.type == "IDENT":         return "IDENT"
        if token.type == "OP":            return f"OP_{token.value}"
        if token.type == "PUNCT":         return f"PUNCT_{token.value}"
        if token.type == "INT_CONST":     return "INT_CONST"
        if token.type == "DOUBLE_CONST":  return "DOUBLE_CONST"
        if token.type == "BOOL_CONST":    return "BOOL_CONST"
        if token.type == "STRING_CONST":  return "STRING_CONST"
        # Already-prefixed tokens from the fixed lexer
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
                        if terminal not in self.parse_table[nt]:
                            self.parse_table[nt][terminal] = prod

    def _report_error(self, line, col, msg):
        self.errors.append({"line": line, "col": col, "message": msg})
        if self.error_handler:
            self.error_handler.report_syntactic_error(line, col, msg)

    def parse(self):
        stack = ['$', self.grammar.start_symbol]
        idx   = 0
        step  = 0

        while stack:
            step += 1
            top = stack[-1]

            if idx < len(self.tokens):
                current_token = self.tokens[idx]
                token_sym     = self.get_token_symbol(current_token)
                line          = current_token.line
                col           = current_token.column
            else:
                current_token = None
                token_sym     = "$"
                line = col    = 0

            # ── Accept ────────────────────────────────────────────────────
            if top == '$' and token_sym == '$':
                self.trace.append({
                    "step": step,
                    "stack_top": top,
                    "input": token_sym,
                    "action": "accept",
                    "action_label": "Accept — parse successful"
                })
                break

            # ── Terminal match ─────────────────────────────────────────────
            if top == token_sym:
                self.trace.append({
                    "step": step,
                    "stack_top": top,
                    "input": token_sym,
                    "action": "match",
                    "action_label": f"Match  {top}"
                })
                stack.pop()
                idx += 1
                continue

            # ── Terminal mismatch ──────────────────────────────────────────
            if top not in self.grammar.non_terminals:
                msg = f"Expected '{top}', got '{token_sym}'"
                self._report_error(line, col, msg)
                self.trace.append({
                    "step": step,
                    "stack_top": top,
                    "input": token_sym,
                    "action": "error",
                    "action_label": f"Error  {msg}"
                })
                stack.pop()   # discard unmatched terminal
                idx += 1      # skip bad token
                continue

            # ── Non-terminal: look up table ────────────────────────────────
            prod = self.parse_table.get(top, {}).get(token_sym)

            if prod is not None:
                rhs_str = " ".join(prod) if prod != ['epsilon'] else "ε"
                self.trace.append({
                    "step": step,
                    "stack_top": top,
                    "input": token_sym,
                    "action": "predict",
                    "action_label": f"Predict  {top}  →  {rhs_str}"
                })
                stack.pop()
                if prod != ['epsilon']:
                    for sym in reversed(prod):
                        stack.append(sym)
            else:
                # ── Panic-mode recovery ────────────────────────────────────
                expected = sorted(self.parse_table.get(top, {}).keys())
                msg = f"Unexpected '{token_sym}' — expected one of {expected}"
                self._report_error(line, col, msg)
                self.trace.append({
                    "step": step,
                    "stack_top": top,
                    "input": token_sym,
                    "action": "error",
                    "action_label": f"Error (panic)  {msg}"
                })
                follow = self.grammar.follow_sets.get(top, set())
                if token_sym in follow or token_sym == '$':
                    stack.pop()
                else:
                    idx += 1

        return {
            "trace": self.trace,
            "errors": self.errors,
            # Serialise table: prod lists → strings for readability
            "table": {
                nt: {t: " ".join(p) if p != ['epsilon'] else "ε"
                     for t, p in row.items()}
                for nt, row in self.parse_table.items()
            }
        }