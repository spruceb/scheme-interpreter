from itertools import takewhile
class Symbol:
    def __init__(self, symbol):
        if " " in symbol:
                raise SyntaxError("Space in invalid symbol: {}".format(string))
        self.string = symbol.upper()

    def __str__(self):
        return self.string
    def __eq__(self, other):
        return isinstance(other, Symbol) and self.string.upper() == other.string.upper()
    def __hash__(self):
        return hash(self.string)
    def __repr__(self):
        return "Symbol({})".format(self)

class Cell:
    def __init__(self, car=None, cdr=None, null=False):
        self.car = car
        self.cdr = cdr
        self.null = null

    def __str__(self):
        if self.null:
            return "()"
        elif type(self.cdr) is Cell and self.cdr.null:
            return "({})".format(self.car)
        elif type(self.cdr) is Cell:
            return "({} {}".format(self.car, str(self.cdr)[1:])
        return "({} {})".format(self.car, self.cdr)

    def __iter__(self):
        if not self.null:
            yield self.car
            yield from self.cdr

    def __repr__(self):
        return "Cell({})".format(self)

def cons_list(python_list):
    i = iter(python_list)
    car = next(i, Cell(null=True))
    if type(car) is Cell and car.null:
        return car
    return Cell(car, cons_list(i))
DELIMS = ' \n\t'
class Number:
    def __init__(self, value):
        if type(value) is str:
            if (value.count(".") > 1 or value.count('-') > 1):
                raise SyntaxError("Invalid number: {}".format(string)) 
            f = float(value)
            i = int(f)
        else:
            i = int(value)
            f = float(value)
        self.value = i if f == float(i) else f
    
    def __str__(self):
        return str(self.value)

    def __eq__(self, other):
        return type(self) is type(other) and self.value == other.value

    def __repr__(self):
        return "Number({})".format(self)

class String:
    def __init__(self, value):
        self.value = value.replace('\\"', '"')

    def __str__(self):
        return '"{}"'.format(self.value)

    def __eq__(self, other):
        return type(self) is type(other) and self.value == other.value

    def __repr__(self):
        return "String({})".format(self)

def first_item(string):
    string = string.strip()
    if string[0] == "(":
        count = 0
        for i, c in enumerate(string):
            count += 1 if c == "(" else -1 if c == ")" else 0
            if count == 0:
                return (string[:i + 1], string[i + 1:])
            elif count < 0:
                raise SyntaxError("Unbalanced parens: {}".format(string))
    elif string[0] == '"':
        end = string.find('"', 1) + 1
        while string[end-2] == '\\':
            end = string.find('"', end) + 1
        return (string[:end], string[end:])
    else:
        rest = iter(string)
        return ("".join(takewhile(lambda x: x not in DELIMS + ')', rest)), 
                "".join(rest))

def parse(string):
    string = string.strip()
    if string == ')' or string == '': return Cell(null=True)
    if string[0] != "(":
        def is_num(s):
            return (s[0] == '-' and len(s) > 1 and is_num(s[1:])) \
                    or all(c.isdigit() or c == "." for c in s)
        if is_num(string):
            return Number(string)
        elif string[0] == string[-1] == '"':
            return String(string[1:-1])
        else:
            return Symbol(string)
    else:
        if string in "()" or string == '()':
            return Cell(null=True)
        if string[-1] != ")" or string.count('(') != string.count(')'):
            raise SyntaxError("Unbalanced parens:\n {}".format(string))
        string = string[1:-1].strip()
        split = first_item(string)
        return Cell(parse(split[0]), parse('(' + split[1] + ')'))
