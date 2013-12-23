import ast
import re
from StringIO import StringIO
import subprocess
import sys

from more_itertools import chunked, peekable

from unparse import Unparser


class Unknown(Exception): pass

class CueGeneric(ast.AST):

    """
    Represents a node in a tree.
    
    A tree node has a single parent, a list of children,
    and a reference to the data it contains.
    """

    _fields = ['children']

    def __init__(self, level, type_, content):
        self._parent = None
        self.children = []
        self.level = level
        self.type = type_
        self.content = content

    def __repr__(self):
        content = self.content
        if len(content) > 40:
            content = content[:40] + '...'

        return '{}({})'.format(self.__class__.__name__,
                               repr((self.level, self.type, content)))

    @property
    def parent(self):
        return self._parent

    @parent.setter
    def parent(self, value):
        # If this node already has a parent,
        # delete this node from that parent's children
        if self._parent:
            self._parent.children.remove(self)
        self._parent = value
        self._parent.children.append(self)

    def walk(self):
        yield self
        for child in self.children:
            for node in child.walk():
                yield node

    def is_double(self):
        return self.type == 'double'

    def is_assignment(self):
        if self.type == 'language':
            first_child = self.children[0]
            return (first_child.type == 'symbol' and
                    first_child.content == '<-' or first_child.content == '=')

    def is_addition(self):
        if self.type == 'language':
            first_child = self.children[0]
            return (first_child.type == 'symbol' and
                    first_child.content == '+')


class CueExpression(CueGeneric): pass
class CueLanguage(CueGeneric): pass
class CueSymbol(CueGeneric): pass
class CueDouble(CueGeneric): pass
class CueNumber(CueGeneric): pass
class CueNull(CueGeneric): pass


class CueBinOp(ast.AST):
    _fields = ['left', 'right']

_g = globals()
for name in ['Assign', 'Add', 'Sub', 'Mult', 'Div', 'Mod']:
    name = 'Cue' + name
    _g[name] = type(name, (CueBinOp,), {})


class CueFunction(ast.AST):
    _fields = ['args', 'body', 'dontknow']


def run_cue(text):
    p = subprocess.Popen(['Rscript', 'cue.r'], stdin=subprocess.PIPE,
                         stdout=subprocess.PIPE, stderr=subprocess.PIPE)

    out, err = p.communicate(text)
    return out


def reader(lines):
    lines = (line.strip() for line in lines if line.startswith('.'))
    lines = (re.sub('^\.(?:level|type|content)\s', '', line) for line in lines)
    chunks = chunked(lines, 3)

    def gen():
        for level, type_, content in chunks:
            yield CueGeneric(int(level), type_, content)
    return peekable(gen())


def build_tree(nodes, parent):
    try:
        while nodes.peek().level > parent.level:
            if nodes.peek().level == parent.level + 1:
                node = nodes.next()
                node.parent = parent
            else:
                build_tree(nodes, node)

    except StopIteration:
        pass


def print_tree(root):
    for node in root.walk():
        indent = '  ' * node.level
        print indent, node


class Transformer(ast.NodeTransformer):

    def visit_CueGeneric(self, node):
        m = {
            'expression': CueExpression,
            'language': CueLanguage,
            'symbol': CueSymbol,
            'double': CueDouble,
            'number': CueNumber,
            'NULL': CueNull,
        }
        cls = m[node.type]
        newnode = cls(node.level, node.type, node.content)
        newnode.children = node.children
        return self.visit(newnode)

    def visit_CueExpression(self, node):
        print node, node.children
        return [self.visit(child) for child in node.children]

    def visit_CueLanguage(self, node):
        children = [self.visit(child) for child in node.children]
        assert len(children) > 0

        # TODO should visit children here?
        first = children[0]
        op_str = first.content


        if op_str == 'function':
            assert len(children) == 4
            args, body, dontknow = children[1:]
            newnode = CueFunction(args, body, dontknow)
            return self.visit(newnode)


        if op_str == 'return':
            newnode = ast.Return(value=None)
            return self.visit(newnode)


        assert len(children) == 3
        left, right = children[1:]
        assert isinstance(first, CueSymbol)

        # Assignment, which is special in R because it could either be 
        # simple assignment, or a function definition, or ...
        if op_str == '<-' or op_str == '=':
            newnode = CueAssign(left, right)
            return self.visit(newnode)


        # Simple binary operation 
        binary_ops = {
            '%': ast.Mod(),
            '*': ast.Mult(),
            '/': ast.Div(),
            '+': ast.Add(),
            '-': ast.Sub(),
        }

        try:
            op = binary_ops[op_str]
        except KeyError:
            raise Unknown()

        newnode = ast.BinOp(left, op, right)
        return self.visit(newnode)


    def visit_CueAssign(self, node):
        # TODO a lot of these assertions should fail as the transformer
        #      develops, i.e. having a symbol on the right-hand side
        #      is totally valid, but I don't handle it yet
        assert isinstance(node.left, CueSymbol)
        assert not isinstance(node.right, CueSymbol)

        newleft = ast.Name(node.left.content, ast.Assign())

        # TODO could be a symbol
        if isinstance(node.right, CueFunction):
            return ast.FunctionDef(node.left.content, [], [node.right.body], [])

        return ast.Assign([newleft], node.right)

    def visit_CueAdd(self, node):
        return ast.BinOp(node.left, ast.Add(), node.right)

    def visit_CueMult(self, node):
        return ast.BinOp(node.left, ast.Mult(), node.right)

    def visit_CueSymbol(self, node):
        print node, node.children
        return node

    def visit_CueDouble(self, node):
        # TODO could be float()?
        return ast.Num(int(node.content))

    def visit_CueNumber(self, node):
        print node, node.children
        return node


def translate(raw):

    cue_out = run_cue(raw)
    cue_nodes = reader(cue_out.split('\n'))

    print cue_out

    root = cue_nodes.next()
    build_tree(cue_nodes, root)

    body = Transformer().visit(root)
    tree = ast.Module(body)

    print ast.dump(tree)

    out = StringIO()
    Unparser(tree, out)
    return out.getvalue()
    

if __name__ == '__main__':
    #print translate('x <- 1')
    print translate('n <- function() return(1, 2, 3, 4)')
