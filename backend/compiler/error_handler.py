class ErrorHandler:
    def __init__(self):
        self.lexical_errors = []
        self.syntactic_errors = []
        self.semantic_errors = []

    def report_lexical_error(self, line, col, msg):
        self.lexical_errors.append(f"Lexical Error at line {line}, col {col}: {msg}")

    def report_syntactic_error(self, line, col, msg):
        self.syntactic_errors.append(f"Syntactic Error at line {line}, col {col}: {msg}")

    def report_semantic_error(self, line, col, msg):
        self.semantic_errors.append(f"Semantic Error at line {line}, col {col}: {msg}")

    def has_errors(self):
        return len(self.lexical_errors) > 0 or len(self.syntactic_errors) > 0 or len(self.semantic_errors) > 0

    def get_all_errors(self):
        return {
            "lexical": self.lexical_errors,
            "syntactic": self.syntactic_errors,
            "semantic": self.semantic_errors
        }
