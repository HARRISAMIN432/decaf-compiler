import os
import sys

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from compiler.lexer import Lexer
from compiler.grammar import get_decaf_grammar
from compiler.parser_rd import RecursiveDescentParser
from compiler.parser_ll1 import LL1Parser
from compiler.parser_lr import LRParser
from compiler.semantic import SymbolTableBuilder
from compiler.error_handler import ErrorHandler

def test_file(filepath):
    original_path = filepath
    if not os.path.exists(filepath):
        if filepath.endswith('.decaf'):
            alt_path = filepath.replace('.decaf', '.txt')
            if os.path.exists(alt_path):
                filepath = alt_path
                print(f"Using alternate file: {filepath}")
        elif filepath.endswith('.txt'):
            alt_path = filepath.replace('.txt', '.decaf')
            if os.path.exists(alt_path):
                filepath = alt_path
                print(f"Using alternate file: {filepath}")
    
    print(f"\n--- Testing {filepath} ---")
    
    if not os.path.exists(filepath):
        print(f"ERROR: File not found: {filepath}")
        print(f"Tried original: {original_path}")
        return
    
    with open(filepath, 'r') as f:
        source_code = f.read()

    error_handler = ErrorHandler()

    lexer = Lexer(source_code)
    tokens = lexer.tokenize()
    
    print(f"Tokens found: {len(tokens)}")
    for t in tokens[:5]:
        print(f"  {t}")
    if len(tokens) > 5:
        print("  ...")

    grammar = get_decaf_grammar()
    grammar.compute_follow()
    grammar.build_slr_tables()
    print("Grammar parsed, FIRST/FOLLOW computed, and SLR tables built.")
    
    rd_parser = RecursiveDescentParser(tokens)
    rd_result = rd_parser.parse()
    print(f"RD Parser Errors: {len(rd_result['errors'])}")
    
    ll1_parser = LL1Parser(grammar, tokens)
    ll1_result = ll1_parser.parse()
    print(f"LL1 Parser Trace length: {len(ll1_result['trace'])}")
    
    lr_parser = LRParser(grammar, tokens)
    lr_result = lr_parser.parse()
    print(f"LR Parser Trace length: {len(lr_result['trace'])}")
    if lr_result['errors']:
        print("LR Errors:")
        for e in lr_result['errors']:
            print("  " + e)
    else:
        print("LR Parser: SUCCESS (No errors)")
    
    st_builder = SymbolTableBuilder(tokens)
    st = st_builder.build()
            
    print(f"Symbol Table Entries: {len(st.dump())}")

if __name__ == '__main__':
    root_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    test_file_path = os.path.join(root_dir, 'test', 'test4.txt')
    print(f"Looking for file at: {test_file_path}")
    test_file(test_file_path)
    print("\nTests completed successfully without crashing!")