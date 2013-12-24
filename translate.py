# http://cran.r-project.org/doc/manuals/r-release/R-lang.html

import ast
from StringIO import StringIO
import subprocess

from more_itertools import chunked

from reader import reader
from unparse import Unparser


class UnknownError(Exception): pass

class CueGeneric(ast.AST):

    """
    Represents a node in a tree.
    
    A tree node has a single parent, a list of children,
    and a reference to the data it contains.
    """

    def __init__(self, level, type_, recs):
        self.level = level
        self.type = type_
        self.recs = recs
        self.children = []

        self.content = None
        for rec in recs:
            if rec.name == 'content':
                self.content = rec.value
            

    def __repr__(self):
        return '{}({})'.format(self.__class__.__name__, self.type)


class CueNull(ast.AST): pass

class CueBody(ast.AST):
    _fields = ['exprs']

class CueExpression(ast.AST):
    _fields = ['children']

class CuePairlist(ast.AST):
    _fields = ['argslist']

    def __init__(self, recs):
        self.argslist = []

        # TODO make these separate nodes
        rec_values = (rec.value for rec in recs)
        for name, value, type_ in chunked(rec_values, 3):
            self.argslist.append((name, value, type_))


class CueLanguage(ast.AST):
    _fields = ['children']

class CueSymbol(ast.AST):
    _fields = ['content']


class CueFunction(ast.AST):
    _fields = ['args', 'body']

    def __init__(self, args, body, dontknow):
        self.args = args
        # TODO parse out the body statements
        self.body = [body]

class CueAssign(ast.AST):
    _fields = ['left', 'right']

class CueAssignOp(ast.operator): pass


def add_simple_ops():
    # Simple CueOp nodes
    _g = globals()
    for name in ['Function', 'If', 'Return', 'Block', 'Paren']:
        name = 'Cue' + name + 'Op'
        _g[name] = type(name, (ast.AST,), {})

add_simple_ops()

class CueError(Exception): pass

def run_cue(text):
    p = subprocess.Popen(['Rscript', 'cue.r'], stdin=subprocess.PIPE,
                         stdout=subprocess.PIPE, stderr=subprocess.PIPE)

    out, err = p.communicate(text)
    if err:
        raise CueError(err)

    return out


class Transformer(ast.NodeTransformer):

    def visit_CueGeneric(self, node):

        if node.type == 'symbol':
            newnode = CueSymbol(node.content)

        elif node.type == 'language':
            newnode = CueLanguage(node.children)

        elif node.type == 'expression':
            newnode = CueExpression(node.children)

        elif node.type == 'NULL':
            newnode = CueNull()

        elif node.type == 'double':
            # TODO could be float()?
            newnode = ast.Num(int(node.content))

        elif node.type == 'pairlist':
            newnode = CuePairlist(node.recs)

        elif node.type == 'character':
            newnode = ast.Str(node.content)

        return self.visit(newnode)

    def visit_CueExpression(self, node):
        return [self.visit(child) for child in node.children]

    def visit_CueSymbol(self, node):
        op_str = node.content


        op_map = {
            # Binary
            '<-': CueAssignOp,
            '=': CueAssignOp,
            '*': ast.Mult,
            # TODO this probably isn't true, unless __future__.division is always
            #      imported. R also has '%/%' for integer division
            '/': ast.Div,
            '+': ast.Add,
            '-': ast.Sub,
            '%%': ast.Mod,
            '^': ast.Pow,
            '**': ast.Pow,

            # Comparison
            '<': ast.Lt,
            '<=': ast.LtE,
            '>': ast.Gt,
            '>=': ast.GtE,
            '==': ast.Eq,
            '!=': ast.NotEq,
            '%in%': ast.In,
            # R doesn't have a simple equivalent to 'is'
            # http://stackoverflow.com/questions/10912729/r-object-identity

            # Unary
            '!': ast.Not,

            # Boolean
            # TODO there's a difference between vectorized and not
            # TODO not handling the vectorized ops '&', '|', etc.
            '&&': ast.And,
            '||': ast.Or,

            # Other
            'function': CueFunctionOp,
            'if': CueIfOp,
            '{': CueBlockOp,
            '(': CueParenOp,
            'return': CueReturnOp,
        }

        try:
            return op_map[op_str]()
        except KeyError:
            return ast.Name(op_str, ast.Load())


    def visit_CueLanguage(self, node):
        # TODO should visit children here?
        children = [self.visit(child) for child in node.children]
        assert len(children) > 0

        op = children[0]
        rest = children[1:]

        # TODO could break these out into their own nodes,
        #      but it doesn't seem critical

        if isinstance(op, ast.operator):
            assert len(rest) == 2
            left, right = rest

            # Assignment is special in R because it could either be 
            # simple assignment, or a function definition, or ...
            if isinstance(op, CueAssignOp):
                newnode = CueAssign(left, right)
            else:
                newnode = ast.BinOp(left, op, right)

        elif isinstance(op, ast.cmpop):
            assert len(rest) == 2
            left, right = rest
            newnode = ast.Compare(left, [op], [right])

        elif isinstance(op, ast.unaryop):
            assert len(rest) == 1
            operand = rest[0]
            newnode = ast.UnaryOp(op, operand)

        elif isinstance(op, ast.boolop):
            assert len(rest) == 2
            left, right = rest
            newnode = ast.BoolOp(op, [left, right])

        elif isinstance(op, CueFunctionOp):
            assert len(rest) == 3
            args, body, dontknow = rest
            newnode = CueFunction(args, body, dontknow)

        elif isinstance(op, CueIfOp):
            assert len(rest) == 2
            cond, body = rest

            if isinstance(body, ast.expr):
                body = ast.Expr(body)
            elif isinstance(body, CueBody):
                body = [ast.Expr(e) for e in body.exprs]

            newnode = ast.If(rest[0], body, None)

        elif isinstance(op, CueBlockOp):
            newnode = CueBody(rest)

        elif isinstance(op, CueParenOp):
            print rest
            newnode = rest[0]

        elif isinstance(op, CueReturnOp):
            if not rest:
                newnode = ast.Return(value=None)
            else:
                assert len(rest) == 1
                value = rest[0]
                newnode = ast.Return(value=value)

        elif isinstance(op, ast.Name):
            # TODO this allows invalid function names,
            #      and doesn't catch symbols that aren't functions,
            #      such as '(' and 'read.csv'

            # TODO wouldn't support foo(1)(2)

            args = []
            for r in rest:
                if isinstance(r, CueSymbol):
                    n = ast.Name(r.content, ast.Load())
                    args.append(n)

                elif isinstance(r, ast.expr):
                    args.append(r)

                else:
                    raise UnknownError()

            newnode = ast.Call(op, args, [], None, None)

        else:
            raise UnknownError()

        return self.visit(newnode)


    def visit_CueAssign(self, node):
        # TODO a lot of these assertions should fail as the transformer
        #      develops, i.e. having a symbol on the right-hand side
        #      is totally valid, but I don't handle it yet
        assert not isinstance(node.right, CueSymbol)

        newleft = ast.Name(node.left.id, ast.Store())

        # TODO could be a symbol
        # TODO move to visit_CueFunction
        if isinstance(node.right, CueFunction):
            arguments = []

            if isinstance(node.right.args, CuePairlist):
                argslist = node.right.args.argslist
                args = [ast.Name(name, ast.Param()) for name, value, type_ in argslist]
                arguments = ast.arguments(args, None, None, [])

            body = []
            for n in node.right.body:
                if isinstance(n, ast.stmt):
                    body.append(n)
                elif isinstance(n, ast.expr):
                    n = ast.Expr(n)
                    body.append(n)
                elif isinstance(n, CueBody):
                    for expr in n.exprs:
                        body.append(ast.Expr(expr))

            return ast.FunctionDef(node.left.id, arguments, body, [])

        return ast.Assign([newleft], node.right)

    def visit_CueAdd(self, node):
        return ast.BinOp(node.left, ast.Add(), node.right)

    def visit_CueMult(self, node):
        return ast.BinOp(node.left, ast.Mult(), node.right)


def translate(raw):

    cue_out = run_cue(raw)
    print cue_out

    nodes = reader(cue_out.split('\n'), CueGeneric)
    root = nodes.next()

    body = Transformer().visit(root)
    tree = ast.Module(body)

    print ast.dump(tree)

    out = StringIO()
    Unparser(tree, out)
    return out.getvalue()
    

if __name__ == '__main__':
    #print translate('1 %in% foo')
    #print translate('funcname <- function(x) return()')
    print translate('foo(c, d, 1)')
