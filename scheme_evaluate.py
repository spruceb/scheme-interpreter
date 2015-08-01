from scheme_parse import Symbol, Cell, Number, String, cons_list

class Environment:
    def __init__(self, parent, definitions={}):
        self._definitions = definitions
        self.parent = parent

    def __getitem__(self, key):
        if type(key) is str:
            key = Symbol(key)
        result = self._definitions.get(key)
        if result is not None:
            return result
        if self.parent is not None:
            return self.parent[key]
        raise RuntimeError("Symbol not defined: {}".format(key))

    def get(self, key):
        try:
            return self[key]
        except RuntimeError:
            return None 
    def __str__(self):
        return "Environment({})".format(self._definitions)

    def set(self, key, value):
        if self.parent is not None:
            if self.get(key) is None and self.parent.get(key) is not None:       
                self.parent.set(key, value)
        else:
            self.define(key, value)

    def define(self, key, value):
        if type(key) is str:
            key = Symbol(key)
        if type(key) is not Symbol:
            raise RuntimeError("Attempt to use a non-symbol {} as a symbol".format(key))
        self._definitions[key] = value

class Function:
    pass

class ExternFunction(Function):
        def __init__(self, python_function, parent_env):
            self.parent_env = parent_env
            self.python_function = python_function

        def __call__(self, arguments):
            return self.python_function(arguments, self.parent_env)

        def __str__(self):
            return '[function {}]'.format(self.python_function)

        def __repr__(self):
            return(str(self))


class Lambda(Function):
    def __init__(self, argnames, code, parent_env):
        self.argnames = argnames
        self.code = code
        self.parent_env = parent_env

    def __call__(self, arguments):
        if type(self.argnames) is Symbol:
            name_bind = {self.argnames: arguments}
        elif Symbol('.') in self.argnames:
            names_l = list(self.argnames)
            args_l = list(arguments)
            positionals = names_l.index(Symbol('.'))
            name_bind = {s: v for s, v in zip(names_l[:positionals], args_l[:positionals])}
            name_bind[names_l[positionals + 1]] = cons_list(args_l[positionals:])
        else:
            name_bind = {s: v for s, v in zip(self.argnames, arguments)}
        call_env = Environment(self.parent_env, name_bind)
        return scheme_eval(self.code, call_env)

    def __str__(self):
        return "[function (lambda {} {})]".format(self.argnames, self.code)

    def __repr__(self):
        return str(self)

class Form:
    def __init__(self, function):
        self.function = function

    def __call__(self, args, env):
        return self.function(args, env)

def scheme_eval_list(lst, env):
    return cons_list(map(lambda x: scheme_eval(x, env), iter(lst)))

def scheme_eval(data, env):
    if type(data) is Number or type(data) is String:
        return data
    elif type(data) is Symbol:
        if data.string[0] == "'":
            return scheme_eval(Cell(Symbol('quote'), Cell(Symbol(data.string[1:]), Cell(null=True))), env)
        return env[data]
    elif type(data) is Cell:
        if data.null:
            return data
        operator = scheme_eval(data.car, env)
        args = data.cdr
        if isinstance(operator, Function):
            return operator(scheme_eval_list(args, env))
        elif type(operator) is Form:
            return operator(args, env)
        else:
            raise SyntaxError('"{}" is not applicable'.format(operator))
    else:
        raise RuntimeError("Unkown parsed object {} of type {}".format(data, type(data)))
