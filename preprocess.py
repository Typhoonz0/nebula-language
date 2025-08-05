import re, sys 
sys.dont_write_bytecode = True

class Tokenizer:
    """Splits the source code into tokens using regular expressions."""
    def tokenize(self, code):
        # Immediately get rid of comments
        code = re.sub(r'//.*', '', code)
        code = re.sub(r'/\*.*?\*/', '', code, flags=re.DOTALL)
        token_spec = [
            (r'\+\+|\+=|-=|\*=|/=|%=', 'AUG_ASSIGN'),
            (r'==|!=|<=|>=|<|>', 'COMPARE'),
            (r'\*\*|\+|-|\*|/|%|=', 'OP'),
            (r'"[^"]*"|\'[^\']*\'', 'STRING'),
            (r'::\s*<[^>]+>', 'TYPEANN'),
            (r'\d+', 'NUMBER'),
            (r'\b\bin\b|def\b|\bif\b|\belse\b|\belif\b|\bor\b|\band\b|\bnot\b|\bfor\b|\bwhile\b|\bbreak\b|\bcontinue\b|\breturn\b|\bglobal\b|\btry\b|\bcatch\b|\bthrow\b|\bclass\b|\bffi\b|\bmatch\b|\bcase\b|\blambda\b', 'KEYWORD'),
            (r'[A-Za-z_]\w*', 'IDENT'),
            (r'[;\|?:{}\[\](),.]', 'SYMBOL'),
            (r'\s+', None),
        ]
        
        # Group each token into its name and value using pipe delim 
        tok_regex = '|'.join(f'(?P<{name}>{regex})' for regex, name in token_spec if name)
        # Turn these into (key, value) tuples
        tokens = [(m.lastgroup, m.group().strip("'").strip('"')) for m in re.finditer(tok_regex, code)]
        # Remove type annotations and return the result

        return [t for t in tokens if t[0] != 'TYPEANN']


    