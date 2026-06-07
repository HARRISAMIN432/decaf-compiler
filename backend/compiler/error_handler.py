class ErrorHandler:
    def __init__(self):
        self.lexical_errors = []
        self.syntactic_errors = []
        self.semantic_errors = []

    def report_lexical_error(self, line, col, msg):
        entry = f"Lexical Error at line {line}, col {col}: {msg}"
        self.lexical_errors.append(entry)

    def report_syntactic_error(self, line, col, msg):
        entry = f"Syntactic Error at line {line}, col {col}: {msg}"
        self.syntactic_errors.append(entry)

    def report_semantic_error(self, line, col, msg):
        entry = f"Semantic Error at line {line}, col {col}: {msg}"
        self.semantic_errors.append(entry)

    def has_errors(self):
        return bool(self.lexical_errors or self.syntactic_errors or self.semantic_errors)

    def total_count(self):
        return len(self.lexical_errors) + len(self.syntactic_errors) + len(self.semantic_errors)

    def get_all_errors(self):
        return {
            "lexical": self.lexical_errors,
            "syntactic": self.syntactic_errors,
            "semantic": self.semantic_errors,
            "summary": f"{self.total_count()} error(s) found: "
                       f"{len(self.lexical_errors)} lexical, "
                       f"{len(self.syntactic_errors)} syntactic, "
                       f"{len(self.semantic_errors)} semantic."
        }

    def print_summary(self):
        """Print all errors to stdout — useful for CLI / demo."""
        if not self.has_errors():
            print("Compilation successful. No errors found.")
            return
        for e in self.lexical_errors:
            print(e)
        for e in self.syntactic_errors:
            print(e)
        for e in self.semantic_errors:
            print(e)
        print(f"\n=== {self.total_count()} error(s) total ===")
