# -*- coding: utf-8 -*-
from pytest import fixture

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

    def test_find_diff_start(self):
        lines = [
            '    def test_mydata(self):',
            '>       datatest.validate(1, 2)',
            'E       ValidationError: invalid data (1 difference): [',
            'E           Deviation(-1, 2),',
            'E       ]',
            '',
            'test_script.py:42: ValidationError',
        ]
        assert DatatestReprEntry._find_diff_start(lines) == 2, 'line index 2'

    def test_find_diff_start_no_message(self):
        lines = [
            '    def test_mydata(self):',
            '>       datatest.validate(1, 2)',
            'E       ValidationError: 1 difference: [',  # <- Diff count only,
            'E           Deviation(-1, 2),',             # no message.
            'E       ]',
            '',
            'test_script.py:42: ValidationError',
        ]
        assert DatatestReprEntry._find_diff_start(lines) == 2, 'line index 2'

    def test_find_diff_start_missing(self):
        """When beginning of differences can not be found, return None."""
        assert DatatestReprEntry._find_diff_start(['']) is None

    def test_find_diff_stop(self):
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
        assert DatatestReprEntry._find_diff_stop(lines) == 5, msg

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
        assert DatatestReprEntry._find_diff_stop(lines) == 6, msg

    def test_find_diff_stop_missing(self):
        """When end of differences can not be found, return None."""
        assert DatatestReprEntry._find_diff_stop(['']) is None

    def test_toterminal(self):
        """Should trim leading "E   " prefix for differences but still
        print in red.
        """
        lines = [
            '    def test_mydata(self):',
            '>       datatest.validate(1, 2)',
            'E       ValidationError: invalid data (1 difference): [',
            'E           Deviation(-1, 2),',
            'E       ]'
        ]

        original_entry = ReprEntry(
            lines,
            ReprFuncArgs([]),
            None,
            ReprFileLocation('test_script.py', 42, 'ValidationError'),
            'long',
        )

        wrapped_entry = DatatestReprEntry(original_entry)

        tw = DummyTerminalWriter()
        wrapped_entry.toterminal(tw)  # <- Call method.

        expected = [
            ('    def test_mydata(self):',
                {'bold': True, 'red': False}),
            ('>       datatest.validate(1, 2)',
                {'bold': True, 'red': False}),
            ('E       ValidationError: invalid data (1 difference): [',
                {'bold': True, 'red': True}),
            ('            Deviation(-1, 2),',
                {'bold': True, 'red': True}),
            ('        ]',
                {'bold': True, 'red': True}),
            ('',
                {}),
            ('test_script.py',
                {'bold': True, 'red': True}),
            (':42: ValidationError',
                {}),
        ]

        assert tw.all_lines == expected


class TestReprEntryReplacement(object):
    """The pytest-datatest plugin uses a pytest_runtest_makereport()
    hook wrapper to modify the printed error message when handling
    datatest.ValidationError failures.

    The plugin should automatically replace ReprEntry objects with
    DatatestReprEntry objects. This will have the effect of removing
    the "E" prefix from the difference rows shown in error messages.
    """

    def test_simple_failure(self, testdir):
        """Test simple failure case."""

        testdir.makepyfile('''
            from datatest import ValidationError
            from datatest import Invalid

            def test_validation():
                raise ValidationError([Invalid('a')], 'invalid data')
        ''')
        result = testdir.runpytest('-v')

        result.stdout.fnmatch_lines([
            "E       ValidationError: invalid data (1 difference): [",
            "            Invalid('a'),",  # <- No "E" prefix!
            "        ]",                  # <- No "E" prefix!
            "",
        ])

    def test_wrapped_failure(self, testdir):
        """Should also replace ReprEntry objects in wrapped functions too."""

        testdir.makepyfile('''
            from datatest import ValidationError
            from datatest import Invalid

            def wrapped():
                raise ValidationError([Invalid('a')], 'invalid data')

            def test_wrapped_call():
                wrapped()
        ''')
        result = testdir.runpytest('-v')

        result.stdout.fnmatch_lines([
            "E       ValidationError: invalid data (1 difference): [",
            "            Invalid('a'),",  # <- No "E" prefix!
            "        ]",                  # <- No "E" prefix!
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
                    raise ValidationError([Invalid('a')], 'invalid data')
        ''')
        result = testdir.runpytest('-v')

        result.stdout.fnmatch_lines([
            "E       ValidationError: invalid data (1 difference): [",
            "            Invalid('a'),",  # <- No "E" prefix!
            "        ]",                  # <- No "E" prefix!
            "",
        ])


class TestTruncation(object):
    @fixture(autouse=True)
    def long_error(self, testdir):
        testdir.makepyfile('''
            from datatest import ValidationError
            from datatest import Invalid

            def test_validation():
                raise ValidationError(
                    [Invalid(x) for x in range(10)],
                    description='invalid data',
                )
        ''')

    def test_default_truncation(self, testdir):
        result = testdir.runpytest('-v')
        result.stdout.fnmatch_lines([
            "E       ValidationError: invalid data (10 differences): [",
            "            Invalid(0),",  # <- No "E" prefix!
            "            Invalid(1),",  # <- No "E" prefix!
            "            Invalid(2),",  # <- No "E" prefix!
            "            Invalid(3),",  # <- No "E" prefix!
            "            Invalid(4),",  # <- No "E" prefix!
            "            Invalid(5),",  # <- No "E" prefix!
            "            Invalid(6),",  # <- No "E" prefix!
            "            Invalid(7),",  # <- No "E" prefix!
            "            ...",          # <- No "E" prefix!
            "E       ",
            "E       ...Full output truncated, use '-vv' to show",
            "",
        ])

    def test_increased_verbosity(self, testdir):
        result = testdir.runpytest('-vv')
        result.stdout.fnmatch_lines([
            "E       ValidationError: invalid data (10 differences): [",
            "            Invalid(0),",  # <- No "E" prefix!
            "            Invalid(1),",  # <- No "E" prefix!
            "            Invalid(2),",  # <- No "E" prefix!
            "            Invalid(3),",  # <- No "E" prefix!
            "            Invalid(4),",  # <- No "E" prefix!
            "            Invalid(5),",  # <- No "E" prefix!
            "            Invalid(6),",  # <- No "E" prefix!
            "            Invalid(7),",  # <- No "E" prefix!
            "            Invalid(8),",  # <- No "E" prefix!
            "            Invalid(9),",  # <- No "E" prefix!
            "        ]",                # <- No "E" prefix!
            "",
        ])


class TestMandatoryMarker(object):
    def test_marker_registered(self, testdir):
        result = testdir.runpytest('--markers')
        result.stdout.fnmatch_lines([
            '@pytest.mark.mandatory:*',
        ])

    @fixture
    def passing_cases(self, testdir):
        testdir.makepyfile('''
            import pytest

            @pytest.mark.mandatory
            def test_first():
                pass

            def test_second():
                pass
        ''')
        return testdir

    @fixture
    def failing_cases(self, testdir):
        testdir.makepyfile('''
            import pytest

            @pytest.mark.mandatory
            def test_first():
                raise Exception()

            def test_second():
                raise Exception()
        ''')
        return testdir

    def test_session_finished(self, passing_cases):
        result = passing_cases.runpytest()
        result.assert_outcomes(passed=2, failed=0)

    def test_session_stopped(self, failing_cases):
        """When a mandatory test fails, the session should stop
        immediately.
        """
        result = failing_cases.runpytest()
        result.assert_outcomes(passed=0, failed=1)  # 2nd test shouldn't run.

    def test_session_ignore_mandatory(self, failing_cases):
        """Using --ignore-mandatory should prevent mandatory failures
        from stopping the session early.
        """
        result = failing_cases.runpytest('--ignore-mandatory')
        result.assert_outcomes(passed=0, failed=2)

    def test_message_finished(self, passing_cases):
        result = passing_cases.runpytest()
        assert 'stopping early' not in result.stdout.str()

    def test_message_stopped(self, failing_cases):
        result = failing_cases.runpytest()
        result.stdout.fnmatch_lines([
            "stopping early, mandatory 'test_first' failed",
            "use '--ignore-mandatory' to continue testing",
        ])

    def test_message_ignore_mandatory(self, failing_cases):
        result = failing_cases.runpytest('--ignore-mandatory')
        assert 'stopping early' not in result.stdout.str()
