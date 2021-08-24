# ----------------------------------------------------------------------
# |
# |  PytestTestParser.py
# |
# |  David Brownell <db@DavidBrownell.com>
# |      2020-01-04 05:43:14
# |
# ----------------------------------------------------------------------
# |
# |  Copyright David Brownell 2020-21
# |  Distributed under the Boost Software License, Version 1.0. See
# |  accompanying file LICENSE_1_0.txt or copy at
# |  http://www.boost.org/LICENSE_1_0.txt.
# |
# ----------------------------------------------------------------------
"""Contains the TestParser object"""

import os
import re
import sys

import CommonEnvironment
from CommonEnvironment import Interface
from CommonEnvironment.Shell.All import CurrentShell
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
        # If these imports are present, it is NOT a pytest test file
        re.compile(r"^\s*import unittest"),
        re.compile(r"^\s*from unittest import"),
    ]

    @classmethod
    @Interface.override
    def IsSupportedTestItem(cls, item):
        # pytest is only supported on python3
        if sys.version_info[0] == 2:
            return False

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
    _Parse_passed                           = re.compile(
        r"""(?#
            Delimiter prefix                )== (?#
            Passed statement                )\d+ passed(?#
            Skipped statement [optional]    )(?:, \d+ skipped)?(?#
            In ___s                         ) in [\d\.]+s(?#
            Minutes conversion [optional]   )(?: \([\d:]+\))?(?#
            Delimiter suffix                ) ==(?#
        )""",
    )

    _Pytest_version                         = re.compile(r"(?P<value>pytest-\d+\.\d+\.\d+)")
    _Benchmark_version                      = re.compile(r"(?P<value>benchmark-\d+\.\d+\.\d+)")

    _Parse_benchmark_content                = re.compile(
        r"""(?#
        Header Prefix                       )----+ benchmark: \d+ tests ----+\r?\n(?#
        Header
            Name                            )Name \(time in (?P<units>\S+)\)\s+(?#
            Min                             )Min\s+(?#
            Max                             )Max\s+(?#
            Mean                            )Mean\s+(?#
            StdDev                          )StdDev\s+(?#
            Median                          )Median\s+(?#
            InterQuartile Range             )IQR\s+(?#
            Outliners                       )Outliers\s+(?#
            Operations per second           )OPS \(Mops/s\)\s+(?#
            Rounds                          )Rounds\s+(?#
            Iterations                      )Iterations\r?\n(?#
        Header Suffix                       )----+\r?\n(?#
        Content                             )(?P<content>.+)\r?\n(?#
        Footer                              )----+\r?\n(?#
        )""",
        re.DOTALL | re.MULTILINE,
    )

    _Parse_benchmark_line_item              = re.compile(
        r"""(?#
        Name                                )(?P<name>\S+)\s+(?#
        Min                                 )(?P<min>{float_regex})(?: \((?P<min_dev>{float_regex})\))?\s+(?#
        Max                                 )(?P<max>{float_regex})(?: \((?P<max_dev>{float_regex})\))?\s+(?#
        Mean                                )(?P<mean>{float_regex})(?: \((?P<mean_dev>{float_regex})\))?\s+(?#
        StdDev                              )(?P<std_dev>{float_regex})(?: \((?P<std_dev_dev>{float_regex})\))?\s+(?#
        Median                              )(?P<median>{float_regex})(?: \((?P<median_dev>{float_regex})\))?\s+(?#
        IQR                                 )(?P<iqr>{float_regex})(?: \((?P<iqr_dev>{float_regex})\))?\s+(?#
        Outliers                            )(?P<outlier_first>\d+);(?P<outlier_second>\d+)\s+(?#
        OPS                                 )(?P<ops>{float_regex})(?: \((?P<ops_dev>{float_regex})\))?\s+(?#
        Rounds                              )(?P<rounds>\d+)\s+(?#
        Iterations                          )(?P<iterations>\d+)(?#
        )""".format(
            float_regex=r"[\d,]+\.\d+",
        ),
    )

    @classmethod
    @Interface.override
    def Parse(cls, test_data):
        if cls._Parse_failed.search(test_data):
            return -1

        if not cls._Parse_passed.search(test_data):
            return 1

        benchmarks = []

        match = cls._Parse_benchmark_content.search(test_data)
        if match:
            # Get the pytest and benchmark versions
            pytest_version = cls._Pytest_version.search(test_data)
            assert pytest_version
            pytest_version = pytest_version.group("value")

            benchmark_version = cls._Benchmark_version.search(test_data)
            assert benchmark_version
            benchmark_version = benchmark_version.group("value")

            # Parse the match
            units = match.group("units")
            match = match.group("content")

            for line_item in match.split("\n"):
                line_item = line_item.strip()

                match = cls._Parse_benchmark_line_item.match(line_item)
                assert match, line_item

                benchmarks.append(
                    TestParserImpl.BenchmarkStat(
                        match.group("name"),
                        cls._filename,
                        1, # Line number
                        "{}, {}".format(pytest_version, benchmark_version),
                        float(match.group("min").replace(",", "")),
                        float(match.group("max").replace(",", "")),
                        float(match.group("mean").replace(",", "")),
                        float(match.group("std_dev").replace(",", "")),
                        int(match.group("rounds")),
                        units,
                        int(match.group("iterations")),
                    ),
                )

        if benchmarks:
            return 0, { "benchmarks" : benchmarks }

        return 0

    # ----------------------------------------------------------------------
    @classmethod
    @Interface.override
    def CreateInvokeCommandLine(cls, context, debug_on_error):
        # Store the filename for later
        cls._filename = context["input"]

        command_line_prefix = 'pytest --verbose -vv --capture=no'

        if CurrentShell.CategoryName == "Windows":
            command_line_prefix += " -W ignore::DeprecationWarning:pywintypes"

        return '{} "{}"'.format(
            command_line_prefix,
            super(TestParser, cls).CreateInvokeCommandLine(context, debug_on_error),
        )
