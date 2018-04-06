# -*- coding: utf-8 -*-
"""
A pytest plugin for test driven data-wrangling with datatest.

This plugin is bundled with the ``datatest`` package however,
it's developed separately as ``pytest_datatest``.

IMPORTANT: Users of Datatest should only install ``datatest``
itself, not this separate package. But developers of the Datatest
project should install both ``datatest`` and ``pytest_datatest``.

When both packages are installed, ``pytest_datatest`` is used
in place of the bundled version.

This is done for a few reasons:

1. It's desirable for the plugin to follow the Pytest project's
   plugin submission guidelines. Even if this plugin is never
   submitted to the pytest-dev organisation, it's still good
   practice to follow the guidelines used by official plugins.
2. Datatest should work as expected out-of-the-box and the extra
   code (a single script) is easy to bundle and it's so small
   that there is no impact on user experience.
3. Datatest supports more version of Python than does Pytest
   or tox. It is helpful to keep the testing of the larger
   datatest project separate from the testing of the pytest
   plugin component.
"""

import re
import warnings
from _pytest._code.code import ReprEntry
from _pytest.assertion.truncate import _should_truncate_item
from _pytest.assertion.truncate import DEFAULT_MAX_LINES
from _pytest.assertion.truncate import DEFAULT_MAX_CHARS
from _pytest.assertion.truncate import USAGE_MSG
from pytest import hookimpl
from datatest import ValidationError


version = '0.1.1'

version_info = (0, 1, 1)


if __name__ == 'pytest_datatest':
    try:
        from datatest._pytest_plugin import version_info \
                as bundled_version_info
    except ImportError:
        bundled_version_info = (0, 0, 0)

    if version_info < bundled_version_info:
        _warning_msg = (
            'The installed version of the "pytest_datatest" plugin is '
            'older than the bundled version included with "datatest". '
            'Uninstall "pytest_datatest" to automatically enable the '
            'newer version.'
        )
        warnings.warn(_warning_msg)


class DatatestReprEntry(ReprEntry):
    """Wrapper for ReprEntry to change behavior of toterminal() method."""
    def __init__(self, entry):
        if not isinstance(entry, ReprEntry):
            cls_name = entry.__class__.__name__
            raise ValueError('expected ReprEntry, got {0}'.format(cls_name))

        super(DatatestReprEntry, self).__init__(
            getattr(entry, 'lines', []),
            getattr(entry, 'reprfuncargs', None),
            getattr(entry, 'reprlocals', None),
            getattr(entry, 'reprfileloc', None),
            getattr(entry, 'style', None),
        )

    @staticmethod
    def _find_diff_start(lines):
        """Returns index of line where ValidationError differences begin."""
        regex = re.compile('^E   .+\(\d+ difference[s]?\): [\[{]$')
        for index, line in enumerate(lines):
            if regex.search(line) is not None:
                return index
        return None

    @staticmethod
    def _find_diff_stop(lines):
        """Returns index of line after ValidationError differences have
        ended.
        """
        regex = re.compile('^E   \s*(?:\}|\]|\.\.\.)$')
        for index, line in enumerate(reversed(lines)):
            if regex.search(line) is not None:
                return len(lines) - index
        return None

    def _writelines(self, tw):
        """If row contains a difference item, trim the "E   " prefix
        and indent with four spaces (but still print in red).
        """
        lines = list(self.lines)

        diff_start = self._find_diff_start(lines)
        diff_stop = self._find_diff_stop(lines)

        if isinstance(diff_start, int) and isinstance(diff_stop, int):
            lines[diff_start] = lines[diff_start].replace(
                'datatest.ValidationError', 'ValidationError')

            for index, line in enumerate(lines):
                red = line.startswith('E   ')
                if diff_start < index < diff_stop:
                    line = ' ' + line[1:]  # Replace "E" prefix with space.
                tw.line(line, bold=True, red=red)
        else:
            for line in lines:
                red = line.startswith('E   ')
                tw.line(line, bold=True, red=red)

    def toterminal(self, tw):
        if self.style == 'short':
            self.reprfileloc.toterminal(tw)
            self._writelines(tw)  # <- Calls tw.line() method.
            return

        if self.reprfuncargs:
            self.reprfuncargs.toterminal(tw)

        self._writelines(tw)  # <- Calls tw.line() method.

        if self.reprlocals:
            tw.line('')
            self.reprlocals.toterminal(tw)

        if self.reprfileloc:
            if self.lines:
                tw.line('')
            self.reprfileloc.toterminal(tw)


def _should_truncate(line_count, char_count):
    return (line_count > DEFAULT_MAX_LINES) or (char_count > DEFAULT_MAX_CHARS)


_truncation_notice = '...Full output truncated, {0}'.format(USAGE_MSG)


@hookimpl(tryfirst=True, hookwrapper=True)
def pytest_runtest_makereport(item, call):
    """Hook wrapper to replace ReprEntry instances for ValidationError
    exceptons.
    """
    if call.when == 'call':

        datafail = call.excinfo and call.excinfo.errisinstance(ValidationError)

        # Pytest-style truncation must be applied before `yield`.
        if datafail and _should_truncate_item(item):
            call.excinfo.value._should_truncate = _should_truncate
            call.excinfo.value._truncation_notice = _truncation_notice

        outcome = yield

        # Check for failure again--unittest-style failures only appear
        # after `yield`.
        datafail = datafail or \
            call.excinfo and call.excinfo.errisinstance(ValidationError)

        if datafail:
            result = outcome.get_result()
            entries = result.longrepr.reprtraceback.reprentries
            new_entries = [DatatestReprEntry(entry) for entry in entries]
            result.longrepr.reprtraceback.reprentries = new_entries

    else:
        outcome = yield
