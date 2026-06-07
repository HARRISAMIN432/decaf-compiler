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

    # Single shared error handler for the whole pipeline
    error_handler = ErrorHandler()

    # ── 1. Lexical Analysis ────────────────────────────────────────────────
    lexer  = Lexer(source_code, error_handler=error_handler)
    tokens = lexer.tokenize()

    # Separate clean tokens from error tokens for display
    clean_tokens = [t for t in tokens if t.type != "ERROR"]
    error_tokens = [t for t in tokens if t.type == "ERROR"]
    for et in error_tokens:
        error_handler.report_lexical_error(et.line, et.column, et.value)

    # ── 2. Grammar setup ───────────────────────────────────────────────────
    grammar = get_decaf_grammar()
    grammar.compute_follow()
    grammar.build_slr_tables()

    # ── 3. Recursive Descent Parser ────────────────────────────────────────
    rd_parser = RecursiveDescentParser(clean_tokens, error_handler=error_handler)
    rd_result = rd_parser.parse()

    # ── 4. LL(1) Predictive Parser ─────────────────────────────────────────
    ll1_parser = LL1Parser(grammar, clean_tokens, error_handler=error_handler)
    ll1_result = ll1_parser.parse()

    # ── 5. LR (SLR) Parser ────────────────────────────────────────────────
    lr_parser = LRParser(grammar, clean_tokens, error_handler=error_handler)
    lr_result = lr_parser.parse()

    # ── 6. Symbol Table ────────────────────────────────────────────────────
    st_builder = SymbolTableBuilder(clean_tokens, error_handler=error_handler)
    st = st_builder.build()

    error_handler.print_summary()

    # ── 7. Build clean response ────────────────────────────────────────────
    return jsonify({
        # Tokens: group by type for readability
        "tokens": [t.to_dict() for t in clean_tokens],
        "token_summary": _token_summary(clean_tokens),

        # Parser results
        "parsers": {
            "rd":  rd_result,
            "ll1": {
                "trace":  ll1_result["trace"],
                "errors": ll1_result["errors"],
                # Only send table on explicit request — it's huge
                # "table": ll1_result["table"],
            },
            "lr": lr_result,
        },

        # Grammar: FIRST/FOLLOW sorted for readability
        "grammar": {
            "first":  {k: sorted(v) for k, v in grammar.first_sets.items()
                       if k in grammar.non_terminals},
            "follow": {k: sorted(v) for k, v in grammar.follow_sets.items()
                       if k in grammar.non_terminals},
        },

        # Symbol table
        "symbol_table": st.dump(),

        # All errors unified
        "errors": error_handler.get_all_errors(),
    })


def _token_summary(tokens):
    """Count tokens by category for the summary bar."""
    cats = {"keyword": 0, "identifier": 0, "operator": 0,
            "punctuation": 0, "literal": 0, "other": 0}
    for t in tokens:
        tp = t.type
        if tp.startswith("KEYWORD"):          cats["keyword"]     += 1
        elif tp == "IDENT":                   cats["identifier"]  += 1
        elif tp.startswith("OP"):             cats["operator"]    += 1
        elif tp.startswith("PUNCT"):          cats["punctuation"] += 1
        elif tp in ("INT_CONST","DOUBLE_CONST",
                    "BOOL_CONST","STRING_CONST"): cats["literal"] += 1
        elif tp != "EOF":                     cats["other"]       += 1
    return cats


if __name__ == '__main__':
    app.run(debug=True, port=5000)