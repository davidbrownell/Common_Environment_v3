# ----------------------------------------------------------------------
# |
# |  DebugPlugin_UnitTest.py
# |
# |  David Brownell <db@DavidBrownell.com>
# |      2019-07-09 19:09:33
# |
# ----------------------------------------------------------------------
# |
# |  Copyright David Brownell 2019
# |  Distributed under the Boost Software License, Version 1.0. See
# |  accompanying file LICENSE_1_0.txt or copy at
# |  http://www.boost.org/LICENSE_1_0.txt.
# |
# ----------------------------------------------------------------------
"""Unit test for DebugPlugin.py"""

import os
import sys
import textwrap
import unittest

import six

import CommonEnvironment
from CommonEnvironment.CallOnExit import CallOnExit

from TestImpl import TestImpl

# ----------------------------------------------------------------------
_script_fullpath                            = CommonEnvironment.ThisFullpath()
_script_dir, _script_name                   = os.path.split(_script_fullpath)
# ----------------------------------------------------------------------

sys.path.insert(0, os.path.join(_script_dir, "..", ".."))
with CallOnExit(lambda: sys.path.pop(0)):
    from PythonFormatterImpl.DebugPlugin import Plugin as DebugPlugin

# ----------------------------------------------------------------------
class StandardSuite(TestImpl):
    # ----------------------------------------------------------------------
    def Test(self, expected, flags):
        if sys.version_info[0] == 2:
            typ = type(self)

            if not hasattr(typ, "_displayed_message"):
                sys.stdout.write("This script does not run with python2.\n")
                setattr(typ, "_displayed_message", True)

            self.assertTrue(True)
            return

        # Avoid import problems on python27
        import unittest.mock

        with unittest.mock.patch("PythonFormatterImpl.DebugPlugin.sys.stdout") as mocked:
            sink = six.moves.StringIO()

            mocked.write = lambda content: sink.write(content.rstrip(" "))

            content = textwrap.dedent(
                """\
                a = 10


                def Func():
                    pass
                """,
            )

            super(StandardSuite, self).Test(
                content,
                content,
                "Debug",
                flags=flags,
            )

            sink = sink.getvalue()
            self.assertEqual(sink, expected)

    # ----------------------------------------------------------------------
    def test_Standard(self):
        self.Test(
            textwrap.dedent(
                """\

                # ----------------------------------------------------------------------
                # ----------------------------------------------------------------------
                # ----------------------------------------------------------------------
                # |
                # |  PreprocessTokens
                # |
                # ----------------------------------------------------------------------
                # ----------------------------------------------------------------------
                # ----------------------------------------------------------------------
                Line 1) a = 10

                    Token   0) a                           0  expr_stmt
                    Token   1) =                           1  expr_stmt
                    Token   2)                             1  atom
                    Token   3) 10                          0  atom
                    Token   4)                             0  atom
                    Token   5) NEWLINE                     0  NEWLINE

                Line 2)

                    Token   0) NEWLINE                     0  NEWLINE

                Line 3)

                    Token   0) NEWLINE                     0  NEWLINE

                Line 4) def Func():

                    Token   0) def                         0  funcdef
                    Token   1) Func                        1  funcdef
                    Token   2) (                           0  parameters
                    Token   3) )                           0  parameters
                    Token   4) :                           0  funcdef
                    Token   5) NEWLINE                     0  NEWLINE

                Line 5) pass

                    Token   0) INDENT                      0  INDENT
                    Token   1) pass                        0  simple_stmt
                    Token   2) NEWLINE                     0  NEWLINE


                # ----------------------------------------------------------------------
                # ----------------------------------------------------------------------
                # ----------------------------------------------------------------------
                # |
                # |  PreprocessBlocks
                # |
                # ----------------------------------------------------------------------
                # ----------------------------------------------------------------------
                # ----------------------------------------------------------------------
                Block 1) 1 line

                    Line 1) a = 10

                Block 2) 1 line

                    Line 1)

                def Func():

                Block 3) 1 line

                    Line 1) pass


                # ----------------------------------------------------------------------
                # ----------------------------------------------------------------------
                # ----------------------------------------------------------------------
                # |
                # |  DecorateTokens
                # |
                # ----------------------------------------------------------------------
                # ----------------------------------------------------------------------
                # ----------------------------------------------------------------------
                Line 1) a = 10

                    Token   0) a                           0  expr_stmt
                    Token   1) =                           1  expr_stmt
                    Token   2)                             1  atom
                    Token   3) 10                          0  atom
                    Token   4)                             0  atom
                    Token   5) NEWLINE                     0  NEWLINE

                Line 2)

                    Token   0) NEWLINE                     0  NEWLINE

                Line 3)

                    Token   0) NEWLINE                     0  NEWLINE

                Line 4) def Func():

                    Token   0) def                         0  funcdef
                    Token   1) Func                        1  funcdef
                    Token   2) (                           0  parameters
                    Token   3) )                           0  parameters
                    Token   4) :                           0  funcdef
                    Token   5) NEWLINE                     0  NEWLINE

                Line 5) pass

                    Token   0) INDENT                      0  INDENT
                    Token   1) pass                        0  simple_stmt
                    Token   2) NEWLINE                     0  NEWLINE


                # ----------------------------------------------------------------------
                # ----------------------------------------------------------------------
                # ----------------------------------------------------------------------
                # |
                # |  DecorateBlocks
                # |
                # ----------------------------------------------------------------------
                # ----------------------------------------------------------------------
                # ----------------------------------------------------------------------
                Block 1) 1 line

                    Line 1) a = 10

                Block 2) 1 line

                    Line 1) def Func():

                Block 3) 1 line

                    Line 1) pass


                # ----------------------------------------------------------------------
                # ----------------------------------------------------------------------
                # ----------------------------------------------------------------------
                # |
                # |  PostprocessTokens
                # |
                # ----------------------------------------------------------------------
                # ----------------------------------------------------------------------
                # ----------------------------------------------------------------------
                Line 1) a = 10

                    Token   0) a                           0  expr_stmt
                    Token   1) =                           1  expr_stmt
                    Token   2)                             1  atom
                    Token   3) 10                          0  atom
                    Token   4)                             0  atom
                    Token   5) NEWLINE                     0  NEWLINE

                Line 2)

                    Token   0) NEWLINE                     0  NEWLINE

                Line 3)

                    Token   0) NEWLINE                     0  NEWLINE

                Line 4) def Func():

                    Token   0) def                         0  funcdef
                    Token   1) Func                        1  funcdef
                    Token   2) (                           0  parameters
                    Token   3) )                           0  parameters
                    Token   4) :                           0  funcdef
                    Token   5) NEWLINE                     0  NEWLINE

                Line 5) pass

                    Token   0) INDENT                      0  INDENT
                    Token   1) pass                        0  simple_stmt
                    Token   2) NEWLINE                     0  NEWLINE


                # ----------------------------------------------------------------------
                # ----------------------------------------------------------------------
                # ----------------------------------------------------------------------
                # |
                # |  PostprocessBlocks
                # |
                # ----------------------------------------------------------------------
                # ----------------------------------------------------------------------
                # ----------------------------------------------------------------------
                Block 1) 1 line

                    Line 1) a = 10

                Block 2) 1 line

                    Line 1) def Func():

                Block 3) 1 line

                    Line 1) pass

                """,
            ),
            DebugPlugin.Flag.AllFlags,
        )

    # ----------------------------------------------------------------------
    def test_PreprocessTokens(self):
        self.Test(
            textwrap.dedent(
                """\

                # ----------------------------------------------------------------------
                # ----------------------------------------------------------------------
                # ----------------------------------------------------------------------
                # |
                # |  PreprocessTokens
                # |
                # ----------------------------------------------------------------------
                # ----------------------------------------------------------------------
                # ----------------------------------------------------------------------
                Line 1) a = 10

                    Token   0) a                           0  expr_stmt
                    Token   1) =                           1  expr_stmt
                    Token   2)                             1  atom
                    Token   3) 10                          0  atom
                    Token   4)                             0  atom
                    Token   5) NEWLINE                     0  NEWLINE

                Line 2)

                    Token   0) NEWLINE                     0  NEWLINE

                Line 3)

                    Token   0) NEWLINE                     0  NEWLINE

                Line 4) def Func():

                    Token   0) def                         0  funcdef
                    Token   1) Func                        1  funcdef
                    Token   2) (                           0  parameters
                    Token   3) )                           0  parameters
                    Token   4) :                           0  funcdef
                    Token   5) NEWLINE                     0  NEWLINE

                Line 5) pass

                    Token   0) INDENT                      0  INDENT
                    Token   1) pass                        0  simple_stmt
                    Token   2) NEWLINE                     0  NEWLINE

                """,
            ),
            DebugPlugin.Flag.PreprocessTokens,
        )

    # ----------------------------------------------------------------------
    def test_PostprocessBlocks(self):
        self.Test(
            textwrap.dedent(
                """\

                # ----------------------------------------------------------------------
                # ----------------------------------------------------------------------
                # ----------------------------------------------------------------------
                # |
                # |  PostprocessBlocks
                # |
                # ----------------------------------------------------------------------
                # ----------------------------------------------------------------------
                # ----------------------------------------------------------------------
                Block 1) 1 line

                    Line 1) a = 10

                Block 2) 1 line

                    Line 1) def Func():

                Block 3) 1 line

                    Line 1) pass

                """,
            ),
            DebugPlugin.Flag.PostprocessBlocks,
        )


# ----------------------------------------------------------------------
# ----------------------------------------------------------------------
# ----------------------------------------------------------------------
if __name__ == "__main__":
    try:
        sys.exit(
            unittest.main(
                verbosity=2,
            ),
        )
    except KeyboardInterrupt:
        pass
