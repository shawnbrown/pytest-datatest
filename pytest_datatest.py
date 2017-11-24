# -*- coding: utf-8 -*-

import re
from _pytest._code.code import ReprEntry


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
        return None

    @staticmethod
    def _end_differences(lines):
        """Returns index of line after ValidationError differences have
        ended.
        """
        regex = re.compile('^E   \s*(?:\}|\]|\.\.\.)$')
        for index, line in enumerate(reversed(lines)):
            if regex.search(line) is not None:
                return len(lines) - index
        return None

    def _writelines(self, tw):
        for line in self.lines:
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
