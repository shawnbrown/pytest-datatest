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
            '>       datatest.validate(1, 2)',
            'E       ValidationError: invalid data (1 difference): [',
            'E           Deviation(-1, 2),',
            'E       ]',
            '',
            'test_script.py:42: ValidationError',
        ]
        assert DatatestReprEntry._begin_differences(lines) == 2, 'line index 2'

        with pytest.raises(Exception):
            DatatestReprEntry._begin_differences([''])

    def test_end_differences(self):
        lines = [
            '    def test_mydata(self):',
            '>       datatest.validate(1, 2)',
            'E       ValidationError: invalid data (1 difference): [',
            'E           Deviation(-1, 2),',
            'E       ]',
            '',
            'test_script.py:42: ValidationError',
        ]
        msg = "First line after differences is empty string ('')."
        assert DatatestReprEntry._end_differences(lines) == 5, msg

        lines = [
            '    def test_mydata(self):',
            '>       datatest.validate(a, b)',
            'E       ValidationError: invalid data (4 differences): [',
            'E           Invalid(1),',
            'E           Invalid(2),',
            'E           ...',  # <- Truncation is indicated with an ellipsis.
            '',
            'test_script.py:42: ValidationError',
        ]
        msg = 'Should detect truncated differences, too.'
        assert DatatestReprEntry._end_differences(lines) == 6, msg

        with pytest.raises(Exception):
            DatatestReprEntry._end_differences([''])

    def test_toterminal(self):
        """Should trim leading "E   " prefix for differences but still
        print in red.
        """
        entry = DatatestReprEntry(ReprEntry(
            lines=['    def test_mydata(self):',
                   '>       datatest.validate(1, 2)',
                   'E       ValidationError: invalid data (1 difference): [',
                   'E           Deviation(-1, 2),',
                   'E       ]'],
            reprfuncargs=ReprFuncArgs([]),
            reprlocals=None,
            filelocrepr=ReprFileLocation('test_script.py', 42,
                                         'ValidationError'),
            style='long'
        ))

        tw = DummyTerminalWriter()
        entry.toterminal(tw)

        expected = [
            ('    def test_mydata(self):', {'bold': True, 'red': False}),
            ('>       datatest.validate(1, 2)', {'bold': True, 'red': False}),
            ('E       ValidationError: invalid data (1 difference): [',
                {'bold': True, 'red': True}),
            ('            Deviation(-1, 2),', {'bold': True, 'red': True}),
            ('        ]', {'bold': True, 'red': True}),
            ('', {}),
            ('test_script.py', {'bold': True, 'red': True}),
            (':42: ValidationError', {}),
        ]

        assert tw.all_lines == expected


class TestHookWrapper(object):
    def test_reprentry_replacement(self, testdir):
        """The pytest-datatest plugin uses a pytest_runtest_makereport()
        hook wrapper to modify the printed error message when handling
        datatest.ValidationError failures.

        The plugin should automatically replace ReprEntry objects
        with DatatestRepreEntry objects. This will have the effect
        of removing the "E" prefix from the difference rows shown in
        error messages.
        """

        testdir.makepyfile('''
            from datatest import ValidationError
            from datatest import Invalid

            def test_validation():
                raise ValidationError('invalid data', [Invalid('a', 'b')])
        ''')
        result = testdir.runpytest('-v')

        result.stdout.fnmatch_lines([
            "E       *ValidationError: invalid data (1 difference): [",
            "            Invalid('a', 'b'),",  # <- No "E" prefix!
            "        ]",                       # <- No "E" prefix!
            "",
        ])

    def test_truncation(self, testdir):
        testdir.makepyfile('''
            from datatest import ValidationError
            from datatest import Invalid

            def test_validation():
                raise ValidationError('invalid data', [Invalid('a', 'b')] * 10)
        ''')

        # Check for default truncation behavior.
        result = testdir.runpytest('-v')
        result.stdout.fnmatch_lines([
            "E       *ValidationError: invalid data (10 differences): [",
            "            Invalid('a', 'b'),",  # <- No "E" prefix!
            "            Invalid('a', 'b'),",  # <- No "E" prefix!
            "            Invalid('a', 'b'),",  # <- No "E" prefix!
            "            Invalid('a', 'b'),",  # <- No "E" prefix!
            "            Invalid('a', 'b'),",  # <- No "E" prefix!
            "            Invalid('a', 'b'),",  # <- No "E" prefix!
            "            Invalid('a', 'b'),",  # <- No "E" prefix!
            "            Invalid('a', 'b'),",  # <- No "E" prefix!
            "            ...",                 # <- No "E" prefix!
            "E       ",
            "E       ...Full output truncated, use '-vv' to show",
            "",
        ])

        # Check same test with increased verbosity.
        result = testdir.runpytest('-vv')
        result.stdout.fnmatch_lines([
            "E       *ValidationError: invalid data (10 differences): [",
            "            Invalid('a', 'b'),",  # <- No "E" prefix!
            "            Invalid('a', 'b'),",  # <- No "E" prefix!
            "            Invalid('a', 'b'),",  # <- No "E" prefix!
            "            Invalid('a', 'b'),",  # <- No "E" prefix!
            "            Invalid('a', 'b'),",  # <- No "E" prefix!
            "            Invalid('a', 'b'),",  # <- No "E" prefix!
            "            Invalid('a', 'b'),",  # <- No "E" prefix!
            "            Invalid('a', 'b'),",  # <- No "E" prefix!
            "            Invalid('a', 'b'),",  # <- No "E" prefix!
            "            Invalid('a', 'b'),",  # <- No "E" prefix!
            "        ]",                       # <- No "E" prefix!
            "",
        ])

    def test_with_unittester(self, testdir):
        """Test ReprEntry replacement with unittest-style tests."""

        testdir.makepyfile('''
            from datatest import DataTestCase
            from datatest import ValidationError
            from datatest import Invalid

            class TestValidation(DataTestCase):
                def test_validation(self):
                    raise ValidationError('invalid data', [Invalid('a', 'b')])
        ''')
        result = testdir.runpytest('-v')

        result.stdout.fnmatch_lines([
            "E       *ValidationError: invalid data (1 difference): [",
            "            Invalid('a', 'b'),",  # <- No "E" prefix!
            "        ]",                       # <- No "E" prefix!
            "",
        ])
