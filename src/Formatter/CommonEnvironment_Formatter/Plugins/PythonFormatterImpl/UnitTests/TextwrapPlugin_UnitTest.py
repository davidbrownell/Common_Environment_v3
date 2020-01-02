# ----------------------------------------------------------------------
# |
# |  TextwrapPlugin_UnitTest.py
# |
# |  David Brownell <db@DavidBrownell.com>
# |      2019-07-09 20:19:17
# |
# ----------------------------------------------------------------------
# |
# |  Copyright David Brownell 2019-20
# |  Distributed under the Boost Software License, Version 1.0. See
# |  accompanying file LICENSE_1_0.txt or copy at
# |  http://www.boost.org/LICENSE_1_0.txt.
# |
# ----------------------------------------------------------------------
"""Unit test for TextwrapPlugin.py"""

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
    def testStandard(self):
        # This looks strange, but it actually works when content is indented as expected
        self.Test(
            textwrap.dedent(
                """
                print(
                    textwrap.dedent(
                        '''\\
                        one
                        two
                        ''',
                    ),
                )
                """,
            ),
            textwrap.dedent(
                '''
                print(
                    textwrap.dedent(
                        """\\
                        one
                        two
                        """
                    )
                )
                ''',
            ).lstrip(),
            "Textwrap",
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
