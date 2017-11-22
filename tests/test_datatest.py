# -*- coding: utf-8 -*-

from _pytest._code.code import ReprEntry
from _pytest._code.code import ReprFuncArgs
from _pytest._code.code import ReprFileLocation

from pytest_datatest import DatatestReprEntry


def test_DatatestReprEntry(testdir):
    lines = [
        '    def test_foo():',
        '>       assert 1 == 2',
        'E       assert 1 == 2',
    ]
    reprfuncargs = ReprFuncArgs([])
    reprlocals = None
    reprfileloc = ReprFileLocation('test_script.py', 9, 'AssertionError')
    style = 'long'

    original = ReprEntry(lines, reprfuncargs, reprlocals, reprfileloc, style)
    wrapped = DatatestReprEntry(original)

    assert isinstance(wrapped, ReprEntry), 'should be derived from ReprEntry'
    assert wrapped.lines == original.lines
    assert wrapped.reprfuncargs == original.reprfuncargs
    assert wrapped.reprlocals == original.reprlocals
    assert wrapped.reprfileloc == original.reprfileloc
    assert wrapped.style == original.style
