# -*- coding: utf-8 -*-
import pytest

from _pytest._code.code import ReprEntry
from _pytest._code.code import ReprFuncArgs
from _pytest._code.code import ReprFileLocation

from pytest_datatest import DatatestReprEntry
from pytest_datatest import _find_validationerror_start
from pytest_datatest import _format_reprentry_lines
from pytest_datatest import pytest_runtest_logreport


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


class TestFindValidationErrorStart(object):
    def test_fully_qualified_class_name(self):
        """First error line uses 'datatest.ValidationError'."""
        lines = [
            '    def test_mydata(self):',
            '>       validate(1, 2)',
            'E       datatest.ValidationError: invalid data (1 difference): [',
            'E           Deviation(-1, 2),',
            'E       ]',
            '',
            'test_script.py:42: ValidationError',
        ]
        position = _find_validationerror_start(lines)
        assert position == 2, 'expects start at index 2'

    def test_unqualified_class_name(self):
        """First error line uses 'ValidationError'."""
        lines = [
            '    def test_mydata(self):',
            '>       validate(1, 2)',
            'E       ValidationError: invalid data (1 difference): [',
            'E           Deviation(-1, 2),',
            'E       ]',
            '',
            'test_script.py:42: ValidationError',
        ]
        position = _find_validationerror_start(lines)
        assert position == 2, 'expects start at index 2'

    def test_no_validationerror_found(self):
        """Check AssertionError, not ValidationError."""
        lines = [
            "    def test_foobar():",
            ">       assert 'foo' == 'bar'",
            "E       AssertionError: assert 'foo' == 'bar'",
            "E         - bar",
            "E         + foo",
            "",
            "test_script.py:42: AssertionError",
        ]
        position = _find_validationerror_start(lines)
        assert position == -1, 'not found, should be -1'

    def test_nested_validationerror_string(self):
        """Check that there are no false positives for lines that look
        like ValidationErrors but occur after the first line with a
        fail_marker.
        """
        lines = [
            r"    def test_bar():",
            r">       assert 'foo' == '''",
            r"    \b\b\b\bdatatest.ValidationError: invalid data (1 difference): [",
            r"    '''",
            r"E       AssertionError: assert 'foo' == '\n\x08\x08\x...ference): [\n'",
            r"E         + foo",
            r"E         - ",
            r"E       datatest.ValidationError: invalid data (1 difference): [",
            r"",
            r"test_script.py:42: AssertionError",
        ]
        position = _find_validationerror_start(lines)
        assert position == -1, 'not found, should be -1'


class TestFormatReprEntryLines(object):
    def test_formatting(self):
        lines = [
            '    def test_mydata(self):',
            '>       validate(1, 2)',
            'E       datatest.ValidationError: invalid data (1 difference): [',
            'E           Deviation(-1, 2),',
            'E       ]',
            '',
            'test_script.py:42: ValidationError',
        ]
        position = _find_validationerror_start(lines)
        formatted = _format_reprentry_lines(lines, position)

        expected = [
            '    def test_mydata(self):',
            '>       validate(1, 2)',
            'E       ValidationError: invalid data (1 difference): [',
            '            Deviation(-1, 2),',  # <- No "E" prefix!
            '        ]',                      # <- No "E" prefix!
            '',
            'test_script.py:42: ValidationError',
        ]
        assert formatted == expected

    def test_nongreedy_matching(self):
        """Should stop removing `fail_marker` characters after the
        first line without a matching `fail_marker`.
        """
        lines = [
            '    def test_mydata(self):',
            '>       validate(1, 2)',
            'E       datatest.ValidationError: invalid data (1 difference): [',
            'E           Deviation(-1, 2),',
            'E       ]',
            '',
            'Etest_script.py:42: ValidationError',  # <- Starts with fail_marker match!
        ]
        position = _find_validationerror_start(lines)
        formatted = _format_reprentry_lines(lines, position)

        expected = [
            '    def test_mydata(self):',
            '>       validate(1, 2)',
            'E       ValidationError: invalid data (1 difference): [',
            '            Deviation(-1, 2),',        # <- No "E" prefix!
            '        ]',                            # <- No "E" prefix!
            '',
            'Etest_script.py:42: ValidationError',  # <- Should be unchanged!
        ]
        # Comparing the last two lines is enough.
        assert formatted[-2:] == expected[-2:]


class TestPytestRuntestLogreport(object):
    pass


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
    @pytest.fixture(autouse=True)
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


class TestXdistPlugin(object):
    """Check behavior using the `pytest-xdist` plugin. Communication
    between xdist workers and pytest are managed with JSON messages.
    Unlike non-xdist test sessions, results are processed using the
    _pytest.reports._report_kwargs_from_json() function.
    """

    @pytest.fixture
    def passing_case(self, testdir):
        testdir.makepyfile('''
            from datatest import validate

            def test_one():
                validate('foo', 'foo')

            def test_two():
                validate('bar', 'bar')
        ''')
        return testdir

    @pytest.fixture
    def failing_case(self, testdir):
        testdir.makepyfile('''
            from datatest import validate

            def test_one():
                validate('foo', 'baz')

            def test_two():
                validate('bar', 'baz')
        ''')
        return testdir

    def test_passing(self, passing_case):
        """Run passing cases with xdist option '-n 1'."""
        result = passing_case.runpytest('-n', '1')
        result.assert_outcomes(passed=2, failed=0)

    @pytest.mark.xfail
    def test_failing(self, failing_case):
        """Run failing cases with xdist option '-n 1'."""
        result = failing_case.runpytest('-n', '1')
        result.assert_outcomes(passed=0, failed=2)


class TestMandatoryMarker(object):
    def test_marker_registered(self, testdir):
        result = testdir.runpytest('--markers')
        result.stdout.fnmatch_lines([
            '@pytest.mark.mandatory:*',
        ])

    @pytest.fixture
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

    @pytest.fixture
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
