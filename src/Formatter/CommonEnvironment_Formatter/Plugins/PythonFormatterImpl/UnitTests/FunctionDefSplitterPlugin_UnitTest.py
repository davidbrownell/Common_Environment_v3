# ----------------------------------------------------------------------
# |
# |  FunctionDefSplitterPlugin_UnitTest.py
# |
# |  David Brownell <db@DavidBrownell.com>
# |      2019-07-09 20:04:01
# |
# ----------------------------------------------------------------------
# |
# |  Copyright David Brownell 2019-20
# |  Distributed under the Boost Software License, Version 1.0. See
# |  accompanying file LICENSE_1_0.txt or copy at
# |  http://www.boost.org/LICENSE_1_0.txt.
# |
# ----------------------------------------------------------------------
"""Unit test for FunctionDefSplitterPlugin.py"""

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
                def Foo1(a, b, c):
                    pass

                def Foo2(a, b, c, d, e, f, g, h, i, j, k, l, m, n):
                    pass

                def Foo3(a, b, c=3):
                    pass

                def Foo4(a # one
                ):
                    pass

                def Foo5(
                    a, # one
                    b, # two
                ):
                    pass
                """,
            ),
            textwrap.dedent(
                """\
                def Foo1(a, b, c):
                    pass


                def Foo2(
                    a,
                    b,
                    c,
                    d,
                    e,
                    f,
                    g,
                    h,
                    i,
                    j,
                    k,
                    l,
                    m,
                    n,
                ):
                    pass


                def Foo3(
                    a,
                    b,
                    c=3,
                ):
                    pass


                def Foo4(a  # one


                ):
                    pass


                def Foo5(
                    a,  # one
                    b,  # two
                ):
                    pass

                """,
            ),
            "FunctionDefSplitter",
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
