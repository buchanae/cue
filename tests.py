from nose.tools import eq_

from translate import translate


tests = (
    ('1 + 2', '1 + 2'),

    ('n <- 1', 'n = 1'),

    ('n = 1', 'n = 1'),

    ('1 + 2 + 3', '1 + 2 + 3'),

    ('(1 + 2) + 3', '(1 + 2) + 3'),
    print translate('n <- function() return(1, 2, 3, 4)')
    '1, 2',
)


def test_all():
    for raw, expected in tests:
        yield eq_, translate(raw), expected
