# ----------------------------------------------------------------------
# |
# |  FunctionCallSplitterPlugin_UnitTest.py
# |
# |  David Brownell <db@DavidBrownell.com>
# |      2019-07-09 19:57:01
# |
# ----------------------------------------------------------------------
# |
# |  Copyright David Brownell 2019
# |  Distributed under the Boost Software License, Version 1.0. See
# |  accompanying file LICENSE_1_0.txt or copy at
# |  http://www.boost.org/LICENSE_1_0.txt.
# |
# ----------------------------------------------------------------------
"""Unit test for FunctionCallSplitterPlugin.py"""

import os
import sys
import textwrap
import unittest

import CommonEnvironment

from TestImpl import TestImpl

# ----------------------------------------------------------------------
_script_fullpath                            = CommonEnvironment.ThisFullpath()
_script_dir, _script_name                   = os.path.split(_script_fullpath)
# ----------------------------------------------------------------------

# ----------------------------------------------------------------------
class StandardSuite(TestImpl):
    # ----------------------------------------------------------------------
    def test_Standard(self):
        self.Test(
            textwrap.dedent(
                """\
                Foo(1, 2, 3)
                Foo(1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11)
                Foo(1, 2, c=3)
                Foo(1, # one
                    2,
                    3, # three
                )
                """,
            ),
            textwrap.dedent(
                """\
                Foo(1, 2, 3)
                Foo(
                    1,
                    2,
                    3,
                    4,
                    5,
                    6,
                    7,
                    8,
                    9,
                    10,
                    11,
                )
                Foo(
                    1,
                    2,
                    c=3,
                )
                Foo(
                    1,  # one
                    2,
                    3,  # three
                )

                """,
            ),
            "FunctionCallSplitter",
        )

    # ----------------------------------------------------------------------
    def test_NumArgs(self):
        self.Test(
            textwrap.dedent(
                """\
                Foo(1, 2, 3)
                Foo(1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11)
                Foo(1, 2, c=3)
                Foo(1, # one
                    2,
                    3, # three
                )
                """,
            ),
            textwrap.dedent(
                """\
                Foo(
                    1,
                    2,
                    3,
                )
                Foo(
                    1,
                    2,
                    3,
                    4,
                    5,
                    6,
                    7,
                    8,
                    9,
                    10,
                    11,
                )
                Foo(
                    1,
                    2,
                    c=3,
                )
                Foo(
                    1,  # one
                    2,
                    3,  # three
                )

                """,
            ),
            "FunctionCallSplitter",
            num_args=2,
        )


# ----------------------------------------------------------------------
# ----------------------------------------------------------------------
# ----------------------------------------------------------------------
if __name__ == "__main__":
    try:
        sys.exit(unittest.main(verbosity=2))
    except KeyboardInterrupt:
        pass
