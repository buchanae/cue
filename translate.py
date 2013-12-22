import subprocess

from more_itertools import chunked, peekable


class TreeNode(object):

    """
    Represents a node in a tree.
    
    A tree node has a single parent, a list of children,
    and a reference to the data it contains.
    """

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

        return 'TreeNode({})'.format(repr((self.level, self.type, content)))

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


def run_cue(text):
    p = subprocess.Popen(['Rscript', 'cue.r'], stdin=subprocess.PIPE,
                         stdout=subprocess.PIPE, stderr=subprocess.PIPE)

    out, err = p.communicate(text)
    return out


def reader(lines):
    lines = (line.strip() for line in lines if line)
    chunks = chunked(lines, 3)

    def gen():
        for level, type_, content in chunks:
            yield TreeNode(int(level), type_, content)
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


def is_assignment(node):
    first_child = node.children[0]
    return (node.type == 'language' and first_child.type == 'symbol' and
            first_child.content == '<-' or first_child.content == '=')


def output_assignment(node):
    left = node.children[1]
    right = node.children[2]
    simple = {'double'}

    if right.type in simple:
        print left.content, '=', right.content

    # Function definition
    elif right.type == 'language':
        output_function(left.content, right)


func_tpl = '''
def {name}():
    body
'''.strip()


def output_function(name, node):
    print func_tpl.format(name=name)


if __name__ == '__main__':

    out = run_cue("""
    x <- 1

    # comment
    """)

    nodes = reader(out.split('\n'))

    root = nodes.next()
    build_tree(nodes, root)

    for node in root.children:
        if is_assignment(node):
            output_assignment(node)
