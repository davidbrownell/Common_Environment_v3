# ----------------------------------------------------------------------
# |
# |  PluginBase.py
# |
# |  David Brownell <db@DavidBrownell.com>
# |      2019-03-19 15:59:06
# |
# ----------------------------------------------------------------------
# |
# |  Copyright David Brownell 2019
# |  Distributed under the Boost Software License, Version 1.0. See
# |  accompanying file LICENSE_1_0.txt or copy at
# |  http://www.boost.org/LICENSE_1_0.txt.
# |
# ----------------------------------------------------------------------
"""Contains the PluginBase object"""

import os

import six

import CommonEnvironment
from CommonEnvironment.FormatterImpl.Plugin import Plugin as FormatterPluginBase
from CommonEnvironment import Interface

# ----------------------------------------------------------------------
_script_fullpath                            = CommonEnvironment.ThisFullpath()
_script_dir, _script_name                   = os.path.split(_script_fullpath)
#  ----------------------------------------------------------------------

# ----------------------------------------------------------------------
class PluginBase(FormatterPluginBase):
    # ----------------------------------------------------------------------
    # |  Protected Methods
    @classmethod
    def EnumerateLines(cls, lines):
        """Enumerates all non-ignored lines in the collection of lines."""

        # Maintain compatibility with python 2.7
        for result in cls._EnumerateLinesImpl(lines):
            yield result

    # ----------------------------------------------------------------------
    @classmethod
    def EnumerateBlocks(cls, lines):
        for line_index, line, set_next_line_func in cls._EnumerateLinesImpl(
            lines,
            include_next_line_func=True,
        ):
            if not line.leaves:
                continue

            starting_line_index = line_index
            line_index += 1

            while line_index < len(lines) and lines[line_index].leaves:
                line_index += 1

            set_next_line_func(line_index)
            yield starting_line_index, lines[starting_line_index:line_index]

    # ----------------------------------------------------------------------
    @classmethod
    def IgnoreLine(cls, line):
        return line.comments and line.comments[0][1].value in ["# yapf: disable", "# fmt: off"]

    # ----------------------------------------------------------------------
    @staticmethod
    def FirstLeafValue(line):
        if not line.leaves:
            return None

        return line.leaves[0].value

    # ----------------------------------------------------------------------
    @staticmethod
    def LastLeafValue(line):
        """Return the last, non-whitespace, leaf on the line"""

        if not line.leaves:
            return None

        index = -1

        while line.leaves[index].value == "" and -index < len(line.leaves):
            index -= 1

        return line.leaves[index].value

    # ----------------------------------------------------------------------
    @staticmethod
    def ReplaceLines(lines, modification_map):
        """\
        Replaces lines with lines the modification_map.

        The modification_map is in the form:
            <line>: int -> <new_lines>: list
                or
            (<start_line>: int, <end_line>: int) -> <new_lines>: list
        """

        for line_info in reversed(list(six.iterkeys(modification_map))):
            new_lines = modification_map[line_info]
            
            if isinstance(line_info, tuple):
                start_line, end_line = line_info
            else:
                start_line = line_info
                end_line = start_line + 1

                new_lines[-1].comments = lines[start_line].comments

            for _ in range(end_line - start_line):
                del lines[start_line]

            for new_line in reversed(new_lines):
                lines.insert(start_line, new_line)

        return lines

    # ----------------------------------------------------------------------
    # ----------------------------------------------------------------------
    # ----------------------------------------------------------------------
    @classmethod
    def _EnumerateLinesImpl(
        cls,
        lines,
        include_next_line_func=False,
    ):
        nonlocals = CommonEnvironment.Nonlocals(
            index=0,
        )

        if include_next_line_func:
            # ----------------------------------------------------------------------
            def SetNextLine(index):
                nonlocals.index = index

            # ----------------------------------------------------------------------

            yield_func = lambda index, line: (index, line, SetNextLine)
        else:
            yield_func = lambda index, line: (index, line)

        disabled_command = None

        while nonlocals.index < len(lines):
            this_line = lines[nonlocals.index]
            this_index = nonlocals.index
            nonlocals.index += 1

            if cls.IgnoreLine(this_line):
                continue

            comments = cls._GetComments(this_line)
            if comments is not None:
                if disabled_command is None:
                    if "yapf: disable" in comments or "fmt: off" in comments:
                        disabled_command = comments
                        continue

                elif ("yapf" in disabled_command and "yapf: enable" in comments) or ("fmt" in disabled_command and "fmt: on" in comments):
                    disabled_command = None
                    continue

            if disabled_command is not None:
                continue

            yield yield_func(this_index, this_line)

    # ----------------------------------------------------------------------
    @staticmethod
    def _GetComments(line):
        # Gets the comments at the end of or within the provided line
        if line.comments:
            return line.comments[0][1].value

        for leaf in line.leaves:
            if leaf.value.startswith("#"):
                return leaf.value

        return None
