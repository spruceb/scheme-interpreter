from scheme_parse import Symbol, Cell, Number, String, cons_list
from scheme_evaluate import scheme_eval, Environment, Lambda, Form, ExternFunction, Function
from functools import reduce 
from numbers import Real
from collections.abc import Iterable
import operator
import math
import fractions

global_env = Environment(None)

global_env.define(Symbol('#t'), Symbol('#t'))
global_env.define(Symbol('true'), Symbol('#t'))
global_env.define(Symbol('#f'), Symbol('#f'))
global_env.define(Symbol('false'), Symbol('#f'))

scheme_true = Symbol('#t')
scheme_false = Symbol('#f')
# Functions, construct syntax trees instead of calling

def scheme_wrap(expr):
    if isinstance(expr, bool):
        return scheme_true if expr else scheme_false
    elif isinstance(expr, Real):
        return Number(expr)
    elif isinstance(expr, str):
        return String(expr)
    elif isinstance(expr, Iterable):
        return cons_list(map(scheme_wrap, expr))
    else:
        return expr

def python_wrap(sexpr):
    if isinstance(sexpr, Cell):
        return list(map(python_wrap, list(sexpr)))
    elif isinstance(sexpr, Number) or isinstance(sexpr, String):
        return sexpr.value
    elif isinstance(sexpr, Function) or isinstance(sexpr, Symbol):
        return sexpr

def listify(expr):
    return expr if isinstance(expr, Iterable) else [expr]

def dict_map(f, d):
    return {s: f(v) for s, v in d.items()}

def wrap_python_function(func):
    return lambda args, env: scheme_wrap(func(*listify(python_wrap(args))))

def reduce_factory(binary_function):
    return lambda *args: reduce(binary_function, args[1:], args[0])

reduce_functions = {'+': operator.add,
                    '*': operator.mul,
                    '-': operator.sub,
                    '/': operator.truediv,
                    'gcd': fractions.gcd,
                    'lcm': lambda a, b: (a * b) // fractions.gcd(a, b)}
reduce_functions = dict_map(reduce_factory, reduce_functions)


python_wrapped_functions = {'abs': abs,
                  'floor': math.floor,
                  'ceiling': math.ceil,
                  'round': round,
                  'truncate': int,
                  'sin': math.sin,
                  'cos': math.cos,
                  'tan': math.tan,
                  'asin': math.asin,
                  'acos': math.acos,
                  'exp': math.exp,
                  'quotient': lambda x, y: divmod(x, y)[0],
                  'remainder': lambda x, y: divmod(x, y)[1],
                  'modulo': operator.mod,
                  'log': math.log,
                  'max': max,
                  'min': min,
                  'zero?': lambda x: x == 0,
                  'sqrt': math.sqrt,
                  'expt': pow,
                  'eq?': lambda x, y: x == y,
                  'begin': lambda *x: x[-1],
                  'list': cons_list}
python_wrapped_functions.update(reduce_functions)
python_wrapped_functions = dict_map(wrap_python_function, python_wrapped_functions)

wrapped_functions = {'cons': lambda args: Cell(args.car, args.cdr.car),
                     'car': lambda args: args.car.car,
                     'cdr': lambda args: args.car.cdr,
                     'not': lambda args: scheme_wrap(args.car == scheme_false),
                     'pair?': lambda args: isinstance(args.car, Cell),
                     'null?': lambda args: isinstance(args.car, Cell) and args.car.null,
                     'number?': lambda args: isinstance(args.car, Number),
                     'procedure?': lambda args: isinstance(args.car, Function),
                     'display': lambda args: print(args.car, end=''),
                     'newline': lambda args: print()}

wrapped_functions = dict_map(lambda f: lambda args, env: f(args), wrapped_functions)

def comparision_factory(f):
    def _(args, env):
        last = args.car.value
        for i in iter(args.cdr):
            if f(i.value, last):
                return scheme_false
            last = i.value
        return scheme_true
    return _

eql = comparision_factory(lambda x, y: x != y)
greater = comparision_factory(lambda x, y: x >= y)
ge = comparision_factory(lambda x, y: x > y)
less = comparision_factory(lambda x, y: x <= y)
le = comparision_factory(lambda x, y: x < y)

def set_car(args, env):
    args.car.car = args.cdr.car

def set_cdr(args, env):
    args.car.cdr = args.cdr.car

global_functions = {'>': greater,
                    '>=': ge,
                    '<': less,
                    '<=': le,
                    '=': eql,
                    'set-car!': set_car,
                    'set-cdr!': set_cdr}
global_functions.update(python_wrapped_functions)
global_functions.update(wrapped_functions)


# Forms, can be called directly

def create_lambda(args, env):
    argnames = args.car
    body = args.cdr
    return Lambda(argnames, Cell(Symbol('begin'), body), env)

def define(args, env):
    if type(args.car) is Symbol:
        env.define(args.car, scheme_eval(args.cdr.car, env))
    elif type(args.car) is Cell:
        name = args.car.car
        arguments = args.car.cdr
        body = args.cdr
        if arguments.car == Symbol('.'):
            arguments = arguments.cdr.car
        env.define(name, create_lambda(Cell(arguments, body), env))

def cond(args, env):
    l = list(args)
    for i, s in enumerate(l):
        if s.car == Symbol('else') or scheme_eval(s.car, env) != Symbol('#f'):
            if s.car == Symbol('else') and i != len(l) - 1:
                raise SyntaxError('Misplaced ELSE clause')
            return scheme_eval(Cell(Symbol('begin'), s.cdr), env)

def scheme_if(args, env):
    return cond(cons_list([cons_list([args.car, args.cdr.car]), 
                    cons_list([Symbol('else'), args.cdr.cdr.car])]), env)

def scheme_and(args, env):
    for i in iter(args):
        result = scheme_eval(i, env)
        if result == scheme_false:
            return result
    return result

def scheme_or(args, env):
    for i in iter(args):
        result = scheme_eval(i, env)
        if result != scheme_false:
            return result
    return scheme_false

def scheme_apply(args, env):
    return scheme_eval(Cell(args.car, scheme_eval(args.cdr.car, env)), env)

def let(args, env):
    var_list = args.car
    body = args.cdr
    argnames = cons_list(i.car for i in var_list)
    arg_values = cons_list(scheme_eval(i.cdr.car, env) for i in var_list)
    l = create_lambda(Cell(argnames, body), env)
    return l(arg_values)

def let_star(args, env):
    if args.car.null:
        return scheme_eval(Cell(Symbol('begin'), args.cdr), env)
    else:
        return let_star(Cell(args.car.cdr, args.cdr), 
                    Environment(env, 
                                {args.car.car.car: 
                                    scheme_eval(args.car.car.cdr.car, env)}))

global_forms = {'lambda': create_lambda,
                'define': define,
                'cond': cond,
                'if': scheme_if,
                'and': scheme_and,
                'or': scheme_or,
                'quote': lambda args, env: args.car,
                'apply': scheme_apply,
                'set!': lambda args, env: env.set(args.car, args.cdr.car),
                'let': let,
                'let*': let_star}

for s, v in global_functions.items():
    global_env.define(s, ExternFunction(v, global_env))
for s, v in global_forms.items():
    global_env.define(s, Form(v))