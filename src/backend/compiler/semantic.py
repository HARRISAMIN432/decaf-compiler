from compiler.symbol_table import SymbolTableManager

class SymbolTableBuilder:
    def __init__(self, tokens, error_handler=None):
        self.tokens        = tokens
        self.error_handler = error_handler
        self.st            = SymbolTableManager()

    def build(self):
        self.st.enter_scope()  

        idx = 0
        while idx < len(self.tokens):
            t = self.tokens[idx]

            if t.type == "PUNCT_{" or (t.type == "PUNCT" and t.value == "{"):
                self.st.enter_scope()
                idx += 1
                continue

            if t.type == "PUNCT_}" or (t.type == "PUNCT" and t.value == "}"):
                self.st.exit_scope()
                idx += 1
                continue

            if t.type in ("KEYWORD_class", "KEYWORD") and (
                    t.type == "KEYWORD_class" or t.value == "class"):
                if idx + 1 < len(self.tokens):
                    nt = self.tokens[idx + 1]
                    if nt.type == "IDENT":
                        ok, msg = self.st.insert(nt.value, "class", "class", nt.line)
                        if not ok:
                            self._sem_error(nt.line, nt.column, msg)
                        idx += 2
                        continue

            type_kws = {
                "KEYWORD_int", "KEYWORD_double",
                "KEYWORD_bool", "KEYWORD_string", "KEYWORD_void"
            }
            legacy_type = (t.type == "KEYWORD" and
                           t.value in ("int","double","bool","string","void"))

            if t.type in type_kws or legacy_type:
                var_type = t.value if hasattr(t, 'value') else t.type.split('_',1)[1]
                if idx + 1 < len(self.tokens):
                    nt = self.tokens[idx + 1]
                    if nt.type == "IDENT":
                        is_func = (idx + 2 < len(self.tokens) and
                                   (self.tokens[idx+2].type in ("PUNCT_(","PUNCT") and
                                    getattr(self.tokens[idx+2],'value','') == '('))
                        kind = "function" if is_func else "variable"
                        ok, msg = self.st.insert(nt.value, kind, var_type, nt.line)
                        if not ok:
                            self._sem_error(nt.line, nt.column, msg)
                        idx += 2
                        continue

            if t.type == "IDENT":
                if idx + 1 < len(self.tokens):
                    nt = self.tokens[idx + 1]
                    if nt.type == "IDENT":
                        if idx + 2 < len(self.tokens):
                            after = self.tokens[idx + 2]
                            semi  = (after.type in ("PUNCT_;","PUNCT") and
                                     getattr(after,'value','') == ';')
                            if semi:
                                ok, msg = self.st.insert(
                                    nt.value, "object", t.value, nt.line)
                                if not ok:
                                    self._sem_error(nt.line, nt.column, msg)
                                idx += 3
                                continue

            idx += 1

        return self.st

    def _sem_error(self, line, col, msg):
        if self.error_handler:
            self.error_handler.report_semantic_error(line, col, msg)
