import ast
from StringIO import StringIO
import subprocess

from more_itertools import chunked

from reader import reader
from unparse import Unparser


class Unknown(Exception): pass

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

class CueBinOp(ast.AST):
    _fields = ['left', 'right']

_g = globals()
for name in ['Assign', 'Add', 'Sub', 'Mult', 'Div', 'Mod']:
    name = 'Cue' + name
    _g[name] = type(name, (CueBinOp,), {})


class CueFunction(ast.AST):
    _fields = ['args', 'body']

    def __init__(self, args, body, dontknow):
        self.args = args
        # TODO parse out the body statements
        self.body = [body]


def run_cue(text):
    p = subprocess.Popen(['Rscript', 'cue.r'], stdin=subprocess.PIPE,
                         stdout=subprocess.PIPE, stderr=subprocess.PIPE)

    out, err = p.communicate(text)
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

        return self.visit(newnode)

    def visit_CueExpression(self, node):
        return [self.visit(child) for child in node.children]

    def visit_CueLanguage(self, node):
        children = [self.visit(child) for child in node.children]
        assert len(children) > 0

        # TODO should visit children here?
        first = children[0]
        rest = children[1:]
        op_str = first.content


        # Simple binary operation 
        binary_ops = {
            '<-': CueAssign,
            '=': CueAssign,
            '%': ast.Mod,
            '*': ast.Mult,
            '/': ast.Div,
            '+': ast.Add,
            '-': ast.Sub,
        }

        assert isinstance(first, CueSymbol)

        if op_str in binary_ops:
            assert len(rest) == 2
            left, right = rest

            op_cls = binary_ops[op_str]

            # Assignment is special in R because it could either be 
            # simple assignment, or a function definition, or ...
            if op_cls == CueAssign:
                newnode = CueAssign(left, right)
            else:
                newnode = ast.BinOp(left, op_cls(), right)


        elif op_str == 'function':
            assert len(rest) == 3
            args, body, dontknow = rest
            newnode = CueFunction(args, body, dontknow)


        elif op_str == 'return':
            if not rest:
                newnode = ast.Return(value=None)
            else:
                assert len(rest) == 1
                value = rest[0]
                newnode = ast.Return(value=value)

        else:
            # TODO this allows invalid function names,
            #      and doesn't catch symbols that aren't functions,
            #      such as '(' and '{'

            # TODO wouldn't support foo(1)(2)
            name = ast.Name(op_str, ast.Load())
            print rest
            newnode = ast.Call(name, rest, [], None, None)

        return self.visit(newnode)


    def visit_CueAssign(self, node):
        # TODO a lot of these assertions should fail as the transformer
        #      develops, i.e. having a symbol on the right-hand side
        #      is totally valid, but I don't handle it yet
        assert isinstance(node.left, CueSymbol)
        assert not isinstance(node.right, CueSymbol)

        newleft = ast.Name(node.left.content, ast.Store())

        # TODO could be a symbol
        if isinstance(node.right, CueFunction):
            arguments = []

            if isinstance(node.right.args, CuePairlist):
                print 'function', node.right.args.argslist
                argslist = node.right.args.argslist
                args = [ast.Name(name, ast.Param()) for name, value, type_ in argslist]
                arguments = ast.arguments(args, None, None, [])

            # TODO should probably do this stuff in visit_CueFunction
            body = []
            for n in node.right.body:
                if isinstance(n, ast.expr):
                    n = ast.Expr(n)

                assert isinstance(n, ast.stmt)
                body.append(n)

            return ast.FunctionDef(node.left.content, arguments, body, [])

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
    print translate('func <- function(x) return(1)')
    #print translate('foo <- function(x, baz=2, bar=4) { return(x) }; foo(1, bar=3)')
