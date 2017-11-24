# -*- coding: utf-8 -*-

import pytest
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

        with pytest.raises(Exception):
            DatatestReprEntry._begin_differences([''])

    def test_end_differences(self):
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
        msg = 'First line after differences is index 6.'
        assert DatatestReprEntry._end_differences(lines) == 6, msg

        lines = [
            '    def test_mydata(self):',
            '        import datatest',
            '>       datatest.validate(a, b)',
            'E       ValidationError: invalid data (4 differences): [',
            'E           Invalid(1),',
            'E           Invalid(2),',
            'E           ...',  # <- Truncation indicated with ellipsis.
            '',
            'test_script.py:42: ValidationError',
        ]
        msg = 'Should detect truncated differences, too.'
        assert DatatestReprEntry._end_differences(lines) == 7, msg

        with pytest.raises(Exception):
            DatatestReprEntry._end_differences([''])

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
