from nose.tools import eq_

from translate import translate


tests = (
    ('1 + 2', '1 + 2'),

    ('n <- 1', 'n = 1'),

    ('n = 1', 'n = 1'),

    ('1 + 2 + 3', '1 + 2 + 3'),

    ('(1 + 2) + 3', '(1 + 2) + 3'),
)


def test_all():
    for raw, expected in tests:
        yield eq_, translate(raw), expected
