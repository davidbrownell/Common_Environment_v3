# ----------------------------------------------------------------------
# |
# |  AlignTrailingCommentsPlugin_UnitTest.py
# |
# |  David Brownell <db@DavidBrownell.com>
# |      2019-07-09 18:57:51
# |
# ----------------------------------------------------------------------
# |
# |  Copyright David Brownell 2019
# |  Distributed under the Boost Software License, Version 1.0. See
# |  accompanying file LICENSE_1_0.txt or copy at
# |  http://www.boost.org/LICENSE_1_0.txt.
# |
# ----------------------------------------------------------------------
"""Unit test for AlignTrailingCommentsPlugin.py"""

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
                a # a

                one # one

                two # two

                three # three

                a # a
                one # one
                two # two
                three # three
                """,
            ),
            textwrap.dedent(
                """\
                a                                           # a

                one                                         # one

                two                                         # two

                three                                       # three

                a                                           # a
                one                                         # one
                two                                         # two
                three                                       # three
                """,
            ),
            "AlignTrailingComments",
        )

    # ----------------------------------------------------------------------
    def test_AlignmentColumns(self):
        self.Test(
            textwrap.dedent(
                """\
                a # a

                one # one

                two______ # two

                three___________ # three

                a # a
                one # one
                two______ # two
                three___________ # three
                """,
            ),
            textwrap.dedent(
                """\
                a   # a

                one      # one

                two______     # two

                three___________ # three

                a                # a
                one              # one
                two______        # two
                three___________ # three
                """,
            ),
            "AlignTrailingComments",
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
