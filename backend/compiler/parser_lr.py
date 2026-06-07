class LRParser:
    def __init__(self, grammar, tokens, error_handler=None):
        self.grammar      = grammar
        self.tokens       = tokens
        self.error_handler = error_handler
        self.action_table = grammar.action_table
        self.goto_table   = grammar.goto_table
        self.productions  = grammar.productions
        self.errors  = []
        self.trace   = []

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
        return token.type

    def _report_error(self, line, col, msg):
        self.errors.append({"line": line, "col": col, "message": msg})
        if self.error_handler:
            self.error_handler.report_syntactic_error(line, col, msg)

    def parse(self):
        state_stack  = [0]
        symbol_stack = []
        idx   = 0
        step  = 0
        MAX   = 20000

        while step < MAX:
            step += 1
            state = state_stack[-1]

            if idx < len(self.tokens):
                tok       = self.tokens[idx]
                token_sym = self.get_token_symbol(tok)
                line, col = tok.line, tok.column
            else:
                tok = None
                token_sym = "$"
                line = col = 0

            action = self.action_table.get(state, {}).get(token_sym)

            # ── Shift ─────────────────────────────────────────────────────
            if action and action.startswith("s"):
                next_state = int(action[1:])
                state_stack.append(next_state)
                symbol_stack.append(token_sym)
                idx += 1
                self.trace.append({
                    "step": step,
                    "state": state,
                    "input": token_sym,
                    "action": "shift",
                    "action_label": f"Shift  {token_sym}  → state {next_state}"
                })

            # ── Reduce ────────────────────────────────────────────────────
            elif action and action.startswith("r"):
                prod_idx  = int(action[1:])
                nt, rhs   = self.productions[prod_idx]
                pop_count = 0 if rhs == ['epsilon'] else len(rhs)
                for _ in range(pop_count):
                    state_stack.pop()
                    if symbol_stack:
                        symbol_stack.pop()

                top_state  = state_stack[-1]
                goto_state = self.goto_table.get(top_state, {}).get(nt)
                rhs_str    = " ".join(rhs) if rhs != ['epsilon'] else "ε"

                if goto_state is None:
                    msg = f"GOTO error: no entry for ({top_state}, {nt})"
                    self._report_error(line, col, msg)
                    self.trace.append({
                        "step": step, "state": state, "input": token_sym,
                        "action": "error", "action_label": f"Error  {msg}"
                    })
                    break

                state_stack.append(goto_state)
                symbol_stack.append(nt)
                self.trace.append({
                    "step": step,
                    "state": state,
                    "input": token_sym,
                    "action": "reduce",
                    "action_label": f"Reduce  {nt}  →  {rhs_str}"
                })

            # ── Accept ────────────────────────────────────────────────────
            elif action == "Accept":
                self.trace.append({
                    "step": step, "state": state, "input": token_sym,
                    "action": "accept", "action_label": "Accept — parse successful"
                })
                break

            # ── Error + panic recovery ─────────────────────────────────────
            else:
                expected = sorted(self.action_table.get(state, {}).keys())
                msg = f"Unexpected '{token_sym}' in state {state} — expected {expected}"
                self._report_error(line, col, msg)
                self.trace.append({
                    "step": step, "state": state, "input": token_sym,
                    "action": "error", "action_label": f"Error (panic recovery)"
                })

                # Pop states until we find one with a sync token action
                sync_tokens = {'PUNCT_;', 'PUNCT_}', '$'}
                recovered   = False
                while len(state_stack) > 1:
                    top = state_stack[-1]
                    for s in sync_tokens:
                        if s in self.action_table.get(top, {}):
                            while idx < len(self.tokens):
                                sym = self.get_token_symbol(self.tokens[idx])
                                if sym == s or sym == '$':
                                    recovered = True
                                    break
                                idx += 1
                            break
                    if recovered:
                        break
                    state_stack.pop()
                    if symbol_stack:
                        symbol_stack.pop()

                if not recovered:
                    break

        return {"trace": self.trace, "errors": self.errors}