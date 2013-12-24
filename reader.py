from collections import namedtuple
from itertools import tee
import re

from more_itertools import peekable


_rx = re.compile('^\.(.+?)(?:\s(.*))?$')
Rec = namedtuple('Rec', 'name value')

class ParseError(Exception): pass

def _gen_recs(lines):
    for line in lines:
        if line.startswith('.'):
            m = _rx.match(line.strip())
            if not m:
                raise ParseError(line)
            else:
                yield Rec._make(m.groups())


def _group_recs(recs):
    recs = peekable(recs)

    group = []
    try:
        while True:
            while not group or recs.peek().name != 'level':
                group.append(recs.next())

            yield group
            group = []

    except StopIteration:
        yield group




def _convert(groups, Node):
    for group in groups:
        level_rec = group[0]
        assert level_rec.name == 'level'
        level = int(level_rec.value)

        type_rec = group[1]
        assert type_rec.name == 'type', 'expected .type: {}'.format(type_rec)
        type_ = type_rec.value

        node = Node(level, type_, group[2:])

        yield node
        

class Node(object):
    def __init__(self, level, type_, recs):
        self.level = level
        self.type = type_
        self.recs = recs
        self.children = []

    def __repr__(self):
        return 'Node({}, {})'.format(self.level, self.type)


def _build_tree(nodes, parent):
    try:
        while nodes.peek().level > parent.level:
            if nodes.peek().level == parent.level + 1:
                node = nodes.next()
                parent.children.append(node)
            else:
                _build_tree(nodes, node)

    except StopIteration:
        pass


def reader(lines, Node=Node):
    recs = _gen_recs(lines)
    groups = _group_recs(recs)
    nodes = _convert(groups, Node)

    nodes_a, nodes_b = tee(nodes)

    root = nodes_a.next()
    nodes_a = peekable(nodes_a)
    _build_tree(nodes_a, root)

    return nodes_b


def print_tree(root):
    for node in root.walk():
        indent = '  ' * node.level
        print indent, node
