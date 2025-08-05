"""
the nebula programming language
"""
PATH = ["tests", "lib", "examples"]
VERSION = 1.0
import sys, os
sys.dont_write_bytecode = True
import re
import operator
from preprocess import Tokenizer
from parser import Parser 

"""Since Python Exceptions are classes it makes since to do the same here."""
class BreakSignal(Exception): pass
class ContinueSignal(Exception): pass
class ReturnSignal(Exception): 
    def __init__(self, value): self.value = value


class Typecast:
    """Provides a set of builtin typecasting functions to our language."""
    def integer(arg): return int(arg[0])
    def float(arg): return float(arg[0])
    def string(arg): return str(arg[0])
    def list(arg): return list(arg[0])
    def dict(arg): return dict(arg[0])

class Builtins:
    """Provides a set of builtin functions to our language."""
    def type(args):
        return type(args[0]).__name__
    
    def print(args):
        # repr() prints the proper way since it may expand lists [1, 2, 3] into 1 2 3 when we don't want that
        print(*[repr(a) for a in args])

    def printf(args):
        # we only use codecs here so it makes sense for readability
        import codecs
        # printf takes a seperator and an end char
        values, sep, end = args[:-2], ' ', '\n'
        if len(args) >= 2:
            sep, end = args[-2], args[-1]
        elif len(args) == 1:
            end = args[-1]
            
            values = []
        def fmt(v):
            if isinstance(v, str):
                return v
            else:
                return repr(v)
        end = codecs.decode(end, 'unicode_escape')
        print(sep.join(fmt(v) for v in values), end=end)

    def input(args):
        # Check if a prompt was provided
        if not args:
            inp = input()
        else:
            inp = input(*args)
        # If a single . was given, most likely a floating point
        if re.match(r'^-?\d+(?:\.\d+)$', inp):
            try:
                return float(inp)
            except:
                try:
                    return int(inp)
                except:
                    return inp
        return inp
    def range(args):
        # Since range() isn't a data type we return a list
        if len(args) == 1:
            return list(range(args[0]))
        elif len(args) == 2:
            return list(range(args[0], args[1]))
        elif len(args) == 3:
            return list(range(args[0], args[1], args[2]))
        else:
            raise Exception("range expects 1 to 3 arguments")
        
    def open(args):
        # Opens a new file object inside our language
        if len(args) == 1:
            f = open(args[0], 'r')
        elif len(args) == 2:
            f = open(args[0], args[1])
        else:
            raise TypeError("open expects 1 or 2 arguments")
        return {'__type__': '__file__', '__file__': f}

    def map(args, interpreter):
        fn, iterable = args
        return [fn([x], interpreter) for x in iterable]

    def filter(args, interpreter):
        fn, iterable = args
        return [x for x in iterable if fn([x], interpreter)]

    def reduce(args, interpreter):
        from functools import reduce
        if len(args) == 3:
            fn, iterable, initializer = args
            return reduce(lambda a, b: fn([a, b], interpreter), iterable, initializer)
        elif len(args) == 2:
            fn, iterable = args
            return reduce(lambda a, b: fn([a, b], interpreter), iterable)
        else:
            raise Exception("reduce expects 2 or 3 arguments")
    
class Function:
    """Creates a function object to execute, but since our language isn't native Python, overwrite __call__ dunder to execute."""
    def __init__(self, params, body, scope):
        self.params = params
        self.body = body
        self.scope = scope

    def __call__(self, args, interpreter):
        local_scope = self.scope.copy()

        pos_target = None       # For *args
        kw_target = None      # For **kwargs

        # Detect if the last parameter is *args or **kwargs
        fixed_params = []
        for param in self.params:
            if isinstance(param, str):
                name, default_expr = param, None
            else:
                name, default_expr = param
            # Get rid of ** and * as we know what the variable is now
            if name.startswith("**"):
                kw_target = name[2:]
            elif name.startswith("*") and not name.startswith("**"):
                pos_target = name[1:]
            else:
                fixed_params.append((name, default_expr))

        # Assign positional arguments to a single fixed param
        for i, (name, default_expr) in enumerate(fixed_params):
            if i < len(str(args)):
                local_scope[name] = args[i]
            elif default_expr is not None:
                local_scope[name] = interpreter.execute(default_expr, local_scope)
            else:
                raise TypeError(f"Missing required argument '{name}'")

        # Remaining args after fixed params
        remaining = args[len(fixed_params):]

        # Assign *args (if present)
        if pos_target:
            local_scope[pos_target] = remaining
            remaining = []

        # Assign **kwargs (if present)
        if kw_target:
            # Expect a single dictionary argument for **kwargs
            if remaining:
                # If there are leftover positional args, they must form a dict
                if len(remaining) == 1 and isinstance(remaining[0], dict):
                    local_scope[kw_target] = remaining[0]
                else:
                    raise TypeError(f"Invalid arguments for ^{kw_target}, expected a single dict")
            else:
                local_scope[kw_target] = {}
            remaining = []

        # Error if too many arguments exist
        if remaining:
            raise TypeError(f"Too many arguments provided")

        return interpreter.execute_block(self.body, local_scope)

class Interpreter(Tokenizer, Parser):
    """Main interpreter class."""

    def __init__(self):
        """Even though this isn't an object orinted language, class methods still apply here."""
        self.classs = {}
        self.string_methods = {
            'reverse': lambda s: s[::-1],
            'upper': lambda s: s.upper(),
            'lower': lambda s: s.lower(),
            'join': lambda self, iterable: self.join([str(x) for x in iterable]),
            'split': lambda s, delim=' ': s.split(delim),
            'strip': lambda s: s.strip()
        }

        self.list_methods = {
            'append': lambda l, i: l.append(i),
            'extend': lambda l, i: l.extend(i),
            'remove': lambda l, i: l.remove(i),
            'sort': lambda l, i=False: l.sort(reverse = i),
            'reverse': lambda l: l.reverse(),
            'pop': lambda l: l.pop(),
            'index': lambda l, i: l.index(i),
        }

        self.file_methods = {
            'read': lambda f: f.read(),
            'write': lambda f, data: f.write(data),
            'close': lambda f: f.close(),
            'readlines': lambda f: f.readlines(),
            'readline': lambda f: f.readline(),
        }

        self.global_scope = {
            'print': lambda args, _: Builtins.print(args),
            'printf': lambda args, _: Builtins.printf(args),
            'range': lambda args, _: Builtins.range(args),
            'input': lambda args, _: Builtins.input(args),
            'type': lambda args, _: Builtins.type(args),
            'int': lambda args, _: Typecast.integer(args),
            'float': lambda args, _: Typecast.float(args),
            'str': lambda args, _: Typecast.string(args),
            'list': lambda args, _: Typecast.list(args),
            'dict': lambda args, _: Typecast.dict(args),
            'length': lambda args, _: len(args[0]),
            'open': lambda args, _: Builtins.open(args),
            'map': lambda args, interpreter: Builtins.map(args, interpreter),
            'filter': lambda args, interpreter: Builtins.filter(args, interpreter),
            'reduce': lambda args, interpreter: Builtins.reduce(args, interpreter),
            'chr': lambda args, _: chr(args[0]),
            'ord': lambda args, _: ord(args[0]),
            'include': self.include_module,
            'True': True,
            'False': False,
            'None': None,
            '__argc': len(sys.argv),
            '__argv': sys.argv
        }

        self.bodmas = {
            '+': (10, 'left'),
            '-': (10, 'left'),
            '*': (20, 'left'),
            '/': (20, 'left'),
            '%': (20, 'left'),
        }

    def run(self, code):
        """Entrypoint"""
        tokens = self.tokenize(code)
        ast = self.parse(tokens)
        return self.execute_block(ast, self.global_scope)
            
    def current(self):
        """Returns the current token position."""
        return self.tokens[self.pos] if self.pos < len(self.tokens) else (None, None)

    def execute_block(self, stmts, scope):
        """Executes a specific block."""
        result = None
        for stmt in stmts:
            # We want to first capture includes before anything else is executed so it doesn't throw errors on things that do exist.
            if isinstance(stmt, tuple) and stmt[0] == 'include':
                self.execute(stmt, scope)
                continue
            result = self.execute(stmt, scope)

            # Capture the return result for the REPL.
            if type(result) == tuple and result[0] == "return":
                return result[1]
        return result

    def execute(self, node, scope):
     #   print(node)
        """Executes just a node (token within tokens)."""
        kind = node[0]
        if kind == 'include':
            _, filename = node
            current_file_dir = os.path.dirname(sys.argv[1])
            
            # Try resolving the import relative to current file 
            included_path = os.path.normpath(os.path.join(current_file_dir, filename))

            # If not found there, try the filename as is 
            if not os.path.exists(included_path):
                included_path = os.path.normpath(filename) 
            
            try:
                with open(included_path, 'r') as f:
                    code = f.read()
            except FileNotFoundError:
                raise Exception(f"Included file '{filename}' not found (tried '{included_path}')")

            tokens = self.tokenize(code)
            ast = self.parse(tokens)
            self.execute_block(ast, scope)
            return None
        
        if kind == 'in':
            left = self.execute(node[1], scope)
            right = self.execute(node[2], scope)
            return left in right
        

        if kind == 'and':
            left, right = node[1], node[2]
            left_val = self.execute(left, scope)
            if not left_val:
                return False
            return self.execute(right, scope)

        if kind == 'or':
            left, right = node[1], node[2]
            left_val = self.execute(left, scope)
            if left_val:
                return True
            return self.execute(right, scope)

        if kind == 'not':
            val = self.execute(node[1], scope)
            return not val

        if kind == 'ternary':
            _, cond, true_expr, false_expr = node
            cond_val = self.execute(cond, scope)
           
            if cond_val:
                return self.execute(true_expr, scope)
            else:
                return self.execute(false_expr, scope)

        if kind == 'global':
            name = node[1]
            if name not in self.global_scope:
                self.global_scope[name] = None
            scope[name] = self.global_scope[name]
            return None
        
        if kind == 'num':
            return node[1]
        
        if kind == 'str':
            return node[1]
                
        if kind == 'list':
            items = node[1] or []
            return [self.execute(item, scope) for item in items]

        if kind == 'dict':
            items = node[1] or {}
            return {self.execute(key, scope): self.execute(val, scope) for key, val in items}

        if kind == 'var':
            name = node[1]
            if name in scope:
                return scope[name]
            raise NameError(f"Undefined variable {name}")
                
        if kind == 'assign':
            _, name, expr = node

            # Handle keyword unpack
            if isinstance(expr, tuple) and expr[0] == 'kwunpack':
                val = self.execute(expr[1], scope)
                if not isinstance(val, dict):
                    raise TypeError("Right-hand side of ** must evaluate to a dict")
                scope[name] = ('kwunpack', val)
                return scope[name]

            val = self.execute(expr, scope)

            # If val is None, try to guess if expr should be empty list/dict and assign accordingly
            if val is None:
                # Check if expr is a list node or dict node
                if isinstance(expr, tuple):
                    if expr[0] == 'list':
                        val = []
                    elif expr[0] == 'dict':
                        val = {}

            scope[name] = val
            return val
        
        # augmented assignment e.g. a += 1, p.x += 1, a[0] += 1
        if kind in ('augassign', 'augassignattr', 'augassignindex'):
            ops = {
                '+=': operator.add, 
                '-=': operator.sub,
                '*=': operator.mul,
                '/=': operator.truediv,
                '%=': operator.mod
            }
            if kind == 'augassign':
                _, name, op, expr = node
                if name not in scope: raise NameError(f"{name} not defined")
                scope[name] = ops[op](scope[name], self.execute(expr, scope)); return scope[name]
            
            if kind == 'augassignattr':
                _, obj_expr, attr, op, val_expr = node
                obj = self.execute(obj_expr, scope)
                if not isinstance(obj, dict): raise TypeError(f"Cannot set attribute '{attr}' on non-class object {obj}")
                obj[attr] = ops[op](obj.get(attr), self.execute(val_expr, scope)); return obj[attr]
            
            if kind == 'augassignindex':
                _, arr_expr, idx_expr, op, val_expr = node
                arr = self.execute(arr_expr, scope); idx = self.execute(idx_expr, scope)
                arr[idx] = ops[op](arr[idx], self.execute(val_expr, scope)); return None

        if kind == 'binop':
            _, op, a, b = node
            return {
                '+': operator.add, 
                '-': operator.sub, 
                '*': operator.mul, 
                '/': operator.truediv, 
                '%': operator.mod
                }[op](self.execute(a, scope), self.execute(b, scope))

        if kind == 'setindex':
            _, obj_expr, idx_expr, val_expr = node
            obj = self.execute(obj_expr, scope); idx = self.execute(idx_expr, scope); val = self.execute(val_expr, scope)
            if isinstance(obj, (list, dict)): obj[idx] = val; return val
            raise TypeError(f"Cannot index-assign to non-list/dict object: {obj}")

        if kind == 'compare':
            _, op, a, b = node
            a_val = self.execute(a, scope)
            b_val = self.execute(b, scope)

            if op in ('==', '!='):
                return {
                    '==': a_val == b_val,
                    '!=': a_val != b_val,
                }[op]

            # For ordering operators, allow only if both are numbers or both are strings
            if (isinstance(a_val, (int, float)) and isinstance(b_val, (int, float))) or \
            (isinstance(a_val, str) and isinstance(b_val, str)):
                return {
                    '<': a_val < b_val,
                    '>': a_val > b_val,
                    '<=': a_val <= b_val,
                    '>=': a_val >= b_val
                }[op]
            else:
                raise TypeError(f"Cannot compare with operator '{op}' between {type(a_val)} and {type(b_val)}")

        if kind == 'def':
            _, name, params, body = node
            func = Function(params, body, scope)
            # If we're defining a method:
            if '.' in name:
                class_name, method_name = name.split('.', 1)
                if class_name not in self.classs:
                    self.classs[class_name] = {
                        'fields': [],
                        '__methods__': {}
                    }
                # If we're defining a nested method:
                elif isinstance(self.classs[class_name], list):
                    self.classs[class_name] = {
                        'fields': self.classs[class_name],
                        '__methods__': {}
                    }
                self.classs[class_name]['__methods__'][method_name] = func
            else:
                scope[name] = func
            return None
        
        if kind == 'call':
            # Do we have keyword arguments?
            if len(node) == 3:
                func_expr, args = node[1], node[2]
                kwargs = {}
            else:
                func_expr, args, kwargs = node[1], node[2], node[3]

            func = self.execute(func_expr, scope)

            # Evaluate and unpack positional arguments (*args)
            eval_args = []
            eval_kwargs = {}
            for arg in args:
                if isinstance(arg, tuple):
                    if arg[0] == 'unpack':
                        unpacked = self.execute(arg[1], scope)
                        if not isinstance(unpacked, (list, tuple)):
                            raise TypeError("Can only unpack lists or tuples with *")
                        eval_args.extend(unpacked)

                    elif arg[0] == 'kwunpack':
                        unpacked = self.execute(arg[1], scope)
                        if isinstance(unpacked, tuple) and unpacked[0] == 'kwunpack':
                            unpacked = unpacked[1]
                        if not isinstance(unpacked, dict):
                            raise TypeError("Can only keyword-unpack dicts with ^")
                        eval_kwargs.update(unpacked)
                    else:
                        eval_args.append(self.execute(arg, scope))
                else:
                    # unwrap variables that hold kwunpack
                    val = self.execute(arg, scope)
                    if isinstance(val, tuple) and val[0] == 'kwunpack':
                        eval_kwargs.update(val[1])
                    else:
                        eval_args.append(val)

            # Evaluate and unpack keyword arguments (**kwargs)
            for k, v in kwargs.items():
                if k == 'kwunpack' or k.startswith('**'):
                    unpacked = self.execute(v, scope)
                    if not isinstance(unpacked, dict):
                        raise TypeError('Can only keyword-unpack dicts')
                    eval_kwargs.update(unpacked)
                else:
                    eval_kwargs[k] = self.execute(v, scope)

            final_args = []

            if hasattr(func, 'params'):
                remaining_args = eval_args[:]
                has_varargs = False
                has_kwargs = False

                # Check for *args or **kwargs in function parameters
                for param_name, _ in func.params:
                    if param_name.startswith('**'):
                        has_kwargs = True
                    if param_name.startswith('*'):
                        has_varargs = True

                if has_varargs or has_kwargs:
                    # Normal positional & keyword binding first
                    for param_name, default_expr in func.params:
                        if param_name.startswith('**'):
                            # Collect all remaining keyword args
                            final_args.append(eval_kwargs)
                            eval_kwargs = {}
                        elif param_name.startswith('*'):
                            # Collect all remaining positional args
                            final_args.append(remaining_args)
                            remaining_args = []

                        elif remaining_args:
                            final_args.append(remaining_args.pop(0))
                        elif param_name in eval_kwargs:
                            final_args.append(eval_kwargs.pop(param_name))
                        elif default_expr is not None:
                            final_args.append(self.execute(default_expr, scope))
                        else:
                            raise TypeError(f"Missing required argument '{param_name}'")
                else:
                    # No * or ** special parameters
                    for param_name, default_expr in func.params:
                        if param_name in eval_kwargs:
                            final_args.append(eval_kwargs.pop(param_name))
                        elif remaining_args:
                            final_args.append(remaining_args.pop(0))
                        elif default_expr is not None:
                            final_args.append(self.execute(default_expr, scope))
                        else:
                            raise TypeError(f"Missing required argument '{param_name}'")

                if eval_kwargs:
                    unexpected_keys = ', '.join(eval_kwargs.keys())
                    raise TypeError(f"Unexpected keyword arguments: {unexpected_keys}")
            else:
                final_args = eval_args + list(eval_kwargs.values())

            if callable(func):
                return func(final_args, self)

            # If the function is a class method:
            elif isinstance(func_expr, tuple) and func_expr[0] == 'var':
                typename = func_expr[1]
                if typename in self.classs:
                    fields = self.classs[typename]
                    if len(fields) != len(eval_args):
                        raise TypeError(f"{typename} expects {len(fields)} fields, got {len(eval_args)}")
                    return {'__type__': typename, **dict(zip(fields, eval_args))}

            # If the function is the pointer to another:
            elif isinstance(func, Function):
                # func.params is a list of (name, default_expr_or_None)
                params = func.params

                local_scope = {}

                # Assign positional args first
                for i, (param_name, default_expr) in enumerate(params):
                    if i < len(eval_args):
                        local_scope[param_name] = eval_args[i]
                    elif param_name in eval_kwargs:
                        local_scope[param_name] = eval_kwargs.pop(param_name)
                    elif default_expr is not None:
                        local_scope[param_name] = self.execute(default_expr, scope)
                    else:
                        raise RuntimeError(f"Missing required argument '{param_name}'")

                if eval_kwargs:
                    unexpected_keys = ', '.join(eval_kwargs.keys())
                    raise RuntimeError(f"Unexpected keyword arguments: {unexpected_keys}")

                # Execute function body with local scope
                return self.execute_block(func.body, local_scope)

            else:
                raise RuntimeError(f"Attempted to call non-callable: {func}")
        
        # retrive the attribute of a class instance
        if kind == 'getattr':
            obj = self.execute(node[1], scope)
            attr = self.execute(node[2], scope) if isinstance(node[2], tuple) else node[2]

            # class method resolution (user-defined)
            def find_in_class_chain(class_type, attr):
                checked = set()
                def search(cls):
                    if cls in checked or cls not in self.classs:
                        return None
                    checked.add(cls)
                    class_info = self.classs[cls]
                    methods = class_info.get('__methods__', {})
                    method_key_options = [attr, f'{cls}.{attr}', f'self.{attr}']
                    for method_key in method_key_options:
                        if method_key in methods:
                            return methods[method_key]
                    # Check for field (fix: check field names, not tuples)
                    if any(field_name == attr for field_name, _ in class_info.get('fields', [])):
                        return 'field'
                    # Search parents
                    for parent in class_info.get('parents', []):
                        found = search(parent)
                        if found:
                            return found
                    return None
                return search(class_type)
            
            if isinstance(obj, dict) and '__type__' in obj:
                class_type = obj['__type__']
                found = find_in_class_chain(class_type, attr)

                if callable(found):
                    def bound_method(args, interpreter):
                        return found([obj] + args, interpreter)
                    return bound_method
                
                if found == 'field':
                    return obj.get(attr, None)
                
                # List available fields and methods for better error
                available = list(obj.keys())
                # Add all methods from class chain

                def collect_methods(cls, acc):
                    if cls not in self.classs:
                        return
                    class_info = self.classs[cls]
                    acc.update(class_info.get('__methods__', {}).keys())
                    for parent in class_info.get('parents', []):
                        collect_methods(parent, acc)

                method_set = set()
                collect_methods(class_type, method_set)
                available += list(method_set)
                if class_type == '__file__':
                    file_obj = obj['__file__']
                    if attr in self.file_methods:
                        return lambda args, interpreter: self.file_methods[attr](file_obj, *args)

                raise AttributeError(f"Object of type '{class_type}' has no attribute '{attr}'. Available: {available}")

            # Built-in string method resolution
            if isinstance(obj, str) and attr in self.string_methods:
                def bound_str_method(args, _):
                    return self.string_methods[attr](obj, *args)
                return bound_str_method
            
            # Built-in list method resolution
            if isinstance(obj, list) and attr in self.list_methods:
                def bound_str_method(args, _):
                    return self.list_methods[attr](obj, *args)
                return bound_str_method
            
            # File method resolution
            if isinstance(obj, dict) and obj.get('__type__') == '__file__':
                if attr in self.file_methods:
                    def bound_file_method(args, _):
                        return self.file_methods[attr](obj['__file__'], *args)
                    return bound_file_method

            # Native attribute access for dicts or objects
            try:
                return obj[attr]
            except (TypeError, KeyError):
                raise AttributeError(f"Object has no attribute '{attr}'")
        elif kind == 'setattr':
            _, obj_expr, attr_expr, value_expr = node
            obj = self.execute(obj_expr, scope)
            attr = self.execute(attr_expr, scope) if isinstance(attr_expr, tuple) else attr_expr
            value = self.execute(value_expr, scope)

            if obj is None:
                raise RuntimeError(f"Attempted to assign to index {attr} on null object: {obj_expr}")

            if not isinstance(obj, dict) and not isinstance(obj, list):
                raise TypeError(f"Cannot set attribute '{attr}' on non-class object {obj}")

            obj[attr] = value
            return value

        if kind == 'index':
            # Returns an index of a slice.
            _, list_expr, index_expr = node
            lst = self.execute(list_expr, scope)
            idx = self.execute(index_expr, scope)
            if not isinstance(lst, (list, str, dict)):
                raise TypeError("Indexing only supported on lists and strings")
            return lst[idx]
        
        if kind == 'slice':
            _, list_expr, start_expr, stop_expr, step_expr = node
            lst = self.execute(list_expr, scope)
            if not isinstance(lst, (list, str)):
                raise TypeError("Slicing only supported on lists and strings")

            start = self.execute(start_expr, scope) if start_expr else None
            stop = self.execute(stop_expr, scope) if stop_expr else None
            step = self.execute(step_expr, scope) if step_expr else None
            return lst[start:stop:step]

        if kind == 'block':
            return self.execute_block(node[1], scope)
        
        if kind == 'if_chain':
            for branch in node[1]:
                tag, cond, body = branch
                if tag == 'if' or tag == 'elif':
                    if self.execute(cond, scope):
                        return self.execute_block(body, scope)
                elif tag == 'else':
                    return self.execute_block(body, scope)
            return None
        
        if kind == 'for':
            _, var_name, iterable_expr, step_info, body = node
            iterable = self.execute(iterable_expr, scope)
            if isinstance(step_info, tuple) and step_info[0] == 'optional_step':
                step = self.execute(step_info[1], scope)
            else:
                step = 1

            if not isinstance(iterable, list):
                raise TypeError("Expected list for 'for' loop iterable")
            
            for i in range(0, len(iterable), step):
                local = scope
                local[var_name] = iterable[i]
                try:
                    self.execute_block(body, local)
                except ContinueSignal:
                    continue
                except BreakSignal:
                    break
            
            return None

        if kind == 'while':
            _, cond_expr, body = node
            try:
                while self.execute(cond_expr, scope):
                    try:
                        self.execute_block(body, scope)
                    except ContinueSignal:
                        continue
                    except BreakSignal:
                        break
            except ReturnSignal as r:
                return r.value
            return None
        
        if kind == 'break':
            raise BreakSignal()
        
        if kind == 'continue':
            raise ContinueSignal()
        
        if kind == 'return':
            val = self.execute(node[1], scope) if node[1] else None
            return ("return", val)
        
        # Try/Catch/Throw blocks
        if kind == 'try':
            _, err_name, try_block, catch_block = node
            try:
                return self.execute_block(try_block, scope)
            except Exception as e:
                new_scope = scope
                new_scope[err_name] = str(e)
                return self.execute_block(catch_block, new_scope)

        if kind == 'throw':
            _, expr = node
            value = self.execute(expr, scope)
            raise Exception(value)
        
        # class initialization
        if kind == 'class':
            # Support for nested classes
            _, name, parents, fields, methods, nested_classes = node if len(node) == 6 else (*node, [])
            def register_class(name, parents, fields, methods, nested_classes, parent_qual=None):
                qual_name = f"{parent_qual}.{name}" if parent_qual else name
                self.classs[qual_name] = {
                    'fields': fields,
                    'parents': [f"{parent_qual}.{p}" if parent_qual and p in [nc[1] for nc in nested_classes] else p for p in parents],
                    '__methods__': {}
                }
                # Attach methods to class
                for method in methods:
                    _, mname, mparams, mbody = method
                    self.classs[qual_name]['__methods__'][mname] = Function(mparams, mbody, self.global_scope)
                # Recursively register nested classes
                for nested in nested_classes:
                    n_name, n_parents, n_fields, n_methods, n_nested = nested[1], nested[2], nested[3], nested[4], nested[5] if len(nested) == 6 else []
                    register_class(n_name, n_parents, n_fields, n_methods, n_nested, qual_name)
            register_class(name, parents, fields, methods, nested_classes)
            nested_map = self._build_nested_map(name, nested_classes)
            def conclassor(args, _):
                instance = {'__type__': name}
                for i, (field_name, default_expr) in enumerate(fields):
                    if i < len(args):
                        instance[field_name] = args[i]
                    elif default_expr is not None:
                        val = self.execute_with_nested_map(default_expr, self.global_scope, nested_map)
                        instance[field_name] = val
                    else:
                        instance[field_name] = None
                return instance
            self.global_scope[name] = conclassor
            return None

        # Foriegn Function Interface (FFI)
        if kind == 'ffi':
            _, code = node
            exec_env = {}

            # We overwritten these functions in the global scope above, so it doesn't know what to do
            # We temporarily give the functions back to Python since we're executing Python
            exec_env.update({
                'print': lambda *args: print(*args),
                'range': range,
                'input': input,
                'int': int,
                'float': float,
                'str': str,
                'list': list,
                'dict': dict,
                'chr': chr,
                'ord': ord,
                'map': map,
                'filter': filter
            })

            # Inject vars outside of the FFI block
            for key, val in scope.items():
                if not callable(val):
                    exec_env[key] = val

            c = code.split(";")
            for i in c:
                exec(i.lstrip(), {}, exec_env)

            # Pull any new variables back into interpreter scope
            for k, v in exec_env.items():
                if not callable(v):  # avoid overwriting builtins
                    scope[k] = v

            return None
        
        # Match/Case blocks
        if kind == 'match':
            _, match_expr, cases = node
            val = self.execute(match_expr, scope)

            for patterns, body in cases:
                # If this case is the default "else" case
                if len(patterns) == 1 and patterns[0] == 'else':
                    # Default case matches if no previous patterns matched
                    return self.execute_block(body, scope)

                # Otherwise, check if any pattern matches the value
                for pattern in patterns:
                    pattern_val = self.execute(pattern, scope)
                    if val == pattern_val:
                        return self.execute_block(body, scope)

            # No match found and no else case
            return None

        # Handle unpacking in variables and not just function arguments 
        if kind == 'kwunpack':
            val = self.execute(node[1], scope)
            if not isinstance(val, dict):
                raise TypeError("** unpack argument must be a dict")
            return dict(val)
        
        if kind == 'unpack':
            val = self.execute(node[1], scope)
            return val
        
        if kind == 'lambda':
            _, params, body = node
            return Function(params, body, scope.copy())

        if kind == 'getitem':
            _, obj_expr, index_expr = node
            obj = self.execute(obj_expr, scope)
            index = self.execute(index_expr, scope)
            try:
                return obj[index]
            except (IndexError, KeyError, TypeError):
                raise RuntimeError(f"Cannot index into object: {obj} with key {index}")
        raise RuntimeError(f"Unknown node: {node}")
    
    def eval_expr(self, code):
        # Mainly just for lone expressions (1+1==2) to evaluate to True/False and not 1
        tokens = self.tokenize(code)
        ast = self.parse(tokens)
        if len(ast) == 1 and ast[0][0] in {'binop', 'num', 'str', 'var', 'list', 'dict'}:
            return self.execute(ast[0], self.global_scope)
        else:
            return self.execute_block(ast, self.global_scope)

    def include_module(self, args, _):
        filename = args[0]
        if not filename.endswith('.fn'):
            filename = filename + '.fn'
        if filename.startswith('@'):
            for p in PATH:
                f = os.path.join(p, filename[1:])
                if os.path.isfile(f):
                    filename = f
                    break
            else:
                raise FileNotFoundError(f"{filename[1:]} not found in {PATH}")
        try:
            with open(filename, 'r') as f:
                code = f.read()
        except FileNotFoundError:
            raise Exception(f"Included file '{filename}' not found")
        tokens = self.tokenize(code)
        ast = self.parse(tokens)
        module_obj = {}

        # First pass: collect class and methods
        local_class = {}
        nested_maps = {}
        for stmt in ast:
            if isinstance(stmt, tuple) and stmt[0] == 'class':
                # Support both 5 and 6 (nested vs non nested) element class nodes
                if len(stmt) == 6:
                    _, name, parents, fields, methods, nested_classes = stmt
                else:
                    _, name, parents, fields, methods = stmt
                    nested_classes = []

                def register_class(name, parents, fields, methods, nested_classes, parent_qual=None):
                    qual_name = f"{parent_qual}.{name}" if parent_qual else name
                    local_class[qual_name] = {
                        'fields': fields,
                        'parents': [f"{parent_qual}.{p}" if parent_qual and p in [nc[1] for nc in nested_classes] else p for p in parents],
                        '__methods__': {}
                    }

                    for method in methods:
                        _, mname, mparams, mbody = method
                        local_class[qual_name]['__methods__'][mname] = Function(mparams, mbody, self.global_scope)

                    for nested in nested_classes:
                        # Check if we have more nested classes
                        n_name, n_parents, n_fields, n_methods, n_nested = nested[1], nested[2], nested[3], nested[4], nested[5] if len(nested) == 6 else []

                        register_class(n_name, n_parents, n_fields, n_methods, n_nested, qual_name)

                register_class(name, parents, fields, methods, nested_classes)
                nested_map = self._build_nested_map(name, nested_classes)
                nested_maps[name] = nested_map

                def mk_constructor(fields, class_name, nested_map):
                    def constructor(args, _):
                        instance = {'__type__': class_name}
                        for i, (field_name, default_expr) in enumerate(fields):
                            if i < len(args):
                                instance[field_name] = args[i]
                            elif default_expr is not None:
                                val = self.execute_with_nested_map(default_expr, self.global_scope, nested_map)
                                instance[field_name] = val
                            else:
                                instance[field_name] = None
                        return instance
                    return constructor
                module_obj[name] = mk_constructor(fields, name, nested_map)

        # Second pass: collect functions and attach class methods
        for stmt in ast:
            if isinstance(stmt, tuple) and stmt[0] == 'def':
                _, name, params, body = stmt
                if '.' in name:
                    class_name, method_name = name.split('.', 1)
                    if class_name in local_class:
                        local_class[class_name]['__methods__'][method_name] = Function(params, body, self.global_scope)
                else:
                    module_obj[name] = Function(params, body, self.global_scope)
                    
        # Attach local_class to interpreter's self.classs
        for class_name, class_info in local_class.items():
            self.classs[class_name] = class_info
        return module_obj

    def execute_with_nested_map(self, node, scope, nested_map):
        # Like execute, but resolves var nodes using nested_map first
        if isinstance(node, tuple) and node[0] == 'var':
            name = node[1]
            if name in nested_map:
                # Return the qualified class name string
                return nested_map[name]
            if name in scope:
                return scope[name]
            raise NameError(f"Undefined variable {name}")
        if isinstance(node, tuple) and node[0] == 'getattr':
            left = self.execute_with_nested_map(node[1], scope, nested_map)
            attr = node[2]
            # If left is a qualified class name, return method from classs
            if isinstance(left, str) and left in self.classs:
                class_info = self.classs[left]
                if attr in class_info['__methods__']:
                    return class_info['__methods__'][attr]
                raise AttributeError(f"Class '{left}' has no method '{attr}'")
            return self.execute(('getattr', left, attr), scope)
        # Fallback to normal execute
        return self.execute(node, scope)

    def _build_nested_map(self, name, nested_classes, parent_qual=None, parent_map=None):
        # Recursively build a mapping of nested class names to their qualified names
        qual_name = f"{parent_qual}.{name}" if parent_qual else name
        local_map = dict(parent_map) if parent_map else {}
        for nested in nested_classes:
            n_name = nested[1]
            local_map[n_name] = f"{qual_name}.{n_name}"
            # keep recursing until theres no more, then provide an empty list as we reached the final level
            n_nested = nested[5] if len(nested) == 6 else []
            self._build_nested_map(n_name, n_nested, qual_name, local_map)
        return local_map

class REPL:
    def repl(self):
        print(f"nebula version {VERSION}")
        interp = Interpreter()
        buffer = []
        PS1, PS2 = ">>> ", "... "
        prompt = PS1

        while True:
            try:
                line = input(prompt)
            except (EOFError, KeyboardInterrupt):
                print()
                break

            if not buffer and line.strip() in {"quit", "exit", ":q"}:
                break
            if not buffer and line.strip() == ":reset":
                interp = Interpreter()
                buffer.clear()
                prompt = PS1
                print("Interpreter reset.")
                continue

            buffer.append(line)
            code = "\n".join(buffer)

            if self.needs_more(code, interp):
                prompt = PS2
                continue

            try:
                result = interp.run(code)
                if result is not None:
                    print(result)
            except Exception as e:
                print(f"Error: {e}")
            finally:
                buffer.clear()
                prompt = PS1

    def needs_more(self, code, interp):
        """Checks if we want to continue the block inside the REPL"""
        open_braces = code.count('{') - code.count('}')
        open_parens = code.count('(') - code.count(')')
        open_brackets = code.count('[') - code.count(']')

        # Unmatched brackets
        if open_braces > 0 or open_parens > 0 or open_brackets > 0:
            return True

        # Unterminated quotes
        if code.count('"') % 2 != 0 or code.count("'") % 2 != 0:
            return True

        # Try to tokenize and parse to check completeness
        try:
            tokens = interp.tokenize(code)
            interp.parse(tokens)
            return False
        except Exception:
            # If parser can't parse yet (not enough lines), its probably incomplete
            return False

def main():
    with open(sys.argv[1], 'r') as f:
        code = f.read()
    Interpreter().run(code)

if __name__ == '__main__':
    if len(sys.argv) < 2:
        r = REPL().repl()
    else:
        main()
