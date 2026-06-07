"""
Recursive Descent Parser for Decaf (Lab 4).
One function per non-terminal.  The grammar is LL(1) so a single token of
lookahead is sufficient everywhere.
"""

class RecursiveDescentParser:
    def __init__(self, tokens, error_handler=None):
        self.tokens        = tokens
        self.idx           = 0
        self.error_handler = error_handler
        self.errors        = []
        self.current_token = self.tokens[0] if self.tokens else None

    # ── Token navigation ───────────────────────────────────────────────────

    def advance(self):
        self.idx += 1
        self.current_token = (self.tokens[self.idx]
                              if self.idx < len(self.tokens) else None)

    def peek_type(self):
        return self.current_token.type  if self.current_token else "EOF"

    def peek_value(self):
        return self.current_token.value if self.current_token else ""

    def is_keyword(self, kw):
        t = self.current_token
        if t is None:
            return False
        return (t.type == f"KEYWORD_{kw}" or
                (t.type == "KEYWORD" and t.value == kw))

    def is_punct(self, p):
        t = self.current_token
        if t is None:
            return False
        return (t.type == f"PUNCT_{p}" or
                (t.type == "PUNCT" and t.value == p))

    def is_op(self, op):
        t = self.current_token
        if t is None:
            return False
        return (t.type == f"OP_{op}" or
                (t.type == "OP" and t.value == op))

    def is_ident(self):
        return self.peek_type() == "IDENT"

    def is_type_kw(self):
        for kw in ("int", "double", "bool", "string"):
            if self.is_keyword(kw):
                return True
        return self.is_ident()   # named type (class name)

    # ── match: consume one token or report error ───────────────────────────

    def match(self, expected_type, expected_value=None):
        t = self.current_token
        if t is None:
            self._error("EOF", "EOF", expected_type, expected_value)
            return None
        type_ok = (t.type == expected_type or
                   t.type == expected_type.split('_', 1)[0])  # loose match
        # Exact match on full type string (e.g. KEYWORD_int)
        type_ok = (t.type == expected_type)
        val_ok  = (expected_value is None or t.value == expected_value)
        if type_ok and val_ok:
            self.advance()
            return t
        self._error(t.type, t.value, expected_type, expected_value)
        self._panic_recover()
        return None

    def match_keyword(self, kw):
        t = self.current_token
        if t and (t.type == f"KEYWORD_{kw}" or
                  (t.type == "KEYWORD" and t.value == kw)):
            self.advance()
            return t
        self._error(t.type if t else "EOF",
                    t.value if t else "",
                    f"KEYWORD_{kw}", kw)
        self._panic_recover()
        return None

    def match_punct(self, p):
        t = self.current_token
        if t and (t.type == f"PUNCT_{p}" or
                  (t.type == "PUNCT" and t.value == p)):
            self.advance()
            return t
        self._error(t.type if t else "EOF",
                    t.value if t else "",
                    f"PUNCT_{p}", p)
        self._panic_recover()
        return None

    def match_op(self, op):
        t = self.current_token
        if t and (t.type == f"OP_{op}" or
                  (t.type == "OP" and t.value == op)):
            self.advance()
            return t
        self._error(t.type if t else "EOF",
                    t.value if t else "",
                    f"OP_{op}", op)
        self._panic_recover()
        return None

    def match_ident(self):
        t = self.current_token
        if t and t.type == "IDENT":
            self.advance()
            return t
        self._error(t.type if t else "EOF",
                    t.value if t else "",
                    "IDENT", None)
        self._panic_recover()
        return None

    # ── Error reporting & panic-mode recovery ──────────────────────────────

    def _error(self, got_type, got_val, exp_type, exp_val):
        t    = self.current_token
        line = t.line   if t else "EOF"
        col  = t.column if t else 0
        exp  = f"{exp_type}" + (f" '{exp_val}'" if exp_val else "")
        msg  = f"Expected {exp}, got '{got_type}' ('{got_val}')"
        self.errors.append(f"Syntactic Error at line {line}, col {col}: {msg}")
        if self.error_handler:
            self.error_handler.report_syntactic_error(line, col, msg)

    def _panic_recover(self):
        """Skip tokens until ';' or '}' or EOF — then consume the delimiter."""
        while self.current_token:
            if (self.is_punct(';') or self.is_punct('}') or
                    self.peek_type() == "EOF"):
                self.advance()
                return
            self.advance()

    # ── Non-terminal parse functions ───────────────────────────────────────

    def parse(self):
        tree = self.parse_Program()
        return {"tree": tree, "errors": self.errors}

    # Program ::= DeclList
    def parse_Program(self):
        return {"node": "Program", "children": [self.parse_DeclList()]}

    # DeclList ::= Decl DeclList | ε
    def parse_DeclList(self):
        children = []
        while self.current_token and self.peek_type() != "EOF":
            children.append(self.parse_Decl())
        return {"node": "DeclList", "children": children}

    # Decl ::= class IDENT ClassTail | VarOrFuncDecl
    def parse_Decl(self):
        if self.is_keyword("class"):
            self.match_keyword("class")
            name = self.match_ident()
            tail = self.parse_ClassTail()
            return {"node": "Decl(class)",
                    "name": name.value if name else "?",
                    "children": [tail]}
        return {"node": "Decl", "children": [self.parse_VarOrFuncDecl()]}

    # ClassTail ::= extends IDENT ClassBody | ClassBody
    def parse_ClassTail(self):
        if self.is_keyword("extends"):
            self.match_keyword("extends")
            parent = self.match_ident()
            body   = self.parse_ClassBody()
            return {"node": "ClassTail(extends)",
                    "parent": parent.value if parent else "?",
                    "children": [body]}
        return {"node": "ClassTail", "children": [self.parse_ClassBody()]}

    # ClassBody ::= { FieldList }
    def parse_ClassBody(self):
        self.match_punct("{")
        fields = self.parse_FieldList()
        self.match_punct("}")
        return {"node": "ClassBody", "children": [fields]}

    # FieldList ::= Field FieldList | ε
    def parse_FieldList(self):
        children = []
        while self.current_token and not self.is_punct("}"):
            children.append(self.parse_Field())
        return {"node": "FieldList", "children": children}

    # Field ::= VarOrFuncDecl
    def parse_Field(self):
        return {"node": "Field", "children": [self.parse_VarOrFuncDecl()]}

    # VarOrFuncDecl ::= Type IDENT VarOrFuncDeclTail
    #                 | void IDENT ( Formals ) StmtBlock
    def parse_VarOrFuncDecl(self):
        if self.is_keyword("void"):
            self.match_keyword("void")
            name = self.match_ident()
            self.match_punct("(")
            formals = self.parse_Formals()
            self.match_punct(")")
            body = self.parse_StmtBlock()
            return {"node": "FuncDecl(void)",
                    "name": name.value if name else "?",
                    "children": [formals, body]}
        # Type IDENT …
        type_node = self.parse_Type()
        name      = self.match_ident()
        tail      = self.parse_VarOrFuncDeclTail()
        return {"node": "VarOrFuncDecl",
                "name": name.value if name else "?",
                "children": [type_node, tail]}

    # VarOrFuncDeclTail ::= ; | ( Formals ) StmtBlock
    def parse_VarOrFuncDeclTail(self):
        if self.is_punct(";"):
            self.match_punct(";")
            return {"node": "VarDeclTail"}
        self.match_punct("(")
        formals = self.parse_Formals()
        self.match_punct(")")
        body = self.parse_StmtBlock()
        return {"node": "FuncDeclTail", "children": [formals, body]}

    # Type ::= int | double | bool | string | IDENT
    def parse_Type(self):
        for kw in ("int", "double", "bool", "string"):
            if self.is_keyword(kw):
                self.match_keyword(kw)
                return {"node": f"Type({kw})"}
        if self.is_ident():
            name = self.match_ident()
            return {"node": f"Type({name.value if name else '?'})"}
        self._error(self.peek_type(), self.peek_value(), "Type", None)
        self._panic_recover()
        return {"node": "Type(?)"}

    # Formals ::= VariableList | ε
    def parse_Formals(self):
        if self.is_type_kw():
            return {"node": "Formals", "children": [self.parse_VariableList()]}
        return {"node": "Formals(ε)"}

    # VariableList ::= Type IDENT VariableListTail
    def parse_VariableList(self):
        type_node = self.parse_Type()
        name      = self.match_ident()
        tail      = self.parse_VariableListTail()
        return {"node": "VariableList",
                "name": name.value if name else "?",
                "children": [type_node, tail]}

    # VariableListTail ::= , Type IDENT VariableListTail | ε
    def parse_VariableListTail(self):
        if self.is_punct(","):
            self.match_punct(",")
            type_node = self.parse_Type()
            name      = self.match_ident()
            tail      = self.parse_VariableListTail()
            return {"node": "VariableListTail",
                    "name": name.value if name else "?",
                    "children": [type_node, tail]}
        return {"node": "VariableListTail(ε)"}

    # StmtBlock ::= { BlockItemList }
    def parse_StmtBlock(self):
        self.match_punct("{")
        items = self.parse_BlockItemList()
        self.match_punct("}")
        return {"node": "StmtBlock", "children": [items]}

    # BlockItemList ::= BlockItem BlockItemList | ε
    def parse_BlockItemList(self):
        children = []
        starters = {
            "KEYWORD_int","KEYWORD_double","KEYWORD_bool","KEYWORD_string",
            "KEYWORD_this","KEYWORD_if","KEYWORD_while","KEYWORD_for",
            "KEYWORD_return","KEYWORD_break","KEYWORD_Print",
            "INT_CONST","DOUBLE_CONST","BOOL_CONST","STRING_CONST",
            "KEYWORD_New","IDENT","PUNCT_{"
        }
        while self.current_token and self.peek_type() in starters:
            children.append(self.parse_BlockItem())
        return {"node": "BlockItemList", "children": children}

    # BlockItem — dispatches to the right statement kind
    def parse_BlockItem(self):
        t = self.current_token
        if t is None:
            return {"node": "BlockItem(EOF)"}

        if t.type in ("KEYWORD_int","KEYWORD_double",
                      "KEYWORD_bool","KEYWORD_string"):
            kw = t.value if hasattr(t,'value') else t.type.split('_',1)[1]
            self.advance()
            name = self.match_ident()
            self.match_punct(";")
            return {"node": f"VarDecl({kw})",
                    "name": name.value if name else "?"}

        if t.type == "KEYWORD_this":
            self.match_keyword("this")
            stmt = self.parse_IdentStartStmt()
            self.match_punct(";")
            return {"node": "ThisStmt", "children": [stmt]}

        if t.type == "IDENT":
            name = self.match_ident()
            start = self.parse_IdentStart()
            return {"node": "IdentStmt",
                    "name": name.value if name else "?",
                    "children": [start]}

        if t.type == "KEYWORD_if":     return self.parse_IfStmt()
        if t.type == "KEYWORD_while":  return self.parse_WhileStmt()
        if t.type == "KEYWORD_for":    return self.parse_ForStmt()
        if t.type == "KEYWORD_return": return self.parse_ReturnStmt()
        if t.type == "KEYWORD_break":  return self.parse_BreakStmt()
        if t.type == "KEYWORD_Print":  return self.parse_PrintStmt()
        if t.type == "PUNCT_{":        return self.parse_StmtBlock()

        # Fallback: expression statement
        expr = self.parse_OtherExprStart()
        self.match_punct(";")
        return {"node": "ExprStmt", "children": [expr]}

    # IdentStart — after seeing IDENT in a block item
    def parse_IdentStart(self):
        # IDENT ;  (variable declaration of named type)
        if self.is_ident():
            name = self.match_ident()
            self.match_punct(";")
            return {"node": "NamedTypeDecl", "name": name.value if name else "?"}
        # . IDENT …
        if self.is_punct("."):
            self.match_punct(".")
            field = self.match_ident()
            rest  = self.parse_IdentExprRestMethodCall()
            self.match_punct(";")
            return {"node": "FieldAccess",
                    "field": field.value if field else "?",
                    "children": [rest]}
        # ( Actuals ) …
        if self.is_punct("("):
            self.match_punct("(")
            actuals = self.parse_Actuals()
            self.match_punct(")")
            rest = self.parse_IdentExprRest()
            self.match_punct(";")
            return {"node": "FuncCall", "children": [actuals, rest]}
        # IdentExprRest ;
        rest = self.parse_IdentExprRest()
        self.match_punct(";")
        return {"node": "IdentRest", "children": [rest]}

    # IdentStartStmt — after 'this' or IDENT inside a Stmt
    def parse_IdentStartStmt(self):
        if self.is_punct("."):
            self.match_punct(".")
            field = self.match_ident()
            rest  = self.parse_IdentExprRestMethodCall()
            return {"node": "FieldAccess",
                    "field": field.value if field else "?",
                    "children": [rest]}
        if self.is_punct("("):
            self.match_punct("(")
            actuals = self.parse_Actuals()
            self.match_punct(")")
            rest = self.parse_IdentExprRest()
            return {"node": "FuncCall", "children": [actuals, rest]}
        return {"node": "IdentRest", "children": [self.parse_IdentExprRest()]}

    # IdentExprRestMethodCall
    def parse_IdentExprRestMethodCall(self):
        if self.is_punct("("):
            self.match_punct("(")
            actuals = self.parse_Actuals()
            self.match_punct(")")
            rest = self.parse_IdentExprRest()
            return {"node": "MethodCall", "children": [actuals, rest]}
        return {"node": "IdentExprRest", "children": [self.parse_IdentExprRest()]}

    # IdentExprRest ::= = Expr | TermTail SimpleExprTail
    def parse_IdentExprRest(self):
        if self.is_op("="):
            self.match_op("=")
            expr = self.parse_Expr()
            return {"node": "Assign", "children": [expr]}
        tail1 = self.parse_TermTail()
        tail2 = self.parse_SimpleExprTail()
        return {"node": "IdentExprRest", "children": [tail1, tail2]}

    # ── Statements ─────────────────────────────────────────────────────────

    def parse_IfStmt(self):
        self.match_keyword("if")
        self.match_punct("(")
        cond = self.parse_Expr()
        self.match_punct(")")
        then = self.parse_Stmt()
        if self.is_keyword("else"):
            self.match_keyword("else")
            else_ = self.parse_Stmt()
            return {"node": "IfStmt", "children": [cond, then, else_]}
        return {"node": "IfStmt", "children": [cond, then]}

    def parse_WhileStmt(self):
        self.match_keyword("while")
        self.match_punct("(")
        cond = self.parse_Expr()
        self.match_punct(")")
        body = self.parse_Stmt()
        return {"node": "WhileStmt", "children": [cond, body]}

    def parse_ForStmt(self):
        self.match_keyword("for")
        self.match_punct("(")
        init = self.parse_Expr()
        self.match_punct(";")
        cond = self.parse_Expr()
        self.match_punct(";")
        step = self.parse_Expr()
        self.match_punct(")")
        body = self.parse_Stmt()
        return {"node": "ForStmt", "children": [init, cond, step, body]}

    def parse_ReturnStmt(self):
        self.match_keyword("return")
        if self.is_punct(";"):
            self.match_punct(";")
            return {"node": "ReturnStmt(void)"}
        expr = self.parse_Expr()
        self.match_punct(";")
        return {"node": "ReturnStmt", "children": [expr]}

    def parse_BreakStmt(self):
        self.match_keyword("break")
        self.match_punct(";")
        return {"node": "BreakStmt"}

    def parse_PrintStmt(self):
        self.match_keyword("Print")
        self.match_punct("(")
        exprs = self.parse_ExprList()
        self.match_punct(")")
        self.match_punct(";")
        return {"node": "PrintStmt", "children": [exprs]}

    # Stmt — used inside if/while/for bodies
    def parse_Stmt(self):
        t = self.current_token
        if t is None:
            return {"node": "Stmt(EOF)"}
        if t.type == "KEYWORD_if":     return self.parse_IfStmt()
        if t.type == "KEYWORD_while":  return self.parse_WhileStmt()
        if t.type == "KEYWORD_for":    return self.parse_ForStmt()
        if t.type == "KEYWORD_return": return self.parse_ReturnStmt()
        if t.type == "KEYWORD_break":  return self.parse_BreakStmt()
        if t.type == "KEYWORD_Print":  return self.parse_PrintStmt()
        if t.type == "PUNCT_{":        return self.parse_StmtBlock()
        if t.type == "KEYWORD_this":
            self.match_keyword("this")
            stmt = self.parse_IdentStartStmt()
            self.match_punct(";")
            return {"node": "ThisStmt", "children": [stmt]}
        if t.type == "IDENT":
            name  = self.match_ident()
            start = self.parse_IdentStartStmt()
            self.match_punct(";")
            return {"node": "IdentStmt",
                    "name": name.value if name else "?",
                    "children": [start]}
        expr = self.parse_OtherExprStart()
        self.match_punct(";")
        return {"node": "ExprStmt", "children": [expr]}

    # ── Expressions ────────────────────────────────────────────────────────

    def parse_Expr(self):
        t = self.current_token
        if t and t.type == "IDENT":
            name = self.match_ident()
            rest = self.parse_IdentExprRestExpr()
            return {"node": "Expr(ident)",
                    "name": name.value if name else "?",
                    "children": [rest]}
        if t and t.type == "KEYWORD_this":
            self.match_keyword("this")
            rest = self.parse_IdentExprRestExpr()
            return {"node": "Expr(this)", "children": [rest]}
        return {"node": "Expr", "children": [self.parse_OtherExprStart()]}

    def parse_IdentExprRestExpr(self):
        if self.is_punct("."):
            self.match_punct(".")
            field = self.match_ident()
            rest  = self.parse_IdentExprRestMethodCall()
            return {"node": "FieldExpr",
                    "field": field.value if field else "?",
                    "children": [rest]}
        if self.is_punct("("):
            self.match_punct("(")
            actuals = self.parse_Actuals()
            self.match_punct(")")
            rest = self.parse_IdentExprRest()
            return {"node": "CallExpr", "children": [actuals, rest]}
        return {"node": "IdentExprRest", "children": [self.parse_IdentExprRest()]}

    def parse_OtherExprStart(self):
        t = self.current_token
        if t and t.type == "INT_CONST":
            self.advance(); tail = self.parse_SimpleExprTail()
            return {"node": f"IntConst({t.value})", "children": [tail]}
        if t and t.type == "DOUBLE_CONST":
            self.advance(); tail = self.parse_SimpleExprTail()
            return {"node": f"DoubleConst({t.value})", "children": [tail]}
        if t and t.type == "BOOL_CONST":
            self.advance(); tail = self.parse_SimpleExprTail()
            return {"node": f"BoolConst({t.value})", "children": [tail]}
        if t and t.type == "STRING_CONST":
            self.advance(); tail = self.parse_SimpleExprTail()
            return {"node": f"StringConst", "children": [tail]}
        if t and t.type == "KEYWORD_New":
            self.match_keyword("New")
            self.match_punct("(")
            name = self.match_ident()
            self.match_punct(")")
            tail = self.parse_SimpleExprTail()
            return {"node": f"New({name.value if name else '?'})", "children": [tail]}
        if t and t.type == "PUNCT_(":
            self.match_punct("(")
            expr = self.parse_Expr()
            self.match_punct(")")
            tail = self.parse_SimpleExprTail()
            return {"node": "ParenExpr", "children": [expr, tail]}
        self._error(self.peek_type(), self.peek_value(), "Expr", None)
        self._panic_recover()
        return {"node": "Expr(?)"}

    def parse_SimpleExprTail(self):
        ops = ("OP_+","OP_-","OP_==","OP_<","OP_<=","OP_>","OP_>=","OP_!=")
        t = self.current_token
        if t and t.type in ops:
            op = t.type
            self.advance()
            term = self.parse_Term()
            tail = self.parse_SimpleExprTail()
            return {"node": f"BinOp({op})", "children": [term, tail]}
        return {"node": "SimpleExprTail(ε)"}

    def parse_Term(self):
        factor = self.parse_Factor()
        tail   = self.parse_TermTail()
        return {"node": "Term", "children": [factor, tail]}

    def parse_TermTail(self):
        ops = ("OP_*","OP_/","OP_%")
        t = self.current_token
        if t and t.type in ops:
            op = t.type
            self.advance()
            factor = self.parse_Factor()
            tail   = self.parse_TermTail()
            return {"node": f"MulOp({op})", "children": [factor, tail]}
        return {"node": "TermTail(ε)"}

    def parse_Factor(self):
        t = self.current_token
        if t and t.type == "IDENT":
            name   = self.match_ident()
            suffix = self.parse_FactorIdentSuffix()
            return {"node": f"Factor({name.value if name else '?'})",
                    "children": [suffix]}
        if t and t.type == "KEYWORD_this":
            self.match_keyword("this")
            suffix = self.parse_FactorIdentSuffix()
            return {"node": "Factor(this)", "children": [suffix]}
        for const_type in ("INT_CONST","DOUBLE_CONST","BOOL_CONST","STRING_CONST"):
            if t and t.type == const_type:
                self.advance()
                return {"node": f"Factor({t.value})"}
        if t and t.type == "KEYWORD_New":
            self.match_keyword("New")
            self.match_punct("(")
            name = self.match_ident()
            self.match_punct(")")
            return {"node": f"New({name.value if name else '?'})"}
        if t and t.type == "PUNCT_(":
            self.match_punct("(")
            expr = self.parse_Expr()
            self.match_punct(")")
            return {"node": "ParenFactor", "children": [expr]}
        self._error(self.peek_type(), self.peek_value(), "Factor", None)
        self._panic_recover()
        return {"node": "Factor(?)"}

    def parse_FactorIdentSuffix(self):
        if self.is_punct("."):
            self.match_punct(".")
            field = self.match_ident()
            call  = self.parse_FactorIdentSuffixCall()
            return {"node": "FieldSuffix",
                    "field": field.value if field else "?",
                    "children": [call]}
        if self.is_punct("("):
            self.match_punct("(")
            actuals = self.parse_Actuals()
            self.match_punct(")")
            return {"node": "CallSuffix", "children": [actuals]}
        return {"node": "FactorSuffix(ε)"}

    def parse_FactorIdentSuffixCall(self):
        if self.is_punct("("):
            self.match_punct("(")
            actuals = self.parse_Actuals()
            self.match_punct(")")
            return {"node": "MethodCallSuffix", "children": [actuals]}
        return {"node": "FactorIdentSuffixCall(ε)"}

    def parse_ExprList(self):
        expr_starters = {
            "IDENT","KEYWORD_this","INT_CONST","DOUBLE_CONST",
            "BOOL_CONST","STRING_CONST","KEYWORD_New","PUNCT_("
        }
        if self.current_token and self.peek_type() in expr_starters:
            expr = self.parse_Expr()
            tail = self.parse_ExprListTail()
            return {"node": "ExprList", "children": [expr, tail]}
        return {"node": "ExprList(ε)"}

    def parse_ExprListTail(self):
        if self.is_punct(","):
            self.match_punct(",")
            expr = self.parse_Expr()
            tail = self.parse_ExprListTail()
            return {"node": "ExprListTail", "children": [expr, tail]}
        return {"node": "ExprListTail(ε)"}

    def parse_Actuals(self):
        return {"node": "Actuals", "children": [self.parse_ExprList()]}
