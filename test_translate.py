import hashlib
import os

from nose.tools import assert_raises, eq_

from translate import translate, translate_cue_code, CueError, run_cue


CACHE_DIR = '.cue_output_test_cache'

if not os.path.exists(CACHE_DIR):
    os.mkdir(CACHE_DIR)


# TODO consider comparing to ast.dump() so that you know tree is exact
#      not just syntax

translations = (

    ('(1)', '1'),

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

    ('foo(bar(x), 2)', 'foo(bar(x), 2)'),

    ('if (1) 2', 'if 1:\n    2'),

    ('if (1) { 2; 2 }', 'if 1:\n    2\n    2'),

    ('1 < 2', '(1 < 2)'),

    ('1 > 2', '(1 > 2)'),

    ('1 <= 2', '(1 <= 2)'),

    ('1 >= 2', '(1 >= 2)'),

    ('1 == 2', '(1 == 2)'),

    ('1 != 2', '(1 != 2)'),

    ("'foo'", "'foo'"),

    ("foo('bar')", "foo('bar')"),

    ('!1', '(not 1)'),

    ('1 && 1', '(1 and 1)'),

    ('1 || 1', '(1 or 1)'),

    ('1 && 2 || 3', '((1 and 2) or 3)'),

    ('1 %in% foo', '(1 in foo)'),

    ('foo(1)(bar())', 'foo(1)(bar())'),
)


def check_translation(raw, expected):
    # Cache the cue output because it's fairly slow to start a cue process
    # for every test
    #
    # TODO include some kind of cue version in this hash, so that the cache
    #      is invalidated by updates to cue.r and/or the cue runner
    m = hashlib.md5()
    m.update(raw)
    hashcode = m.hexdigest()
    cache_path = os.path.join(CACHE_DIR, hashcode)

    if os.path.exists(cache_path):
        cue_code = open(cache_path).read()
    else:
        cue_code = run_cue(raw)
        with open(cache_path, 'w') as fh:
            fh.write(cue_code)

    eq_(translate_cue_code(cue_code).lstrip('\n'), expected)

def test_translations():
    for raw, expected in translations:
        yield check_translation, raw, expected


errors = (
    '1, 2',

    '1 < 2 < 4',

    # TODO this doesn't actually fail because it's valid R syntax
    #      but it throws an error when eval'd
    #      Error in return(1, 2, 3) : multi-argument returns are not permitted
    #'foo <- function() return(1, 2, 3)',
)

def expect_cue_error(raw):
    with assert_raises(CueError):
        translate(raw)

def test_errors():
    for raw in errors:
        yield expect_cue_error, raw
