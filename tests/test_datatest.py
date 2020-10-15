# -*- coding: utf-8 -*-
import pytest

from pytest_datatest import _find_validationerror_position
from pytest_datatest import _formatted_lines_generator


class DummyTerminalWriter(object):
    """Helper class for testing calls to line() and write() methods."""
    def __init__(self):
        self.all_lines = []

    def line(self, line, **kwds):
        self.all_lines.append((line, kwds))

    def write(self, line, **kwds):
        self.all_lines.append((line, kwds))


class TestFindValidationErrorPosition(object):
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
        position = _find_validationerror_position(lines)
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
        position = _find_validationerror_position(lines)
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
        position = _find_validationerror_position(lines)
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
        position = _find_validationerror_position(lines)
        assert position == -1, 'not found, should be -1'


class TestFormattedLinesGenerator(object):
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
        position = _find_validationerror_position(lines)
        formatted = _formatted_lines_generator(lines, position)

        expected = [
            '    def test_mydata(self):',
            '>       validate(1, 2)',
            'E       ValidationError: invalid data (1 difference): [',
            '            Deviation(-1, 2),',  # <- No "E" prefix!
            '        ]',                      # <- No "E" prefix!
            '',
            'test_script.py:42: ValidationError',
        ]
        assert list(formatted) == expected

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
        position = _find_validationerror_position(lines)
        formatted = _formatted_lines_generator(lines, position)

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
        assert list(formatted)[-2:] == expected[-2:]


class TestReprEntryLinesFormatting(object):
    """The pytest-datatest plugin uses the pytest_runtest_logreport()
    hook to format the ReprEntry.lines for datatest.ValidationError
    failures.

    This will have the effect of removing the "E" prefix from the
    difference rows shown in error messages.
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
            "        ",
            "        ...Full output truncated, use '-vv' to show",
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
