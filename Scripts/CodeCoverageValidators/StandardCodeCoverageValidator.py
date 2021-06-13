# ----------------------------------------------------------------------
# |
# |  StandardCodeCoverageValidator.py
# |
# |  David Brownell <db@DavidBrownell.com>
# |      2018-05-22 22:31:15
# |
# ----------------------------------------------------------------------
# |
# |  Copyright David Brownell 2018-21.
# |  Distributed under the Boost Software License, Version 1.0.
# |  (See accompanying file LICENSE_1_0.txt or copy at http://www.boost.org/LICENSE_1_0.txt)
# |
# ----------------------------------------------------------------------
"""Contains the CodeCoverageValidator object"""

import os

import rtyaml

import CommonEnvironment
from CommonEnvironment.Interface import override, DerivedProperty
from CommonEnvironment.CodeCoverageValidatorImpl import CodeCoverageValidatorImpl

# ----------------------------------------------------------------------
_script_fullpath                            = CommonEnvironment.ThisFullpath()
_script_dir, _script_name                   = os.path.split(_script_fullpath)
# ----------------------------------------------------------------------

# ----------------------------------------------------------------------
class CodeCoverageValidator(CodeCoverageValidatorImpl):

    # ----------------------------------------------------------------------
    # |  Public Properties
    Name                                    = DerivedProperty("Standard")
    Description                             = DerivedProperty("Ensures that the measured code coverage is at least N%.")

    DEFAULT_MIN_CODE_COVERAGE_PERCENTAGE    = 70.0

    # Read the minimum coverage percentage from this file if it appears anywhere the directory
    # structure of the file being tested. The contents of the file should be a single value that
    # represents the minimum code coverage percentage (0.0 <= N <= 100.0).
    MIN_COVERAGE_PERCENTAGE_FILENAME        = "MinCodeCoverage.yaml"

    # ----------------------------------------------------------------------
    # |  Public Methods
    def __init__(
        self,
        min_code_coverage_percentage=DEFAULT_MIN_CODE_COVERAGE_PERCENTAGE,
        search_for_coverage_file=True,
    ):
        assert min_code_coverage_percentage >= 0.0, min_code_coverage_percentage
        assert min_code_coverage_percentage <= 100.0, min_code_coverage_percentage

        super(CodeCoverageValidator, self).__init__()

        self._min_code_coverage_percentage  = min_code_coverage_percentage
        self._search_for_coverage_file      = search_for_coverage_file

    # ----------------------------------------------------------------------
    @override
    def Validate(self, filename, measured_code_coverage_percentage):
        min_coverage_percentage = self._min_code_coverage_percentage

        if self._search_for_coverage_file:
            dirname = os.path.dirname(filename)

            while True:
                potential_filename = os.path.join(dirname, self.MIN_COVERAGE_PERCENTAGE_FILENAME)
                if os.path.isfile(potential_filename):
                    with open(potential_filename) as f:
                        content = rtyaml.load(f)

                    if isinstance(content, int):
                        content = float(content)

                    if (
                        isinstance(content, float)
                        and content >= 0.0
                        and content <= 100.0
                    ):
                        min_coverage_percentage = content

                    break

                potential_dirname = os.path.dirname(dirname)
                if potential_dirname == dirname:
                    break

                dirname = potential_dirname

        return (0 if measured_code_coverage_percentage >= min_coverage_percentage else -1, min_coverage_percentage)
