# ----------------------------------------------------------------------
# |  
# |  __init__.py
# |  
# |  David Brownell <db@DavidBrownell.com>
# |      2018-05-22 22:15:32
# |  
# ----------------------------------------------------------------------
# |  
# |  Copyright David Brownell 2018.
# |  Distributed under the Boost Software License, Version 1.0.
# |  (See accompanying file LICENSE_1_0.txt or copy at http://www.boost.org/LICENSE_1_0.txt)
# |  
# ----------------------------------------------------------------------
"""Contains the TestExecutorImpl object"""

import os
import sys

from collections import namedtuple

from CommonEnvironment.Interface import Interface, \
                                        abstractproperty, \
                                        abstractmethod, \
                                        extensionmethod

# ----------------------------------------------------------------------
_script_fullpath = os.path.abspath(__file__) if "python" in sys.executable.lower() else sys.executable
_script_dir, _script_name = os.path.split(_script_fullpath)
# ----------------------------------------------------------------------

# ----------------------------------------------------------------------
class TestExecutorImpl(Interface):
    """Abstract base class for object that is able to execute a test and potentiall extract code coverage information from data produced during the test's execution."""

    # ----------------------------------------------------------------------
    # |  
    # |  Public Types
    # |  
    # ----------------------------------------------------------------------
    class ExecuteResult(object):
        def __init__( self,
                      test_result,
                      test_output,
                      test_time,
                      
                      coverage_result=None,
                      coverage_output=None,
                      coverage_time=None,
                      coverage_data_filename=None,
                      
                      coverage_percentage=None,
                      coverage_percentages=None,
                    ):
            self.TestResult                 = test_result
            self.TestOutput                 = test_output
            self.TestTime                   = test_time

            self.CoverageResult             = coverage_result
            self.CoverageOutput             = coverage_output
            self.CoverageTime               = coverage_time
            self.CoverageDataFilename       = coverage_data_filename

            self.CoveragePercentage         = coverage_percentage
            self.CoveragePercentages        = coverage_percentages

    # ----------------------------------------------------------------------
    # |  
    # |  Public Properties
    # |  
    # ----------------------------------------------------------------------
    @abstractproperty
    def Name(self):
        """Name of the code coverage extractor"""
        raise Exception("Abstract property")

    @abstractproperty
    def Description(self):
        """Description of the code coverage extractor"""
        raise Exception("Abstract property")

    # ----------------------------------------------------------------------
    # |  
    # |  Public Methods
    # |  
    # ----------------------------------------------------------------------
    @staticmethod
    @extensionmethod
    def ValidateEnvironment():
        """
        Used to determine if a code coverage extractor can run in the current environment. 
        This method prevents the invocation of a code coverage extractor in an environment 
        where it will never be successful (for example, an environment where the necessary 
        dependencies are not installed).

        Return 0 or None if the environment is valid or a string that describes why the
        environment isn't valid if not.
        """

        # No validation by default
        pass 

    # ----------------------------------------------------------------------
    @staticmethod
    @abstractmethod
    def IsSupportedCompiler(compiler):
        """Returns True if the compiler produces results that can be consumed by the code coverage extractor"""
        raise Exception("Abstract method")

    # ----------------------------------------------------------------------
    @staticmethod
    @abstractmethod
    def Execute( compiler,
                 context,
                 command_line,
                 includes=None,
                 excludes=None,
                 verbose=False,
               ):
        """Returns ExecuteResult"""
        raise Exception("Abstract method")
