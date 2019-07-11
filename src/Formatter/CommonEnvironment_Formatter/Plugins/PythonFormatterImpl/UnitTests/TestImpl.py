# ----------------------------------------------------------------------
# |
# |  TestImpl.py
# |
# |  David Brownell <db@DavidBrownell.com>
# |      2019-07-09 15:47:52
# |
# ----------------------------------------------------------------------
# |
# |  Copyright David Brownell 2019
# |  Distributed under the Boost Software License, Version 1.0. See
# |  accompanying file LICENSE_1_0.txt or copy at
# |  http://www.boost.org/LICENSE_1_0.txt.
# |
# ----------------------------------------------------------------------
"""
Note that the tests in this folder are actually Integration tests (as they
rely on PythonFormatter, but named `UnitTests` so that they participate in code
coverage evaluation.
"""

import os
import sys
import unittest

import CommonEnvironment
from CommonEnvironment.CallOnExit import CallOnExit

# ----------------------------------------------------------------------
_script_fullpath                            = CommonEnvironment.ThisFullpath()
_script_dir, _script_name                   = os.path.split(_script_fullpath)
#  ----------------------------------------------------------------------

# ----------------------------------------------------------------------
class TestImpl(unittest.TestCase):
    # ----------------------------------------------------------------------
    def setUp(self):
        self.maxDiff = None

    # ----------------------------------------------------------------------
    def Test(
        self,
        original,
        expected,
        plugin_name,
        black_line_length=None,
        **plugin_args
    ):
        if sys.version[0] == "2":
            typ = type(self)

            if not hasattr(typ, "_displayed_message"):
                sys.stdout.write("This script does not run with python 2.\n")
                setattr(typ, "_displayed_message", True)

            self.assertTrue(True)
            return

        sys.path.insert(0, os.path.join(_script_dir, "..", ".."))
        with CallOnExit(lambda: sys.path.pop(0)):
            from PythonFormatter import Formatter       # <Unable to import> pylint: disable = E0401

        result = Formatter.Format(
            original,
            black_line_length=black_line_length,
            include_plugin_names=[plugin_name],
            **{plugin_name: plugin_args}
        )

        self.assertEqual(result[0], expected)
        self.assertEqual(result[1], not expected == original)
