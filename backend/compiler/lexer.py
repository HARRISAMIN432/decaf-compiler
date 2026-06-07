KEYWORDS = {
    "void", "int", "double", "bool", "string", "class", "interface", "null", "this",
    "extends", "implements", "for", "while", "if", "else", "return", "break", "New",
    "NewArray", "Print", "ReadInteger", "ReadLine"
}

class Token:
    def __init__(self, type, value, line, column):
        self.type = type
        self.value = value
        self.line = line
        self.column = column

    def __repr__(self):
        return f"({self.type}, '{self.value}')"

    def to_dict(self):
        return {
            "type": self.type,
            "value": self.value,
            "line": self.line,
            "column": self.column
        }


class Lexer:
    def __init__(self, source_code, error_handler=None):
        self.source_code = source_code
        self.buffer_size = 4096
        self.idx = 0
        self.length = len(source_code)

        self.buffer1 = [''] * self.buffer_size
        self.buffer2 = [''] * self.buffer_size
        self.current_buffer = 1
        self.ptr = 0

        self.line = 1
        self.column = 1

        # ── NEW: wire up the shared error handler ──────────────────────────
        self.error_handler = error_handler

        self.load_buffer(self.buffer1)
        self.current_char = self.get_char_at_ptr()

    # ── Buffer helpers (unchanged) ─────────────────────────────────────────

    def load_buffer(self, buffer):
        for i in range(self.buffer_size):
            if self.idx < self.length:
                buffer[i] = self.source_code[self.idx]
                self.idx += 1
            else:
                buffer[i] = '\0'

    def get_char_at_ptr(self):
        return self.buffer1[self.ptr] if self.current_buffer == 1 else self.buffer2[self.ptr]

    def advance(self):
        char = self.current_char
        if char == '\n':
            self.line += 1
            self.column = 1
        elif char != '\0':
            self.column += 1

        self.ptr += 1
        if self.ptr >= self.buffer_size:
            if self.current_buffer == 1:
                self.load_buffer(self.buffer2)
                self.current_buffer = 2
            else:
                self.load_buffer(self.buffer1)
                self.current_buffer = 1
            self.ptr = 0

        self.current_char = self.get_char_at_ptr()

    def peek(self):
        temp_ptr = self.ptr + 1
        if temp_ptr < self.buffer_size:
            return self.buffer1[temp_ptr] if self.current_buffer == 1 else self.buffer2[temp_ptr]
        if self.idx < self.length:
            return self.source_code[self.idx]
        return '\0'

    def skip_whitespace(self):
        while self.current_char in (' ', '\t', '\n', '\r'):
            self.advance()

    def skip_comment(self):
        if self.current_char == '/' and self.peek() == '/':
            while self.current_char != '\n' and self.current_char != '\0':
                self.advance()
            return True
        if self.current_char == '/' and self.peek() == '*':
            self.advance()
            self.advance()
            while not (self.current_char == '*' and self.peek() == '/') and self.current_char != '\0':
                self.advance()
            if self.current_char == '*':
                self.advance()
                self.advance()
            return True
        return False

    # ── Main scanner ───────────────────────────────────────────────────────

    def get_next_token(self):
        while self.current_char != '\0':
            if self.current_char.isspace():
                self.skip_whitespace()
                continue

            if self.current_char == '/' and self.peek() in ('/', '*'):
                self.skip_comment()
                continue

            start_line = self.line
            start_col  = self.column

            # ── Identifiers / keywords ─────────────────────────────────────
            if self.current_char.isalpha() or self.current_char == '_':
                ident = ""
                while self.current_char.isalnum() or self.current_char == '_':
                    ident += self.current_char
                    self.advance()
                if ident in KEYWORDS:
                    return Token(f"KEYWORD_{ident}", ident, start_line, start_col)
                if ident in ("true", "false"):
                    return Token("BOOL_CONST", ident, start_line, start_col)
                return Token("IDENT", ident[:31], start_line, start_col)

            # ── Numbers ────────────────────────────────────────────────────
            if self.current_char.isdigit():
                num_str = ""
                # Hex
                if self.current_char == '0' and self.peek() in ('x', 'X'):
                    num_str += self.current_char; self.advance()
                    num_str += self.current_char; self.advance()
                    while self.current_char.isalnum():
                        num_str += self.current_char; self.advance()
                    return Token("INT_CONST", num_str, start_line, start_col)

                while self.current_char.isdigit():
                    num_str += self.current_char; self.advance()

                is_double = False
                if self.current_char == '.':
                    is_double = True
                    num_str += self.current_char; self.advance()
                    while self.current_char.isdigit():
                        num_str += self.current_char; self.advance()

                if self.current_char in ('e', 'E'):
                    is_double = True
                    num_str += self.current_char; self.advance()
                    if self.current_char in ('+', '-'):
                        num_str += self.current_char; self.advance()
                    while self.current_char.isdigit():
                        num_str += self.current_char; self.advance()

                return Token("DOUBLE_CONST" if is_double else "INT_CONST",
                             num_str, start_line, start_col)

            # ── String literals ────────────────────────────────────────────
            if self.current_char == '"':
                string_val = ""
                self.advance()
                while self.current_char not in ('"', '\n', '\0'):
                    string_val += self.current_char; self.advance()
                if self.current_char == '"':
                    self.advance()
                    return Token("STRING_CONST", string_val, start_line, start_col)
                # Unterminated string → lexical error, skip & continue
                msg = f"Unterminated string literal"
                if self.error_handler:
                    self.error_handler.report_lexical_error(start_line, start_col, msg)
                # don't return an ERROR token; just keep scanning
                continue

            # ── Operators ──────────────────────────────────────────────────
            c = self.current_char
            p = self.peek()
            two_char = ['<=', '>=', '==', '!=', '&&', '||']
            single    = ['+', '-', '*', '/', '%', '<', '>', '=', '!']

            if c + p in two_char:
                op = c + p; self.advance(); self.advance()
                return Token(f"OP_{op}", op, start_line, start_col)
            if c in single:
                self.advance()
                return Token(f"OP_{c}", c, start_line, start_col)
            if c in r'\;,.[]{}()':
                self.advance()
                return Token(f"PUNCT_{c}", c, start_line, start_col)

            # ── Unrecognised character → lexical error, SKIP, continue ─────
            self.advance()
            msg = f"Unrecognized character: '{c}'"
            if self.error_handler:
                self.error_handler.report_lexical_error(start_line, start_col, msg)
            # Do NOT emit an ERROR token — just keep scanning so the parser
            # never sees it and doesn't need error recovery for lexical junk.

        return Token("EOF", "", self.line, self.column)

    def tokenize(self):
        tokens = []
        while True:
            tok = self.get_next_token()
            tokens.append(tok)
            if tok.type == "EOF":
                break
        return tokens
