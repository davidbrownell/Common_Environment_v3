# ----------------------------------------------------------------------
# |  
# |  __init__.py
# |  
# |  David Brownell <db@DavidBrownell.com>
# |      2018-05-22 07:53:05
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
import sys

from CommonEnvironment.Interface import Interface, \
                                        abstractmethod, \
                                        abstractproperty, \
                                        extensionmethod

# ----------------------------------------------------------------------
_script_fullpath = os.path.abspath(__file__) if "python" in sys.executable.lower() else sys.executable
_script_dir, _script_name = os.path.split(_script_fullpath)
# ----------------------------------------------------------------------

# ----------------------------------------------------------------------
class TestParserImpl(Interface):
    """Abstract base class for object that is able to consume and interpret test execution results."""

    # ----------------------------------------------------------------------
    # |  
    # |  Public Properties
    # |  
    # ----------------------------------------------------------------------
    @abstractproperty
    def Name(self):
        """Name of the test parser"""
        raise Exception("Abstract property")

    @abstractproperty
    def Description(self):
        """Description of the test parser"""
        raise Exception("Abstract property")

    # ----------------------------------------------------------------------
    # |  
    # |  Public Methods
    # |  
    # ----------------------------------------------------------------------
    @staticmethod
    @abstractmethod
    def IsSupportedCompiler(compiler):
        """Returns True if the compiler produces results that can be consumed by the test parser"""
        raise Exception("Abstract method")

    # ----------------------------------------------------------------------
    @staticmethod
    @abstractmethod
    def Parse(test_data):
        """
        Parses the given data looking for signs of successful execution. Returns
        an error code indicating the results.
        """
        raise Exception("Abstract property")

    # ----------------------------------------------------------------------
    @staticmethod
    @extensionmethod
    def CreateInvokeCommandLine(context, debug_on_error):
        """Returns a command line used to invoke the test execution engine for the given context."""

        for potential_key in [ "input", ]:
            if potential_key in context:
                return context[potential_key]

        if "inputs" in context:
            assert context["inputs"]
            assert isinstance(context["inputs"], list), context["inputs"]
            return context["inputs"][0]

        raise Exception("Unknown input")
