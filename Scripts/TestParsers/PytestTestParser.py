# ----------------------------------------------------------------------
# |
# |  PytestTestParser.py
# |
# |  David Brownell <db@DavidBrownell.com>
# |      2020-01-04 05:43:14
# |
# ----------------------------------------------------------------------
# |
# |  Copyright David Brownell 2020
# |  Distributed under the Boost Software License, Version 1.0. See
# |  accompanying file LICENSE_1_0.txt or copy at
# |  http://www.boost.org/LICENSE_1_0.txt.
# |
# ----------------------------------------------------------------------
"""Contains the TestParser object"""

import os
import re

import CommonEnvironment
from CommonEnvironment import Interface
from CommonEnvironment.TestParserImpl import TestParserImpl

# ----------------------------------------------------------------------
_script_fullpath                            = CommonEnvironment.ThisFullpath()
_script_dir, _script_name                   = os.path.split(_script_fullpath)
# ----------------------------------------------------------------------

# ----------------------------------------------------------------------
@Interface.staticderived
class TestParser(TestParserImpl):
    """Parses content produced by Python's pytest library"""

    # ----------------------------------------------------------------------
    # |  Public Properties
    Name                                    = Interface.DerivedProperty("Pytest")
    Description                             = Interface.DerivedProperty("Parses Python pytest output.")

    # ----------------------------------------------------------------------
    # |  Public Methods
    @staticmethod
    @Interface.override
    def IsSupportedCompiler(compiler):
        # Supports any compiler that supports python; use this file as a test subject
        return compiler.IsSupported(_script_fullpath if os.path.splitext(_script_name)[1] == ".py" else "{}.py".format(os.path.splitext(_script_fullpath)[0]))

    # ----------------------------------------------------------------------
    _IsSupportedTestItem_imports            = [
        re.compile("^\s*import unittest"),
        re.compile("^\s*from unittest import"),
    ]

    @classmethod
    @Interface.override
    def IsSupportedTestItem(cls, item):
        # Use this parser for any python test file that does not explicitly import 'unittest'
        assert os.path.isfile(item), item

        with open(item) as f:
            for line in f.readlines():
                for regex in cls._IsSupportedTestItem_imports:
                    if regex.search(line):
                        return False

        return True

    # ----------------------------------------------------------------------
    _Parse_failed                           = re.compile(r"== FAILURES ==")
    _Parse_passed                           = re.compile(r"== \d+ passed in [\d\.]+s ==")

    @classmethod
    @Interface.override
    def Parse(cls, test_data):
        if cls._Parse_failed.search(test_data):
            return -1

        if cls._Parse_passed.search(test_data):
            return 0

        return 1

    # ----------------------------------------------------------------------
    @classmethod
    @Interface.override
    def CreateInvokeCommandLine(cls, context, debug_on_error):
        command_line = super(TestParser, cls).CreateInvokeCommandLine(context, debug_on_error)

        return 'python -m pytest -o python_files=*Test.py --verbose "{}"'.format(command_line)
