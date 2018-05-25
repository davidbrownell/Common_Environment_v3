# ----------------------------------------------------------------------
# |  
# |  StandardCodeCoverageValidator.py
# |  
# |  David Brownell <db@DavidBrownell.com>
# |      2018-05-22 22:31:15
# |  
# ----------------------------------------------------------------------
# |  
# |  Copyright David Brownell 2018.
# |  Distributed under the Boost Software License, Version 1.0.
# |  (See accompanying file LICENSE_1_0.txt or copy at http://www.boost.org/LICENSE_1_0.txt)
# |  
# ----------------------------------------------------------------------
"""Contains the CodeCoverageValidator object"""

import os
import sys

from CommonEnvironment.Interface import staticderived
from CommonEnvironment.CodeCoverageValidatorImpl import CodeCoverageValidatorImpl

# ----------------------------------------------------------------------
_script_fullpath = os.path.abspath(__file__) if "python" in sys.executable.lower() else sys.executable
_script_dir, _script_name = os.path.split(_script_fullpath)
# ----------------------------------------------------------------------

# ----------------------------------------------------------------------
@staticderived
class CodeCoverageValidator(CodeCoverageValidatorImpl):

    # ----------------------------------------------------------------------
    # |  Public Properties
    Name                                    = "Standard"
    Description                             = "Ensures that the measured code coverage is at least N%."

    DEFAULT_MIN_CODE_COVERAGE_PERCENTAGE    = 70.0

    # ----------------------------------------------------------------------
    # |  Public Methods
    def __init__( self,
                  min_code_coverage_percentage=DEFAULT_MIN_CODE_COVERAGE_PERCENTAGE,
                ):
        super(CodeCoverageValidatorImpl, self).__init__()

        self._min_code_coverage_percentage  = min_code_coverage_percentage
        assert self._min_code_coverage_percentage >= 0.0 and self._min_code_coverage_percentage <= 100.0, self._min_code_coverage_percentage

    # ----------------------------------------------------------------------
    def Validate(self, filename, measured_code_coverage_percentage):
        return ( 0 if measured_code_coverage_percentage >= self._min_code_coverage_percentage else -1,
                 self._min_code_coverage_percentage,
               )
