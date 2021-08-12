# ----------------------------------------------------------------------
# |
# |  AutomatedTestHelpers_UnitTest.py
# |
# |  David Brownell <db@DavidBrownell.com>
# |      2021-08-12 10:36:21
# |
# ----------------------------------------------------------------------
# |
# |  Copyright David Brownell 2021
# |  Distributed under the Boost Software License, Version 1.0. See
# |  accompanying file LICENSE_1_0.txt or copy at
# |  http://www.boost.org/LICENSE_1_0.txt.
# |
# ----------------------------------------------------------------------
"""Unit test for AutomatedTestHelpers.py"""

import os
import sys
import textwrap

import CommonEnvironment
from CommonEnvironment.AutomatedTestHelpers import *

# ----------------------------------------------------------------------
_script_fullpath                            = CommonEnvironment.ThisFullpath()
_script_dir, _script_name                   = os.path.split(_script_fullpath)
# ----------------------------------------------------------------------


# ----------------------------------------------------------------------
def test_StandAlone():
    assert textwrap.dedent(
        """\
        test_StandAlone1
        test_StandAlone2
        """,
    ) == ResultsFromFile()


# ----------------------------------------------------------------------
def test_MissingFile():
    assert ResultsFromFile() == textwrap.dedent(
        """\
        ********************************************************************************
        ********************************************************************************
        ********************************************************************************

        The filename does not exist:

            {}

        ********************************************************************************
        ********************************************************************************
        ********************************************************************************
        """,
    ).format(
        os.path.join(os.path.dirname(_script_fullpath), "Results", "{}.test_MissingFile.txt".format(os.path.splitext(_script_name)[0])),
    )


# ----------------------------------------------------------------------
class TestStandard(object):
    # ----------------------------------------------------------------------
    def test_Method(self):
        assert textwrap.dedent(
            """\
            test_Method1
            test_Method2
            test_Method3
            test_Method4
            """,
        ) == ResultsFromFile()

    # ----------------------------------------------------------------------
    def test_MissingFile(self):
        assert ResultsFromFile() == textwrap.dedent(
            """\
            ********************************************************************************
            ********************************************************************************
            ********************************************************************************

            The filename does not exist:

                {}

            ********************************************************************************
            ********************************************************************************
            ********************************************************************************
            """,
        ).format(
            os.path.join(os.path.dirname(_script_fullpath), "Results", "{}.TestStandard.test_MissingFile.txt".format(os.path.splitext(_script_name)[0])),
        )
