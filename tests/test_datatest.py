# -*- coding: utf-8 -*-

from _pytest._code.code import ReprEntry
from _pytest._code.code import ReprFuncArgs
from _pytest._code.code import ReprFileLocation

from pytest_datatest import DatatestReprEntry


class DummyTerminalWriter(object):
    """Helper class for testing calls to line() and write() methods."""
    def __init__(self):
        self.all_lines = []

    def line(self, line, **kwds):
        self.all_lines.append((line, kwds))

    def write(self, line, **kwds):
        self.all_lines.append((line, kwds))


class TestDatatestReprEntry(object):
    def test_instantiation(self):
        lines = [
            '    def test_foo():',
            '>       assert 1 == 2',
            'E       assert 1 == 2',
        ]
        reprfuncargs = ReprFuncArgs([])
        reprlocals = None
        reprfileloc = ReprFileLocation('test_script.py', 9, 'AssertionError')
        style = 'long'

        original = ReprEntry(
            lines, reprfuncargs, reprlocals, reprfileloc, style)
        wrapped = DatatestReprEntry(original)

        assert isinstance(wrapped, ReprEntry), 'should derive from ReprEntry'
        assert wrapped.lines == original.lines
        assert wrapped.reprfuncargs == original.reprfuncargs
        assert wrapped.reprlocals == original.reprlocals
        assert wrapped.reprfileloc == original.reprfileloc
        assert wrapped.style == original.style

    def test_begin_differences(self):
        lines = [
            '    def test_mydata(self):',
            '        import datatest',
            '>       datatest.validate(1, 2)',
            'E       ValidationError: invalid data (1 difference): [',
            'E           Deviation(-1, 2),',
            'E       ]',
            '',
            'test_script.py:42: ValidationError',
        ]
        assert DatatestReprEntry._begin_differences(lines) == 3, 'line index 3'

    def test_toterminal(self):
        entry = DatatestReprEntry(ReprEntry(
            lines=['    def test_foo():',
                   '>       assert 1 == 2',
                   'E       assert 1 == 2'],
            reprfuncargs=ReprFuncArgs([]),
            reprlocals=None,
            filelocrepr=ReprFileLocation('test_script.py', 9,
                                         'AssertionError'),
            style='long'
        ))

        tw = DummyTerminalWriter()
        entry.toterminal(tw)

        expected = [
            ('    def test_foo():', {'bold': True, 'red': False}),
            ('>       assert 1 == 2', {'bold': True, 'red': False}),
            ('E       assert 1 == 2', {'bold': True, 'red': True}),
            ('', {}),
            ('test_script.py', {'bold': True, 'red': True}),
            (':9: AssertionError', {}),
        ]

        assert tw.all_lines == expected
