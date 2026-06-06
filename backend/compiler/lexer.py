import string

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
    def __init__(self, source_code):
        # We simulate double buffering here
        self.source_code = source_code
        self.buffer_size = 4096
        self.idx = 0
        self.length = len(source_code)
        
        self.buffer1 = [''] * self.buffer_size
        self.buffer2 = [''] * self.buffer_size
        self.current_buffer = 1
        self.ptr = 0
        self.eof_reached = False
        
        self.line = 1
        self.column = 1
        
        self.load_buffer(self.buffer1)
        self.current_char = self.get_char_at_ptr()

    def load_buffer(self, buffer):
        for i in range(self.buffer_size):
            if self.idx < self.length:
                buffer[i] = self.source_code[self.idx]
                self.idx += 1
            else:
                buffer[i] = '\0'

    def get_char_at_ptr(self):
        if self.current_buffer == 1:
            return self.buffer1[self.ptr]
        else:
            return self.buffer2[self.ptr]

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
        # Peek the next character without advancing
        temp_ptr = self.ptr + 1
        if temp_ptr < self.buffer_size:
            return self.buffer1[temp_ptr] if self.current_buffer == 1 else self.buffer2[temp_ptr]
        else:
            # Need to peek into the other buffer, but if it hasn't been loaded, it's tricky.
            # For simplicity, if we are at the edge, peek from source code if available.
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
        elif self.current_char == '/' and self.peek() == '*':
            self.advance()
            self.advance()
            while not (self.current_char == '*' and self.peek() == '/') and self.current_char != '\0':
                self.advance()
            if self.current_char == '*':
                self.advance() # skip *
                self.advance() # skip /
            return True
        return False

    def get_next_token(self):
        while self.current_char != '\0':
            if self.current_char.isspace():
                self.skip_whitespace()
                continue
                
            if self.current_char == '/':
                if self.peek() == '/' or self.peek() == '*':
                    self.skip_comment()
                    continue
            
            start_line = self.line
            start_col = self.column

            if self.current_char.isalpha() or self.current_char == '_':
                ident = ""
                while self.current_char.isalnum() or self.current_char == '_':
                    ident += self.current_char
                    self.advance()
                
                # Check keywords and boolean constants
                if ident in KEYWORDS:
                    return Token("KEYWORD", ident, start_line, start_col)
                elif ident == "true" or ident == "false":
                    return Token("BOOL_CONST", ident, start_line, start_col)
                else:
                    return Token("IDENT", ident[:31], start_line, start_col) # max 31 chars

            if self.current_char.isdigit() or (self.current_char == '.' and self.peek().isdigit()):
                num_str = ""
                is_hex = False
                is_double = False
                if self.current_char == '0' and self.peek() in ('x', 'X'):
                    num_str += self.current_char
                    self.advance()
                    num_str += self.current_char
                    self.advance()
                    is_hex = True
                    while self.current_char.isalnum(): # allow any alnum for hex, will validate later
                        num_str += self.current_char
                        self.advance()
                    return Token("HEX_CONST", num_str, start_line, start_col)

                while self.current_char.isdigit():
                    num_str += self.current_char
                    self.advance()

                if self.current_char == '.':
                    is_double = True
                    num_str += self.current_char
                    self.advance()
                    while self.current_char.isdigit():
                        num_str += self.current_char
                        self.advance()
                
                if self.current_char in ('e', 'E'):
                    is_double = True
                    num_str += self.current_char
                    self.advance()
                    if self.current_char in ('+', '-'):
                        num_str += self.current_char
                        self.advance()
                    while self.current_char.isdigit():
                        num_str += self.current_char
                        self.advance()

                if is_double:
                    return Token("DOUBLE_CONST", num_str, start_line, start_col)
                else:
                    return Token("INT_CONST", num_str, start_line, start_col)

            if self.current_char == '"':
                string_val = ""
                self.advance() # skip opening quote
                while self.current_char != '"' and self.current_char != '\n' and self.current_char != '\0':
                    string_val += self.current_char
                    self.advance()
                
                if self.current_char == '"':
                    self.advance() # skip closing quote
                    return Token("STRING_CONST", string_val, start_line, start_col)
                else:
                    return Token("ERROR", "Unterminated string", start_line, start_col)

            # Operators and punctuation
            c = self.current_char
            p = self.peek()
            two_char_ops = ['<=', '>=', '==', '!=', '&&', '||']
            single_char_ops = ['+', '-', '*', '/', '%', '<', '>', '=', '!']
            
            if c + p in two_char_ops:
                op = c + p
                self.advance()
                self.advance()
                return Token("OP", op, start_line, start_col)
            elif c in single_char_ops:
                self.advance()
                return Token("OP", c, start_line, start_col)
            elif c in "\\;,.[]{}()":
                self.advance()
                return Token("PUNCT", c, start_line, start_col)
            
            # Unrecognized character
            err_char = self.current_char
            self.advance()
            return Token("ERROR", f"Unrecognized character: {err_char}", start_line, start_col)

        return Token("EOF", "", self.line, self.column)

    def tokenize(self):
        tokens = []
        while True:
            token = self.get_next_token()
            tokens.append(token)
            if token.type == "EOF":
                break
        return tokens
