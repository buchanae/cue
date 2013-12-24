from nose.tools import eq_

from translate import translate


tests = (

    ('n <- 1', 'n = 1'),

    ('n = 1', 'n = 1'),

    ('1 + 2', '(1 + 2)'),

    # TODO I don't like how unparse adds the extra parens
    ('1 + 2 + 3', '((1 + 2) + 3)'),

    ('(1 + 2) + 3', '((1 + 2) + 3)'),

    # TODO unparse should add a newline to be nice
    ('funcname <- function() 1', 'def funcname():\n    1'),

    ('funcname <- function() return(1)', 'def funcname():\n    return 1'),

    ('funcname <- function() return()', 'def funcname():\n    return'),

    ('funcname <- function(x) return()', 'def funcname(x):\n    return'),

    #print translate('n <- function() return(1, 2, 3, 4)')
    #'1, 2',
)


def check_translation(raw, expected):
    eq_(translate(raw).lstrip('\n'), expected)

def test_all():
    for raw, expected in tests:
        yield check_translation, raw, expected
