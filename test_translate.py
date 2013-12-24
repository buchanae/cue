from nose.tools import eq_

from translate import translate


tests = (

    ('n <- 1', 'n = 1'),

    ('n = 1', 'n = 1'),

    ('1 + 2', '(1 + 2)'),

    ('1 + 2 + 3', '((1 + 2) + 3)'),

    ('(1 + 2) + 3', '((1 + 2) + 3)'),
    #print translate('n <- function() return(1, 2, 3, 4)')
    #'1, 2',
)


def check_translation(raw, expected):
    eq_(translate(raw).lstrip('\n'), expected)

def test_all():
    for raw, expected in tests:
        yield check_translation, raw, expected
