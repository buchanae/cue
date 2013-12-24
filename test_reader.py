from nose.tools import eq_

from reader import reader, Rec


def test_reader():

    nodes = reader(dummy_lines)
    nodes = list(nodes)

    eq_(len(nodes), 12)

    types = [node.type for node in nodes]
    eq_(types, [
        'expression',
        'language',
        'symbol',
        'symbol',
        'language',
        'symbol',
        'NULL',
        'double',
        'NULL',
        'language',
        'symbol',
        'pairlist',
    ])

    recs = [node.recs for node in nodes]
    eq_(recs, [
        [],
        [],
        [Rec('content', '<-')],
        [Rec('content', 'foo')],
        [],
        [Rec('content', 'function')],
        [Rec('content', None)],
        [Rec('content', '1')],
        [Rec('content', None)],
        [],
        [Rec('content', 'function')],
        [
            Rec('argname', 'x'),
            Rec('argvalue', None),
            Rec('argtype', 'symbol'),
            Rec('argname', 'bar'),
            Rec('argvalue', 'foo'),
            Rec('argtype', 'symbol'),
            Rec('argname', 'gz'),
            Rec('argvalue', '2'),
            Rec('argtype', 'double'),
        ]
    ])

    children = [node.children for node in nodes]
    expected = [
        [nodes[1], nodes[9]],
        nodes[2:5],
        [],
        [],
        nodes[5:9],
        [],
        [],
        [],
        [],
        nodes[10:12],
        [],
        []
    ]
    eq_(children, expected)


dummy_lines = '''
.level 0
.type expression

.level 1
.type language

.level 2
.type symbol
.content <-

.level 2
.type symbol
.content foo

.level 2
.type language

.level 3
.type symbol
.content function

.level 3
.type NULL
.content

.level 3
.type double
.content 1

.level 3
.type NULL
.content

.level 1
.type language

.level 2
.type symbol
.content function

.level 2
.type pairlist
.argname x
.argvalue
.argtype symbol
.argname bar
.argvalue foo
.argtype symbol
.argname gz
.argvalue 2
.argtype double
'''.strip().split('\n')
