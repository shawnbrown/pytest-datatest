# -*- coding: utf-8 -*-

import re
from _pytest._code.code import ReprEntry
from pytest import hookimpl
from datatest import ValidationError


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
    def _begin_differences(lines):
        """Returns index of line where ValidationError differences begin."""
        regex = re.compile('^E   .+\(\d+ difference[s]?\): [\[{]$')
        for index, line in enumerate(lines):
            if regex.search(line) is not None:
                return index
        raise Exception('cannot find beginning of ValidationError differences')

    @staticmethod
    def _end_differences(lines):
        """Returns index of line after ValidationError differences have
        ended.
        """
        regex = re.compile('^E   \s*(?:\}|\]|\.\.\.)$')
        for index, line in enumerate(reversed(lines)):
            if regex.search(line) is not None:
                return len(lines) - index
        raise Exception('cannot find end of ValidationError differences')

    def _writelines(self, tw):
        """If row contains a difference item, trim the "E   " prefix
        and indent with four spaces (but still print in red).
        """
        lines = list(self.lines)

        begin_differences = self._begin_differences(lines)
        end_differences = self._end_differences(lines)

        for index, line in enumerate(lines):  # Trim the "E   " prefix
            red = line.startswith('E   ')     # and adjust indent-level.
            if begin_differences < index < end_differences:
                line = line[1:].strip()
                if line != ']' and line != '}':
                    line = '    {0}'.format(line)
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


@hookimpl(tryfirst=True, hookwrapper=True)
def pytest_runtest_makereport(item, call):
    """Hook wrapper to replace ReprEntry instances for ValidationError
    exceptons.
    """
    if (call.when == 'call'
            and call.excinfo
            and call.excinfo.errisinstance(ValidationError)):

        outcome = yield
        result = outcome.get_result()

        reprentries = result.longrepr.reprtraceback.reprentries
        new_reprentries = [DatatestReprEntry(entry) for entry in reprentries]
        result.longrepr.reprtraceback.reprentries = new_reprentries

    else:
        outcome = yield
