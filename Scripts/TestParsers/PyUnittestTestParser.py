# ----------------------------------------------------------------------
# |  
# |  PythonUnittestTestParser.py
# |  
# |  David Brownell <db@DavidBrownell.com>
# |      2018-05-22 07:59:46
# |  
# ----------------------------------------------------------------------
# |  
# |  Copyright David Brownell 2018.
# |  Distributed under the Boost Software License, Version 1.0.
# |  (See accompanying file LICENSE_1_0.txt or copy at http://www.boost.org/LICENSE_1_0.txt)
# |  
# ----------------------------------------------------------------------
"""Contains the TestParser object"""

import os
import re
import sys

from CommonEnvironment.Interface import staticderived, override, DerivedProperty
from CommonEnvironment.TestParserImpl import TestParserImpl

# ----------------------------------------------------------------------
_script_fullpath = os.path.abspath(__file__) if "python" in sys.executable.lower() else sys.executable
_script_dir, _script_name = os.path.split(_script_fullpath)
# ----------------------------------------------------------------------

# ----------------------------------------------------------------------
@staticderived
class TestParser(TestParserImpl):
    """Parses content produced by Python's unittest library"""

    # ----------------------------------------------------------------------
    # |  Public Properties
    Name                                    = DerivedProperty("PyUnittest")
    Description                             = DerivedProperty("Parses Python unittest output.")

    # ----------------------------------------------------------------------
    # |  Public Methods
    @staticmethod
    @override
    def IsSupportedCompiler(compiler):
        # Supports any compiler that supports python; use this file as a test subject
        return compiler.IsSupported(_script_fullpath if os.path.splitext(_script_name)[1] == ".py" else "{}.py".format(os.path.splitext(_script_fullpath)[0]))

    # ----------------------------------------------------------------------
    _Parse_failed                           = re.compile(r"^FAILED", re.DOTALL | re.MULTILINE)
    _Parse_ok                               = re.compile(r"^OK\s*", re.DOTALL | re.MULTILINE)

    @classmethod
    @override
    def Parse(cls, test_data):
        if cls._Parse_failed.search(test_data):
            return -1

        if cls._Parse_ok.search(test_data):
            return 0

        return 1

    # ----------------------------------------------------------------------
    @classmethod
    @override
    def CreateInvokeCommandLine(cls, context, debug_on_error):
        command_line = super(TestParser, cls).CreateInvokeCommandLine(context, debug_on_error)

        return 'python "{}"'.format(command_line)
