# ----------------------------------------------------------------------
# |
# |  __init__.py
# |
# |  David Brownell <db@DavidBrownell.com>
# |      2018-05-22 07:53:05
# |
# ----------------------------------------------------------------------
# |
# |  Copyright David Brownell 2018-21.
# |  Distributed under the Boost Software License, Version 1.0.
# |  (See accompanying file LICENSE_1_0.txt or copy at http://www.boost.org/LICENSE_1_0.txt)
# |
# ----------------------------------------------------------------------
"""Contains the TestParser object"""

import os

import CommonEnvironment
from CommonEnvironment.Interface import Interface, abstractmethod, abstractproperty, extensionmethod

# ----------------------------------------------------------------------
_script_fullpath                            = CommonEnvironment.ThisFullpath()
_script_dir, _script_name                   = os.path.split(_script_fullpath)
# ----------------------------------------------------------------------

# ----------------------------------------------------------------------
class TestParserImpl(Interface):
    """Abstract base class for object that is able to consume and interpret test execution results."""

    # ----------------------------------------------------------------------
    # |
    # |  Public Types
    # |
    # ----------------------------------------------------------------------
    class BenchmarkStat(object):
        # ----------------------------------------------------------------------
        def __init__(
            self,
            name,
            source_filename,
            source_line,
            extractor,
            min_value,
            max_value,
            mean_value,
            standard_deviation,
            samples,
            units,
            iterations=1,
        ):
            self.Name                       = name
            self.SourceFilename             = source_filename
            self.SourceLine                 = source_line
            self.Extractor                  = extractor
            self.Min                        = min_value
            self.Max                        = max_value
            self.Mean                       = mean_value
            self.StandardDeviation          = standard_deviation
            self.Samples                    = samples
            self.Units                      = units
            self.Iterations                 = iterations

        # ----------------------------------------------------------------------
        def __repr__(self):
            return CommonEnvironment.ObjectReprImpl(self)

        # ----------------------------------------------------------------------
        @staticmethod
        def ConvertTime(value, units, dest_units):
            # nanoseconds (ns)
            # macroseconds (us)
            # milliseconds (ms)
            # seconds (s)

            if units == dest_units:
                return value

            if units == "s":
                value *= 1000
                units = "ms"

            if units == "ms":
                value *= 1000
                units = "us"

            if units == "us":
                value *= 1000
                units = "ns"

            assert units == "ns", units

            if dest_units == "ns":
                return value

            value /= 1000
            if dest_units == "us":
                return value

            value /= 1000
            if dest_units == "ms":
                return value

            value /= 1000

            assert dest_units == "s", dest_units
            return value

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
    @extensionmethod
    def IsSupportedTestItem(item):
        """Returns True if the test parser is able to process this test item"""
        return True

    # ----------------------------------------------------------------------
    @staticmethod
    @abstractmethod
    def Parse(test_data):
        # ->
        #   Union[
        #       int,
        #       Tuple[int, List[TestParserImpl.BenchmarkStat]],
        #       Tuple[int, List[TestParserImpl.BenchmarkStat], Dict[str, Tuple[int, datetime.timedelta]]],
        #   ]

        """
        Parses the given data looking for signs of successful execution.

        Returns one of the following:
            - Error code
            - Error code and list of benchmarks
            - Error code, list of benchmarks, and subtest error codes and execution times
        """
        raise Exception("Abstract property")

    # ----------------------------------------------------------------------
    @staticmethod
    @extensionmethod
    def CreateInvokeCommandLine(context, debug_on_error):
        """Returns a command line used to invoke the test execution engine for the given context."""

        for potential_key in ["input"]:
            if potential_key in context:
                return context[potential_key]

        if "inputs" in context:
            assert context["inputs"]
            assert isinstance(context["inputs"], list), context["inputs"]
            return context["inputs"][0]

        raise Exception("Unknown input")

    # ----------------------------------------------------------------------
    @staticmethod
    @extensionmethod
    def RemoveTemporaryArtifacts(context):
        """Remove any additional artifacts once compilation is complete"""
        pass
