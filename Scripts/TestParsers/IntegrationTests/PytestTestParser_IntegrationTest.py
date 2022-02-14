# ----------------------------------------------------------------------
# |
# |  PytestTestParser_IntegrationTest.py
# |
# |  David Brownell <db@DavidBrownell.com>
# |      2021-07-08 10:01:36
# |
# ----------------------------------------------------------------------
# |
# |  Copyright David Brownell 2021-22
# |  Distributed under the Boost Software License, Version 1.0. See
# |  accompanying file LICENSE_1_0.txt or copy at
# |  http://www.boost.org/LICENSE_1_0.txt.
# |
# ----------------------------------------------------------------------
"""Verifies that PytestTestParser is executing and extracting data properly"""

import os

import CommonEnvironment

# ----------------------------------------------------------------------
_script_fullpath                            = CommonEnvironment.ThisFullpath()
_script_dir, _script_name                   = os.path.split(_script_fullpath)
# ----------------------------------------------------------------------

# ----------------------------------------------------------------------
def TestFunc(a, b):
    return a + b

def test_Benchmarks(benchmark):
    assert benchmark(TestFunc, 10, 20) == 30
