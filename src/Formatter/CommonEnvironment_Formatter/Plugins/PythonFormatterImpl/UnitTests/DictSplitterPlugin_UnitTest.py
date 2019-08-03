# ----------------------------------------------------------------------
# |
# |  DictSplitterPlugin_UnitTest.py
# |
# |  David Brownell <db@DavidBrownell.com>
# |      2019-07-09 19:45:30
# |
# ----------------------------------------------------------------------
# |
# |  Copyright David Brownell 2019
# |  Distributed under the Boost Software License, Version 1.0. See
# |  accompanying file LICENSE_1_0.txt or copy at
# |  http://www.boost.org/LICENSE_1_0.txt.
# |
# ----------------------------------------------------------------------
"""Unit test for DictSplitterPlugin.py"""

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
                a = {1, 2}
                b = {1, 2, 3, 4}
                d = {a: b for a, b in l}
                """,
            ),
            textwrap.dedent(
                """\
                a = {1, 2}
                b = {
                    1,
                    2,
                    3,
                    4,
                }
                d = {a: b for a, b in l}

                """,
            ),
            "DictSplitter",
        )

    # ----------------------------------------------------------------------
    def test_Args(self):
        self.Test(
            textwrap.dedent(
                """\
                a = {1, 2}
                b = {1, 2, 3, 4}
                d = {a: b for a, b in l}
                """,
            ),
            textwrap.dedent(
                """\
                a = {
                    1,
                    2,
                }
                b = {
                    1,
                    2,
                    3,
                    4,
                }
                d = {
                    a: b for a,
                    b in l
                }

                """,
            ),
            "DictSplitter",
            num_args=1,
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