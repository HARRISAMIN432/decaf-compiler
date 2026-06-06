class SymbolTableEntry:
    def __init__(self, name, kind, type_, scope_level, line_number):
        self.name = name
        self.kind = kind
        self.type = type_
        self.scope_level = scope_level
        self.line_number = line_number

    def to_dict(self):
        return {
            "name": self.name,
            "kind": self.kind,
            "type": self.type,
            "scope_level": self.scope_level,
            "line_number": self.line_number
        }

class SymbolTableManager:
    def __init__(self):
        self.scope_stack = [{}] # List of hash tables (dicts)
        self.current_scope_level = 0
        self.all_entries = [] # To keep a flat record for UI display

    def enter_scope(self):
        self.current_scope_level += 1
        self.scope_stack.append({})

    def exit_scope(self):
        if self.current_scope_level > 0:
            self.scope_stack.pop()
            self.current_scope_level -= 1

    def insert(self, name, kind, type_, line_number):
        if name in self.scope_stack[-1]:
            return False, f"Error: Identifier '{name}' already declared in current scope."
        
        entry = SymbolTableEntry(name, kind, type_, self.current_scope_level, line_number)
        self.scope_stack[-1][name] = entry
        self.all_entries.append(entry)
        return True, "Inserted successfully."

    def lookup(self, name):
        # Look from innermost scope to outermost
        for scope in reversed(self.scope_stack):
            if name in scope:
                return scope[name]
        return None

    def delete(self, name):
        if name in self.scope_stack[-1]:
            del self.scope_stack[-1][name]
            return True
        return False
        
    def dump(self):
        return [entry.to_dict() for entry in self.all_entries]
