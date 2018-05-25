# ----------------------------------------------------------------------
# |  
# |  __init__.py
# |  
# |  David Brownell <db@DavidBrownell.com>
# |      2018-05-22 22:27:15
# |  
# ----------------------------------------------------------------------
# |  
# |  Copyright David Brownell 2018.
# |  Distributed under the Boost Software License, Version 1.0.
# |  (See accompanying file LICENSE_1_0.txt or copy at http://www.boost.org/LICENSE_1_0.txt)
# |  
# ----------------------------------------------------------------------
"""Contains the CodeCoverageValidatorImpl"""

import os
import sys

from CommonEnvironment.Interface import Interface, \
                                        abstractproperty, \
                                        abstractmethod

# ----------------------------------------------------------------------
_script_fullpath = os.path.abspath(__file__) if "python" in sys.executable.lower() else sys.executable
_script_dir, _script_name = os.path.split(_script_fullpath)
# ----------------------------------------------------------------------

# ----------------------------------------------------------------------
class CodeCoverageValidatorImpl(Interface):
    """Abstract base class for object that is able to validate code coverage results."""

    # ----------------------------------------------------------------------
    # |  
    # |  Public Properties
    # |  
    # ----------------------------------------------------------------------
    @abstractproperty
    def Name(self):
        """Name of the code coverage validator"""
        raise Exception("Abstract property")

    @abstractproperty
    def Description(self):
        """Description of the code coverage validator"""
        raise Exception("Abstract property")

    # ----------------------------------------------------------------------
    # |  
    # |  Public Methods
    # |  
    # ----------------------------------------------------------------------
    @staticmethod
    @abstractmethod
    def Validate(filename, measured_code_coverage_percentage):
        """Returns (result, min_code_coverage_percentage)"""
        raise Exception("Abstract method")
