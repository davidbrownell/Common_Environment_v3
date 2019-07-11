# ----------------------------------------------------------------------
# |
# |  DecoratorWhitespacePlugin_UnitTest.py
# |
# |  David Brownell <db@DavidBrownell.com>
# |      2019-07-09 19:38:43
# |
# ----------------------------------------------------------------------
# |
# |  Copyright David Brownell 2019
# |  Distributed under the Boost Software License, Version 1.0. See
# |  accompanying file LICENSE_1_0.txt or copy at
# |  http://www.boost.org/LICENSE_1_0.txt.
# |
# ----------------------------------------------------------------------
"""Unit test for DecoratorWhitespacePlugin.py"""

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
class TestStandard(TestImpl):
    # ----------------------------------------------------------------------
    def test_Standard(self):
        self.Test(
            textwrap.dedent(
                """\
                @one
                def Func():
                    pass


                @one
                @two
                def Func():
                    pass
                """,
            ),
            textwrap.dedent(
                """\
                @one
                def Func():
                    pass


                @one
                @two
                def Func():
                    pass
                """,
            ),
            "DecoratorWhitespace",
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
