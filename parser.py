import sys
sys.dont_write_bytecode = True
class Parser:
    """Turns tokens into expressions."""

    def eat(self, expected_type=None, expected_val=None):
        # 'Eats' a token by moving the position one token forward, but optionally makes sure the next token is what we actually want
        token = self.current()
        if token[0] is None:
            raise SyntaxError("Unexpected EOF")
        if expected_type and token[0] != expected_type:
            raise SyntaxError(f"Expected {expected_type}, got {token}")
        if expected_val and token[1] != expected_val:
            raise SyntaxError(f"Expected {expected_val}, got {token}")
        self.pos += 1
        return token

    def peek(self, n=1):
        # Looks at the next token without eating it
        pos = self.pos + n
        if pos >= len(self.tokens):
            return (None, None)
        return self.tokens[pos]
    
    def parse(self, tokens):
        self.tokens = tokens
        self.pos = 0
        x = self.parse_block(until=None)
        return x

    def parse_statement(self):
        _, val = self.current()
        if val == 'def':
            return self.parse_function()
        if val == 'if':
            return self.parse_if()
        if val == 'for':
            return self.parse_for()
        if val == 'while':
            return self.parse_while()
        if val == 'break':
            self.eat('KEYWORD', 'break')
            return ('break',)
        if val == 'continue':
            self.eat('KEYWORD', 'continue')
            return ('continue',)
        if val == 'return':
            self.eat('KEYWORD', 'return')
            expr = self.parse_expression() if self.current()[1] != ';' else None
            return ('return', expr)
        if val == 'global':
            self.eat('KEYWORD', 'global')
            _, name = self.eat('IDENT')
            return ('global', name)
        if val == 'try':
            return self.parse_try()
        if val == 'throw':
            self.eat('KEYWORD', 'throw')
            expr = self.parse_expression()
            return ('throw', expr)
        if val == 'class':
            return self.parse_class()
        if val == 'include':
            return self.parse_include()
        if val == 'ffi':
            return self.parse_ffi()
        if val == 'match':
            return self.parse_match()

        return self.parse_expression()
    
    def parse_block(self, until='}'):
        stmts = []
        while self.pos < len(self.tokens):
            _, val = self.current()
            if until and val == until:
                break
            stmt = self.parse_statement()
            stmts.append(stmt)

        return stmts

    def parse_function(self):
        self.eat('KEYWORD')

        if self.current()[0] != 'IDENT':
            raise SyntaxError("Expected function name")

        # Functions may be split with . to indicate methods
        name_parts = []
        while True:
            _, ident = self.eat('IDENT')
            name_parts.append(ident)
            if self.current()[1] == '.':
                self.eat('SYMBOL', '.')
            else:
                break

        name = '.'.join(name_parts)
        is_method = len(name_parts) > 1

        # Parse arguments
        self.eat('SYMBOL', '(')

        params = []
        while self.current()[1] != ')':
            # Check for optional positional and keyword arguments e.g. *args, **kwargs
            if self.current()[1] == '**':
                self.eat('OP', '**')
                _, ident = self.eat('IDENT')
                params.append(('**' + ident, None))
            elif self.current()[1] == '*':
                self.eat('OP', '*')
                _, ident = self.eat('IDENT')
                params.append(('*' + ident, None))
            else:
            # check for optional positional arguments e.g. x=1, y=2
                _, ident = self.eat('IDENT')
                default_expr = None
                if self.current()[1] == '=':
                    self.eat('OP', '=')
                    default_expr = self.parse_expression()
                params.append((ident, default_expr))

            if self.current()[1] == ',':
                self.eat('SYMBOL', ',')

        self.eat('SYMBOL', ')')

        # Find the function body
        self.eat('SYMBOL', '{')
        body = self.parse_block(until='}')
        self.eat('SYMBOL', '}')

        if is_method:
            params = ['self'] + params

        return ('def', name, params, body)
    
    def parse_if(self):
        self.eat('KEYWORD', 'if')
        self.eat('SYMBOL', '(')
        cond = self.parse_expression()
        self.eat('SYMBOL', ')')
        self.eat('SYMBOL', '{')
        then_body = self.parse_block('}')
        self.eat('SYMBOL', '}')
        branches = [('if', cond, then_body)]
        while self.current()[1] == 'elif':
            self.eat('KEYWORD', 'elif')
            self.eat('SYMBOL', '(')
            cond = self.parse_expression()
            self.eat('SYMBOL', ')')
            self.eat('SYMBOL', '{')
            body = self.parse_block('}')
            self.eat('SYMBOL', '}')
            branches.append(('elif', cond, body))
        if self.current()[1] == 'else':
            self.eat('KEYWORD', 'else')
            self.eat('SYMBOL', '{')
            else_body = self.parse_block('}')
            self.eat('SYMBOL', '}')
            branches.append(('else', None, else_body))
        return ('if_chain', branches)
    
    def parse_for(self):
        self.eat('KEYWORD', 'for')
        self.eat('SYMBOL', '(')
        _, var_name = self.eat('IDENT')
        self.eat('SYMBOL', ',')
        iterable = self.parse_expression()
        step = 1
        if self.current()[1] == ',':
            self.eat('SYMBOL', ',')
            step_expr = self.parse_expression()
            step = ('optional_step', step_expr)
        self.eat('SYMBOL', ')')
        self.eat('SYMBOL', '{')
        body = self.parse_block('}')
        self.eat('SYMBOL', '}')
        return ('for', var_name, iterable, step, body)
    
    def parse_while(self):
        self.eat('KEYWORD', 'while')
        self.eat('SYMBOL', '(')
        cond_expr = self.parse_expression()
        self.eat('SYMBOL', ')')
        self.eat('SYMBOL', '{')
        body = self.parse_block('}')
        self.eat('SYMBOL', '}')
        return ('while', cond_expr, body)
    
    def parse_expression(self, min_prec=0):
        node = self.parse_primary()

        while True:
            tok = self.current()
            # Comparison (e.g. 1 > 2)

            if tok[1] == "in":
                self.eat('KEYWORD', 'in')
                right = self.parse_expression()
                node = ('in', node, right)

            if tok[1] == "not" and self.peek()[1] == "in":
                self.eat('KEYWORD', 'not')
                self.eat('KEYWORD', 'in')
                right = self.parse_expression()
                node = ('nin', node, right)

            if tok[1] == "and":
                self.eat('KEYWORD', 'and') 
                right = self.parse_expression()
                node = ('and', node, right)
            if tok[1] == "or":
                self.eat('KEYWORD', 'or') 
                right = self.parse_expression()
                node = ('or', node, right)
            if tok[0] == 'COMPARE':
                _, op = self.eat('COMPARE')
                right = self.parse_expression()
                node = ('compare', op, node, right)
            elif tok[0] == 'OP' and tok[1] in self.bodmas:
                prec, assoc = self.bodmas[tok[1]]
                if prec < min_prec:
                    break
                self.eat('OP')
                right = self.parse_expression(prec + 1 if assoc == 'left' else prec)
                node = ('binop', tok[1], node, right)
            
            # Function calls (e.g. f(x))
            elif tok[1] == '(':  
                self.eat('SYMBOL', '(')
                args = []
                kwargs = {}
                while self.current()[1] != ')':
                    if self.current()[1] == '**':
                        self.eat('OP', '**')
                        unpack_expr = self.parse_expression()
                        args.append(('kwunpack', unpack_expr))
                    elif self.current()[1] == '*':
                        self.eat('OP', '*')
                        unpack_expr = self.parse_expression()
                        args.append(('unpack', unpack_expr))

                    elif self.current()[0] == 'IDENT' and self.peek()[1] == '=':
                        key = self.eat('IDENT')[1]
                        self.eat('OP', '=')
                        val = self.parse_expression()
                        kwargs[key] = val
                    else:
                        args.append(self.parse_expression())
                    if self.current()[1] == ',':
                        self.eat('SYMBOL', ',')
                self.eat('SYMBOL', ')')
                node = ('call', node, args, kwargs)
            
            # slices and indexes e.g. list[3:], list[0]
            elif tok[1] == '[':
                self.eat('SYMBOL', '[')
                
                start = stop = step = None
                has_colon = False

                # Check for empty slice part (e.g. [:])
                
                if self.current()[1] != ':':
                    start = self.parse_expression()
                
                if self.current()[1] == ':':
                    has_colon = True
                    self.eat('SYMBOL', ':')
                    if self.current()[1] != ':' and self.current()[1] != ']':
                        stop = self.parse_expression()
                
                if self.current()[1] == ':':
                    self.eat('SYMBOL', ':')
                    if self.current()[1] != ']':
                        step = self.parse_expression()

                self.eat('SYMBOL', ']')

                if has_colon:
                    node = ('slice', node, start, stop, step)
                else:
                    node = ('index', node, start)

            elif tok[1] == '.':
                self.eat('SYMBOL', '.')
                next_tok = self.current()
                if next_tok[0] != 'IDENT':
                    # Combine e.g. 0 . 1 into float
                    if node[0] == 'num' and next_tok[0] == 'NUMBER':
                        self.eat('NUMBER')
                        combined = float(f"{node[1]}.{next_tok[1]}")
                        node = ('num', combined)
                        continue  # Keep going until we whittle down the float expression 
                    else:
                        raise SyntaxError("Attribute access must be followed by an ident")
                _, attr = self.eat('IDENT')
                node = ('getattr', node, attr)


            # Ternary expression (e.g. x == 1 ? True : False)
            elif tok[1] == '?':
                self.eat('SYMBOL', '?')
                true_expr = self.parse_expression()
                self.eat('SYMBOL', ':')
                false_expr = self.parse_expression()
                node = ('ternary', node, true_expr, false_expr)
            else:
                break
        return node

    def parse_primary(self):
        kind, val = self.current()
        if kind == 'NUMBER':
            self.eat('NUMBER')
            return ('num', int(val))
        if kind == 'STRING':
            self.eat('STRING')
            return ('str', val)
        if kind == 'IDENT':
            name = self.eat('IDENT')[1]
            node = ('var', name)

            # Handle field access (e.g. x.a.b.c...)
            while self.current() == ('SYMBOL', '.'):
                self.eat('SYMBOL', '.')
                attr = self.eat('IDENT')[1]
                node = ('getattr', node, attr)

            while self.current() == ('SYMBOL', '['):
                self.eat('SYMBOL', '[')

                start = stop = step = None
                has_colon = False

                if self.current()[1] != ':':
                    expr = self.parse_expression()
                    if self.current()[1] != ':' and self.current()[1] != ']':
                        self.eat('SYMBOL', ']')
                        node = ('getitem', node, expr)
                        continue
                    start = expr

                if self.current()[1] == ':':
                    has_colon = True
                    self.eat('SYMBOL', ':')
                    if self.current()[1] != ':' and self.current()[1] != ']':
                        stop = self.parse_expression()

                if self.current()[1] == ':':
                    self.eat('SYMBOL', ':')
                    if self.current()[1] != ']':
                        step = self.parse_expression()

                self.eat('SYMBOL', ']')
                node = ('slice', node, start, stop, step) if has_colon else ('getitem', node, start)

            # assignment: x = y, x.a = y, x[0] = y
            if self.current()[0] == 'OP' and self.current()[1] == '=':
                self.eat('OP', '=')
                expr = self.parse_expression()
                if node[0] == 'getitem':
                    return ('setindex', node[1], node[2], expr)
                elif node[0] == 'var':
                    return ('assign', node[1], expr)
                elif node[0] == 'getattr':
                    return ('setattr', node[1], node[2], expr)
                else:
                    raise SyntaxError("Invalid assignment target")

            # augmented assignment: x += y, x.a += y, x[0] += y
            if self.current()[0] == 'AUG_ASSIGN':
                _, op = self.eat('AUG_ASSIGN')
                if op == "++":
                    expr = ('num', 1)
                    op = "+="
                elif op == "--":
                    expr = ('num', 1)
                    op = "-="
                else:
                    expr = self.parse_expression()

                if node[0] == 'var':
                    return ('augassign', node[1], op, expr)
                elif node[0] == 'getattr':
                    return ('augassignattr', node[1], node[2], op, expr)
                elif node[0] == 'getitem':
                    return ('augassignindex', node[1], node[2], op, expr) 
                else:
                    raise SyntaxError("Invalid augmented assignment target")

            return node

        if val == '{':
            self.eat('SYMBOL', '{')
            
            # Check immediate closing: empty dict
            if self.current()[1] == '}':
                self.eat('SYMBOL', '}')
                return ('dict', [])  # empty dict

            # Scan tokens to detect if it's a dict or block
            is_dict = False
            pos = self.pos
            depth = 1
            while pos < len(self.tokens) and depth > 0:
                tkind, tval = self.tokens[pos]
                if tval == '{':
                    depth += 1
                elif tval == '}':
                    depth -= 1
                elif (tval == ':' or tval == '|') and depth == 1:
                    is_dict = True
                    break
                pos += 1

            if is_dict:
                # Parse key expression first
                key_expr = self.parse_expression()

                if self.current()[1] == '|':
                    # Pipe-based dict comprehension syntax:
                    self.eat('SYMBOL', '|')
                    value_expr = self.parse_expression()

                    self.eat('SYMBOL', ',')
                    var_name = self.eat('IDENT')[1]

                    self.eat('SYMBOL', ',')
                    iterable = self.parse_expression()

                    condition = None
                    if self.current()[1] == '|':
                        self.eat('SYMBOL', '|')
                        condition = self.parse_expression()

                    self.eat('SYMBOL', '}')
                    return ('dictcomp', key_expr, value_expr, var_name, iterable, condition)

                elif self.current()[1] == ':':
                    # Regular dict key:value pairs
                    self.eat('SYMBOL', ':')
                    value_expr = self.parse_expression()

                    items = [(key_expr, value_expr)]
                    while self.current()[1] != '}':
                        if self.current()[1] == ',':
                            self.eat('SYMBOL', ',')
                        k = self.parse_expression()
                        self.eat('SYMBOL', ':')
                        v = self.parse_expression()
                        items.append((k, v))

                    self.eat('SYMBOL', '}')
                    return ('dict', items)

                else:
                    # Fallback block if no colon or pipe after key expr
                    block = self.parse_block(until='}')
                    self.eat('SYMBOL', '}')
                    return ('block', block)

            else:
                # Not a dict: parse as a block
                block = self.parse_block(until='}')
                self.eat('SYMBOL', '}')
                return ('block', block)

        if val == '[':
            self.eat('SYMBOL', '[')

            if self.current()[1] == ']':
                self.eat('SYMBOL', ']')
                return ('list', [])

            # Parse result expression
            result_expr = self.parse_expression()

            # Check for custom list comprehension syntax
            if self.current()[0] == 'SYMBOL' and self.current()[1] == '|':
                self.eat('SYMBOL', '|')

                # Parse (var, iterable, step)
                var = self.eat('IDENT')[1]
                self.eat('SYMBOL', ',')
                iterable = self.parse_expression()
                self.eat('SYMBOL', ',')
                step = self.parse_expression()

                # Optional condition
                condition = None
                if self.current()[0] == 'SYMBOL' and self.current()[1] == '|':
                    self.eat('SYMBOL', '|')
                    condition = [self.parse_expression()]
                    while self.current()[0] == 'SYMBOL' and self.current()[1] == '|':
                        self.eat('SYMBOL', '|')
                        condition.append(self.parse_expression())


                self.eat('SYMBOL', ']')
                return ('listcomp', result_expr, var, iterable, step, condition)

            # Regular list
            items = [result_expr]
            while self.current()[0] == 'SYMBOL' and self.current()[1] == ',':
                self.eat('SYMBOL', ',')
                items.append(self.parse_expression())

            self.eat('SYMBOL', ']')
            return ('list', items)


        # Match/Case
        if val == 'match':
            return self.parse_match()
            # Match/Case
        if val == 'not':
            self.eat('KEYWORD', 'not')
            if self.current()[0] == 'KEYWORD' and self.current()[1] == 'in':
                self.eat('KEYWORD', 'in')
                right = self.parse_expression()
                return ('notin', None, right)  # adjust as needed
            expr = self.parse_primary()
            return ('not', expr)

        # Negative numbers get parsed to here, just return the negative version of the next number
        if val == "-":
            self.eat('OP', '-')
            expr = self.parse_primary()
            if expr[0] == 'num':
                return ('num', -expr[1])
            return ('neg', expr)

        # Keyword arguments
        if val == "**":
            self.eat('OP', '**')
            expr = self.parse_primary()
            return ('kwunpack', expr)
    
        # Positional arguments
        if val == "*":
            self.eat('OP', '*')
            expr = self.parse_primary()
            return ('unpack', expr)
        
        # Lambda functions
        if val == 'lambda':
            self.eat('KEYWORD', 'lambda')

            self.eat('SYMBOL', '(')
            params = []
            while self.current()[1] != ')':
                if self.current()[1] == '**':
                    self.eat('OP', '**')
                    _, ident = self.eat('IDENT')
                    params.append(('**' + ident, None))
                elif self.current()[1] == '*':
                    self.eat('OP', '*')
                    _, ident = self.eat('IDENT')
                    params.append(('*' + ident, None))
                else:
                    _, ident = self.eat('IDENT')
                    default_expr = None
                    if self.current()[1] == '=':
                        self.eat('OP', '=')
                        default_expr = self.parse_expression()
                    params.append((ident, default_expr))
                if self.current()[1] == ',':
                    self.eat('SYMBOL', ',')
            self.eat('SYMBOL', ')')

            self.eat('SYMBOL', '{')
            body = self.parse_block(until='}')
            self.eat('SYMBOL', '}')

            return ('lambda', params, body)
        
        # Parentheses for BODMAS
        if val == '(':
            self.eat('SYMBOL', '(')
            expr = self.parse_expression()
            self.eat('SYMBOL', ')')
            return expr


        raise SyntaxError(f"Unexpected token {kind}: {val}")
    
    def parse_include(self):
        self.eat('IDENT', 'include')
        if self.current()[1] == '(':  #
            self.eat('SYMBOL', '(')
            expr = self.parse_expression()
            self.eat('SYMBOL', ')')
            return ('call', ('var', 'include'), [expr], {})
        else:
            kind, filename = self.eat('STRING')
            return ('include', filename)

    def parse_class(self):
        self.eat('KEYWORD', 'class')
        _, name = self.eat('IDENT')
        parents = []
        if self.current()[1] == '(':  
            self.eat('SYMBOL', '(')
            while self.current()[1] != ')':
                _, parent = self.eat('IDENT')
                parents.append(parent)
                if self.current()[1] == ',':
                    self.eat('SYMBOL', ',')
            self.eat('SYMBOL', ')')
        self.eat('SYMBOL', '{')
        fields = []
        methods = []
        nested_classes = []
        while self.current()[1] != '}':
            kind, val = self.current()
            if kind == 'KEYWORD' and val == 'def':
                method = self.parse_function()
                methods.append(method)
            elif kind == 'KEYWORD' and val == 'class':
                nested = self.parse_class()
                nested_classes.append(nested)
            elif kind == 'IDENT':
                _, fname = self.eat('IDENT')
                default_expr = None
                if self.current()[1] == '=':
                    self.eat('OP', '=')
                    default_expr = self.parse_expression()
                fields.append((fname, default_expr))
                if self.current()[1] == ';':
                    self.eat('SYMBOL', ';')
            else:
                raise SyntaxError(f"Expected field, method, or nested class in class, got {self.current()}")
        self.eat('SYMBOL', '}')
        return ('class', name, parents, fields, methods, nested_classes)

    def parse_try(self):
        self.eat('KEYWORD', 'try')
        self.eat('SYMBOL', '{')
        try_block = self.parse_block('}')
        self.eat('SYMBOL', '}')

        self.eat('KEYWORD', 'catch')
        try:
            self.eat('SYMBOL', '(')
            _, err_name = self.eat('IDENT')
            self.eat('SYMBOL', ')')
        except:
            err_name = None

        self.eat('SYMBOL', '{')
        catch_block = self.parse_block('}')
        self.eat('SYMBOL', '}')

        return ('try', err_name, try_block, catch_block)
    
    def parse_ffi(self):
        self.eat('KEYWORD', 'ffi')
        self.eat('SYMBOL', '{')
        raw_code = ''
        depth = 1
        while self.pos < len(self.tokens):
            tok = self.current()
            if tok == ('SYMBOL', '{'):
                depth += 1
            elif tok == ('SYMBOL', '}'):
                depth -= 1
                if depth == 0:
                    self.eat('SYMBOL', '}')
                    break

            if tok[0] == 'STRING':
                raw_code += repr(tok[1]) + ' '
            else:
                raw_code += tok[1] + ' '
            self.pos += 1
        return ('ffi', raw_code.strip())

    def parse_match(self):
        self.eat('KEYWORD', 'match')
        self.eat('SYMBOL', '(')
        expr = self.parse_expression()  
        self.eat('SYMBOL', ')')
        self.eat('SYMBOL', '{')

        cases = []
        while self.current()[1] != '}':
            if self.current()[1] == 'case':
                self.eat('KEYWORD', 'case')

                # Parse one or more patterns separated by '' union op
                patterns = [self.parse_expression()]
                while self.current()[1] == '|':
                    self.eat('SYMBOL', '|')
                    patterns.append(self.parse_expression())

                self.eat('SYMBOL', '{')
                body = self.parse_block('}')
                self.eat('SYMBOL', '}')

                cases.append((patterns, body))

            elif self.current()[1] == 'else':
                self.eat('KEYWORD', 'else')
                self.eat('SYMBOL', '{')
                body = self.parse_block('}')
                self.eat('SYMBOL', '}')
                cases.append((['else'], body))

            else:
                raise SyntaxError(f"Expected 'case' or 'else', got {self.current()}")

        self.eat('SYMBOL', '}')
        return ('match', expr, cases)
