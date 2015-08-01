#!/usr/local/bin/python3
import readline
import sys
from scheme_parse import parse
from scheme_evaluate import scheme_eval
from scheme_global import global_env


def file_eval(filename):
    with open(filename, 'r') as program_file:
        code = program_file.read()
        code = '(begin ' + code + ')'
        parsed = parse(code)
        scheme_eval(parsed, global_env)

def repl():
    code = ''
    while True:
        code += input()
        try:
            parsed = parse(code)
        except SyntaxError as e:
            code += '\n'
            continue
        else:
            result = scheme_eval(parsed, global_env)
            print(result if result is not None else 'Unspecified value')
            code = ''

if __name__ == '__main__':
    if len(sys.argv) > 1:
        file_eval(sys.argv[1])
    else:
        print("Scheme REPL")
        repl()