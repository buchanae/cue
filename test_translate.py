from nose.tools import assert_raises, eq_

from translate import translate, CueError


translations = (

    ('n <- 1', 'n = 1'),

    ('n = 1', 'n = 1'),

    ('1 + 2', '(1 + 2)'),
    ('1 - 2', '(1 - 2)'),
    ('1 * 2', '(1 * 2)'),
    ('1 / 2', '(1 / 2)'),
    ('1 %% 2', '(1 % 2)'),
    ('1 ^ 2', '(1 ** 2)'),
    ('1 ** 2', '(1 ** 2)'),

    # TODO I don't like how unparse adds the extra parens
    ('1 + 2 + 3', '((1 + 2) + 3)'),

    ('(1 + 2) + 3', '((1 + 2) + 3)'),


    ('1 - 2 - 3', '((1 - 2) - 3)'),

    ('funcname <- function() 1', 'def funcname():\n    1'),

    ('funcname <- function() return(1)', 'def funcname():\n    return 1'),

    ('funcname <- function() return()', 'def funcname():\n    return'),

    ('funcname <- function(x) return()', 'def funcname(x):\n    return'),

    ('funcname <- function() { 2; 2 }', 'def funcname():\n    2\n    2'),

    ('funcname <- function() foo(1)', 'def funcname():\n    foo(1)'),

    ('foo(c, d, 1)', 'foo(c, d, 1)'),

    ('if (1) 2', 'if 1:\n    2'),

    ('if (1) { 2; 2 }', 'if 1:\n    2\n    2'),
)


def check_translation(raw, expected):
    eq_(translate(raw).lstrip('\n'), expected)

def test_translations():
    for raw, expected in translations:
        yield check_translation, raw, expected


errors = (
    '1, 2',
)

def expect_cue_error(raw):
    with assert_raises(CueError):
        translate(raw)

def test_errors():
    for raw in errors:
        yield expect_cue_error, raw
