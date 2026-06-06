from compiler.symbol_table import SymbolTableManager

class SymbolTableBuilder:
    def __init__(self, tokens):
        self.tokens = tokens
        self.st = SymbolTableManager()
        # enter_scope() will be called internally to manage scope 1 as global
        
    def build(self):
        self.st.enter_scope() # Global scope
        
        idx = 0
        while idx < len(self.tokens):
            t = self.tokens[idx]
            
            if t.type == "PUNCT" and t.value == '{':
                self.st.enter_scope()
            elif t.type == "PUNCT" and t.value == '}':
                self.st.exit_scope()
                
            elif t.type == "KEYWORD" and t.value in ("int", "double", "bool", "string", "void", "class"):
                if t.value == "class":
                    # class IDENT
                    if idx + 1 < len(self.tokens) and self.tokens[idx+1].type == "IDENT":
                        name_token = self.tokens[idx+1]
                        self.st.insert(name_token.value, "class", "class", name_token.line)
                        idx += 1
                else:
                    var_type = t.value
                    if idx + 1 < len(self.tokens) and self.tokens[idx+1].type == "IDENT":
                        name_token = self.tokens[idx+1]
                        
                        # Lookahead to see if it's a function or variable
                        if idx + 2 < len(self.tokens) and self.tokens[idx+2].value == '(':
                            self.st.insert(name_token.value, "function", var_type, name_token.line)
                        else:
                            self.st.insert(name_token.value, "variable", var_type, name_token.line)
                        idx += 1
            
            # Handling object instantiation/references loosely as variables if not explicitly caught
            # For a proper compiler, this is done in a full AST traversal.
            elif t.type == "IDENT":
                # Check if it's a custom class type declaration like: Animal a;
                # We can peek at the next token. If next is IDENT, it's a declaration.
                if idx + 1 < len(self.tokens) and self.tokens[idx+1].type == "IDENT":
                    # Only if it's not a function call or something else.
                    # Usually, Type IDENT ;
                    next_tok = self.tokens[idx+1]
                    if idx + 2 < len(self.tokens) and self.tokens[idx+2].value in (';', ','):
                        self.st.insert(next_tok.value, "object", t.value, next_tok.line)
                        idx += 1

            idx += 1
            
        return self.st
