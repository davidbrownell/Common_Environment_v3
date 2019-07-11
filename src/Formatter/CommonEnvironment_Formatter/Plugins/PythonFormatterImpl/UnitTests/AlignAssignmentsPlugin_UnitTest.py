# ----------------------------------------------------------------------
# |
# |  AlignAssignmentsPlugin_UnitTest.py
# |
# |  David Brownell <AlignAssignmentsPlugin_UnitTestdb@DavidBrownell.com>
# |      2019-07-09 16:35:21
# |
# ----------------------------------------------------------------------
# |
# |  Copyright David Brownell 2019
# |  Distributed under the Boost Software License, Version 1.0. See
# |  accompanying file LICENSE_1_0.txt or copy at
# |  http://www.boost.org/LICENSE_1_0.txt.
# |
# ----------------------------------------------------------------------
"""Unit test for AllignAssignmentsPlugin.py"""

import os
import sys
import textwrap
import unittest

import CommonEnvironment
from CommonEnvironment.CallOnExit import CallOnExit

from TestImpl import TestImpl

# ----------------------------------------------------------------------
_script_fullpath                            = CommonEnvironment.ThisFullpath()
_script_dir, _script_name                   = os.path.split(_script_fullpath)
# ----------------------------------------------------------------------

sys.path.insert(0, os.path.join(_script_dir, "..", ".."))
with CallOnExit(lambda: sys.path.pop(0)):
    from PythonFormatterImpl.AlignAssignmentsPlugin import (
        Plugin as AlignAssignmentsPlugin,
    )

# ----------------------------------------------------------------------
class StandardSuite(TestImpl):
    # ----------------------------------------------------------------------
    def test_Standard(self):
        self.Test(
            textwrap.dedent(
                """\
                a = 10

                class Foo(object):
                    b = 20

                    def __init__(self):
                        self.c = 30
                        d = 40

                    def Foo(self):
                        self.e = 50
                        f = 60
                """,
            ),
            textwrap.dedent(
                """\
                a                                           = 10


                class Foo(object):
                    b                                       = 20

                    def __init__(self):
                        self.c                              = 30
                        d = 40

                    def Foo(self):
                        self.e = 50
                        f = 60
                """,
            ),
            "AlignAssignments",
        )

    # ----------------------------------------------------------------------
    def test_Module(self):
        self.Test(
            textwrap.dedent(
                """\
                a = 10

                class Foo(object):
                    b = 20

                    def __init__(self):
                        self.c = 30
                        d = 40

                    def Foo(self):
                        self.e = 50
                        f = 60
                """,
            ),
            textwrap.dedent(
                """\
                a                                           = 10


                class Foo(object):
                    b = 20

                    def __init__(self):
                        self.c = 30
                        d = 40

                    def Foo(self):
                        self.e = 50
                        f = 60
                """,
            ),
            "AlignAssignments",
            alignment_flags=AlignAssignmentsPlugin.Flag.ModuleLevel,
        )

    # ----------------------------------------------------------------------
    def test_Class(self):
        self.Test(
            textwrap.dedent(
                """\
                a = 10

                class Foo(object):
                    b = 20

                    def __init__(self):
                        self.c = 30
                        d = 40

                    def Foo(self):
                        self.e = 50
                        f = 60
                """,
            ),
            textwrap.dedent(
                """\
                a = 10


                class Foo(object):
                    b                                       = 20

                    def __init__(self):
                        self.c = 30
                        d = 40

                    def Foo(self):
                        self.e = 50
                        f = 60
                """,
            ),
            "AlignAssignments",
            alignment_flags=AlignAssignmentsPlugin.Flag.ClassLevel,
        )

    # ----------------------------------------------------------------------
    def test_Init(self):
        self.Test(
            textwrap.dedent(
                """\
                a = 10

                class Foo(object):
                    b = 20

                    def __init__(self):
                        self.c = 30
                        d = 40

                    def Foo(self):
                        self.e = 50
                        f = 60
                """,
            ),
            textwrap.dedent(
                """\
                a = 10


                class Foo(object):
                    b = 20

                    def __init__(self):
                        self.c                              = 30
                        d = 40

                    def Foo(self):
                        self.e = 50
                        f = 60
                """,
            ),
            "AlignAssignments",
            alignment_flags=AlignAssignmentsPlugin.Flag.InitLevel,
        )

    # ----------------------------------------------------------------------
    def test_InitAny(self):
        self.Test(
            textwrap.dedent(
                """\
                a = 10

                class Foo(object):
                    b = 20

                    def __init__(self):
                        self.c = 30
                        d = 40

                    def Foo(self):
                        self.e = 50
                        f = 60
                """,
            ),
            textwrap.dedent(
                """\
                a = 10


                class Foo(object):
                    b = 20

                    def __init__(self):
                        self.c                              = 30
                        d                                   = 40

                    def Foo(self):
                        self.e = 50
                        f = 60
                """,
            ),
            "AlignAssignments",
            alignment_flags=AlignAssignmentsPlugin.Flag.InitAnyLevel,
        )

    # ----------------------------------------------------------------------
    def test_Method(self):
        self.Test(
            textwrap.dedent(
                """\
                a = 10

                class Foo(object):
                    b = 20

                    def __init__(self):
                        self.c = 30
                        d = 40

                    def Foo(self):
                        self.e = 50
                        f = 60
                """,
            ),
            textwrap.dedent(
                """\
                a = 10


                class Foo(object):
                    b = 20

                    def __init__(self):
                        self.c = 30
                        d = 40

                    def Foo(self):
                        self.e                              = 50
                        f                                   = 60
                """,
            ),
            "AlignAssignments",
            alignment_flags=AlignAssignmentsPlugin.Flag.MethodLevel,
        )

    # ----------------------------------------------------------------------
    def test_AlignmentColumns(self):
        self.Test(
            textwrap.dedent(
                """\
                a = a

                one = 1

                two______ = 2

                three___________ = 3

                a = a
                one = 1
                two______ = 2
                three___________ = 3
                """,
            ),
            textwrap.dedent(
                """\
                a   = a

                one      = 1

                two______     = 2

                three___________ = 3

                a                = a
                one              = 1
                two______        = 2
                three___________ = 3
                """,
            ),
            "AlignAssignments",
            alignment_columns=[5, 10, 15],
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
