from flask import Flask, request, jsonify
from flask_cors import CORS
from compiler.lexer import Lexer
from compiler.grammar import get_decaf_grammar
from compiler.parser_rd import RecursiveDescentParser
from compiler.parser_ll1 import LL1Parser
from compiler.parser_lr import LRParser
from compiler.semantic import SymbolTableBuilder
from compiler.error_handler import ErrorHandler

app = Flask(__name__)
CORS(app)

@app.route('/api/compile', methods=['POST'])
def compile_code():
    data = request.json
    source_code = data.get('source_code', '')

    error_handler = ErrorHandler()

    # 1. Lexical Analysis
    lexer = Lexer(source_code)
    tokens = lexer.tokenize()
    
    # 2. Grammar Setup
    grammar = get_decaf_grammar()
    grammar.compute_follow()
    grammar.build_slr_tables()
    
    # 3. Parsers
    rd_parser = RecursiveDescentParser(tokens)
    rd_result = rd_parser.parse()
    
    ll1_parser = LL1Parser(grammar, tokens)
    ll1_result = ll1_parser.parse()
    
    lr_parser = LRParser(grammar, tokens)
    lr_result = lr_parser.parse()
    
    # 4. Symbol Table Construction
    st_builder = SymbolTableBuilder(tokens)
    st = st_builder.build()
    
    return jsonify({
        "tokens": [t.to_dict() for t in tokens],
        "parsers": {
            "rd": rd_result,
            "ll1": ll1_result,
            "lr": lr_result
        },
        "grammar": {
            "first": {k: list(v) for k,v in grammar.first_sets.items()},
            "follow": {k: list(v) for k,v in grammar.follow_sets.items()}
        },
        "symbol_table": st.dump(),
        "errors": error_handler.get_all_errors()
    })

if __name__ == '__main__':
    app.run(debug=True, port=5000)
