# ----------------------------------------------------------------------
# |
# |  Results.py
# |
# |  David Brownell <db@DavidBrownell.com>
# |      2020-12-31 14:03:07
# |
# ----------------------------------------------------------------------
# |
# |  Copyright David Brownell 2020-22
# |  Distributed under the Boost Software License, Version 1.0. See
# |  accompanying file LICENSE_1_0.txt or copy at
# |  http://www.boost.org/LICENSE_1_0.txt.
# |
# ----------------------------------------------------------------------
"""Contains the Results object"""

import datetime
import os
import textwrap

from collections import namedtuple

import colorama
import six

import CommonEnvironment
from CommonEnvironment import Nonlocals, ObjectReprImpl
from CommonEnvironment import StringHelpers

from CommonEnvironment.TypeInfo.FundamentalTypes.DurationTypeInfo import DurationTypeInfo
from CommonEnvironment.TypeInfo.FundamentalTypes.Serialization.StringSerialization import (
    StringSerialization,
)

# ----------------------------------------------------------------------
_script_fullpath                            = CommonEnvironment.ThisFullpath()
_script_dir, _script_name                   = os.path.split(_script_fullpath)
# ----------------------------------------------------------------------

# ----------------------------------------------------------------------
class Results(object):
    """Results for executing a single test"""

    # ----------------------------------------------------------------------
    # |
    # |  Public Types
    # |
    # ----------------------------------------------------------------------
    class TestParseResult(object):
        # ----------------------------------------------------------------------
        def __init__(
            self,
            result,                         # : int
            time,                           # : timedelta
            benchmarks=None,                # : Dict[str, List[TestParserImpl.BenchmarkStat]]
            sub_results=None,               # : Dict[str, Tuple[int, timedelta]]
        ):
            self.Result                     = result
            self.Time                       = time
            self.Benchmarks                 = benchmarks
            self.SubResults                 = sub_results

        # ----------------------------------------------------------------------
        def __repr__(self):
            return ObjectReprImpl(self)

    # ----------------------------------------------------------------------
    class CoverageValidationResult(object):
        # ----------------------------------------------------------------------
        def __init__(
            self,
            result,                         # : int
            time,                           # : timedelta
            min,                            # : float
        ):
            self.Result                     = result
            self.Time                       = time
            self.Min                        = min

        # ----------------------------------------------------------------------
        def __repr__(self):
            return ObjectReprImpl(self)

    # ----------------------------------------------------------------------
    # |
    # |  Public Methods
    # |
    # ----------------------------------------------------------------------
    def __init__(self):
        self.compiler_context               = None

        self.compile_binary                 = None
        self.compile_result                 = None
        self.compile_log                    = None
        self.compile_time                   = None

        self.has_errors                     = False

        self.execute_results                = []        # TestExecutorImpl.ExecuteResult
        self.test_parse_results             = []        # TestParseResult
        self.coverage_validation_results    = []        # CoverageValidationResult

    # ----------------------------------------------------------------------
    def __repr__(self):
        return ObjectReprImpl(self)

    # ----------------------------------------------------------------------
    def ResultCode(self):
        if self.compile_result is None or self.compile_result < 0:
            return self.compile_result

        nonlocals = Nonlocals(
            result=self.compile_result,
        )

        # ----------------------------------------------------------------------
        def ApplyResult(result):
            if result is not None:
                if result < 0:
                    nonlocals.result = result
                    return False

                if nonlocals.result in [None, 0]:
                    nonlocals.result = result

            return True

        # ----------------------------------------------------------------------

        for execute_result, test_parse_result, coverage_validation_result in zip(
            self.execute_results,
            self.test_parse_results,
            self.coverage_validation_results,
        ):
            if execute_result is not None:
                should_continue = True

                for item_result in [
                    execute_result.TestResult,
                    execute_result.CoverageResult,
                ]:
                    if not ApplyResult(item_result):
                        should_continue = False
                        break

                if not should_continue:
                    break

            if test_parse_result is not None and not ApplyResult(
                test_parse_result.Result,
            ):
                break

            if coverage_validation_result is not None and not ApplyResult(
                coverage_validation_result.Result,
            ):
                break

        return nonlocals.result

    # ----------------------------------------------------------------------
    def ToString(
        self,
        compiler,
        test_parser,
        optional_test_executor,
        optional_code_coverage_validator,
        include_benchmarks=False,
        include_subresults=False,
    ):
        # ----------------------------------------------------------------------
        def ResultToString(result):
            if result is None:
                result = "{}N/A".format(colorama.Style.DIM)
            elif result == 0:
                result = "{}{}Succeeded".format(
                    colorama.Fore.GREEN,
                    colorama.Style.BRIGHT,
                )
            elif result < 0:
                result = "{}{}Failed ({})".format(
                    colorama.Fore.RED,
                    colorama.Style.BRIGHT,
                    result,
                )
            elif result > 0:
                result = "{}{}Unknown ({})".format(
                    colorama.Fore.YELLOW,
                    colorama.Style.BRIGHT,
                    result,
                )
            else:
                assert False, result

            return "{}{}".format(result, colorama.Style.RESET_ALL)

        # ----------------------------------------------------------------------

        results = [
            "{color_push}{compiler}{test_parser}{executor}{validator}{color_pop}\n\n".format(
                color_push="{}{}".format(colorama.Fore.WHITE, colorama.Style.BRIGHT),
                color_pop=colorama.Style.RESET_ALL,
                compiler="Compiler:                                       {}\n".format(
                    compiler.Name,
                ),
                test_parser="Test Parser:                                    {}\n".format(
                    test_parser.Name,
                ),
                executor="Test Executor:                                  {}\n".format(
                    optional_test_executor.Name,
                ) if optional_test_executor else "",
                validator="Code Coverage Validator:                        {}\n".format(
                    optional_code_coverage_validator.Name,
                ) if optional_code_coverage_validator else "",
            ),
        ]

        result_code = self.ResultCode()
        if result_code is None:
            return "Result:                                         {}\n".format(
                ResultToString(result_code),
            )

        results.append(
            textwrap.dedent(
                """\
                Result:                                         {result_code}

                Compile Result:                                 {compile_result}
                Compile Binary:                                 {compile_binary}
                Compile Log Filename:                           {compile_log}
                Compile Time:                                   {compile_time}

                """,
            ).format(
                result_code=ResultToString(result_code),
                compile_result=ResultToString(self.compile_result),
                compile_binary=self.compile_binary or "N/A",
                compile_log=self.compile_log or "N/A",
                compile_time=self.compile_time or "N/A",
            ),
        )

        for (
            index,
            (execute_result, test_parse_result, coverage_validation_result),
        ) in enumerate(
            zip(
                self.execute_results,
                self.test_parse_results,
                self.coverage_validation_results,
            ),
        ):
            if (
                not execute_result
                and not test_parse_result
                and not coverage_validation_result
            ):
                continue

            header = "Iteration #{}".format(index + 1)
            results.append("{}\n{}\n".format(header, "-" * len(header)))

            if execute_result:
                results.append(
                    StringHelpers.LeftJustify(
                        textwrap.dedent(
                            # <Wrong hanging indentation> pylint: disable = C0330
                            """\
                                Test Execution Result:                      {test_result}
                                Test Execution Log Filename:                {test_log}
                                Test Execution Time:                        {test_time}

                            """,
                        ).format(
                            test_result=ResultToString(execute_result.TestResult),
                            test_log=execute_result.TestOutput,
                            test_time=execute_result.TestTime,
                        ),
                        4,
                        skip_first_line=False,
                    ),
                )

            if test_parse_result:
                results.append(
                    StringHelpers.LeftJustify(
                        textwrap.dedent(
                            # <Wrong hanging indentation> pylint: disable = C0330
                            """\
                            Test Parse Result:                          {test_parse_result}
                            Test Parse Time:                            {test_parse_time}
                            """,
                        ).format(
                            test_parse_result=ResultToString(test_parse_result.Result),
                            test_parse_time=test_parse_result.Time,
                        ),
                        4,
                        skip_first_line=False,
                    ),
                )

                if test_parse_result.SubResults and include_subresults:
                    results.append("    Test Parse Subtests:\n")

                    display_template = "            - {subtest_name} ({result_code}, {result_time})\n"

                    for subtest_name, (result_code, result_time) in six.iteritems(test_parse_result.SubResults):
                        results.append(
                            display_template.format(
                                result_code=result_code,
                                subtest_name=subtest_name,
                                result_time=result_time,
                            ),
                        )

                if test_parse_result.Benchmarks and include_benchmarks:
                    results.append("    Test Parse Benchmarks:\n")

                    for benchmark_name, benchmarks in six.iteritems(
                        test_parse_result.Benchmarks,
                    ):
                        results.append("        {}:\n".format(benchmark_name))

                        for benchmark in benchmarks:
                            results.append(
                                StringHelpers.LeftJustify(
                                    textwrap.dedent(
                                        """\
                                        {name} [{extractor}]
                                            {source_filename} <{source_line}>
                                                Iterations:             {iterations}
                                                Samples:                {samples}

                                                Mean:                   {mean} {units}
                                                Min:                    {min} {units}
                                                Max:                    {max} {units}
                                                Standard Deviation:     {standard_deviation}

                                        """,
                                    ).format(
                                        name=benchmark.Name,
                                        extractor=benchmark.Extractor,
                                        source_filename=benchmark.SourceFilename,
                                        source_line=benchmark.SourceLine,
                                        iterations=benchmark.Iterations,
                                        samples=benchmark.Samples,
                                        mean=benchmark.Mean,
                                        min=benchmark.Min,
                                        max=benchmark.Max,
                                        standard_deviation=benchmark.StandardDeviation,
                                        units=benchmark.Units,
                                    ),
                                    12,
                                    skip_first_line=False,
                                ),
                            )

                results.append("\n")

            if execute_result and execute_result.CoverageResult is not None:
                # ----------------------------------------------------------------------
                def GetPercentageInfo():
                    if execute_result.CoveragePercentages is None:
                        return "N/A"

                    output = []

                    display_template = "        - [{value:<7}] {name:<30}{suffix}"

                    for name, percentage_info in six.iteritems(
                        execute_result.CoveragePercentages,
                    ):
                        if isinstance(percentage_info, tuple):
                            percentage, suffix = percentage_info
                        else:
                            percentage = percentage_info
                            suffix = None

                        output.append(
                            display_template.format(
                                value="N/A" if percentage is None else "{0:0.2f}%".format(percentage),
                                name=name,
                                suffix="" if not suffix else " ({})".format(suffix),
                            ),
                        )

                    return "\n{}".format("\n".join(output))

                # ----------------------------------------------------------------------

                results.append(
                    StringHelpers.LeftJustify(
                        textwrap.dedent(
                            # <Wrong hanging indentation> pylint: disable = C0330
                            """\
                            Code Coverage Result:                       {result}
                            Code Coverage Log Filename:                 {log}
                            Code Coverage Execution Time:               {time}
                            Code Coverage Data Filename:                {data}
                            Code Coverage Percentage:                   {percentage}
                            Code Coverage Percentages:                  {percentages}

                            """,
                        ).format(
                            result=ResultToString(execute_result.CoverageResult),
                            log=execute_result.CoverageOutput or "N/A",
                            time=execute_result.CoverageTime or "N/A",
                            data=execute_result.CoverageDataFilename or "N/A",
                            percentage="{0:0.2f}%".format(
                                execute_result.CoveragePercentage,
                            ) if execute_result.CoveragePercentage is not None else "N/A",
                            percentages=GetPercentageInfo(),
                        ),
                        4,
                        skip_first_line=False,
                    ),
                )

            if coverage_validation_result:
                results.append(
                    StringHelpers.LeftJustify(
                        textwrap.dedent(
                            # <Wrong hanging indentation> pylint: disable = C0330
                            """\
                            Code Coverage Validation Result:            {result}
                            Code Coverage Validation Time:              {time}
                            Code Coverage Minimum Percentage:           {min}

                            """,
                        ).format(
                            result=ResultToString(coverage_validation_result.Result),
                            time=coverage_validation_result.Time,
                            min="N/A" if coverage_validation_result.Min is None else "{}%".format(
                                coverage_validation_result.Min,
                            ),
                        ),
                        4,
                        skip_first_line=False,
                    ),
                )
        return "".join(results)

    # ----------------------------------------------------------------------
    def TotalTime(
        self,
        as_string=True,
    ):
        dti = DurationTypeInfo()

        total_time = datetime.timedelta(
            seconds=0,
        )

        get_duration = lambda duration: StringSerialization.DeserializeItem(
            dti,
            duration,
        ) if duration is not None else datetime.timedelta(
            seconds=0,
        )

        total_time += get_duration(self.compile_time)

        # ----------------------------------------------------------------------
        def CalculateTime(items, attr_name):
            total_time = datetime.timedelta(
                seconds=0,
            )

            for item in items:
                value = getattr(item, attr_name, None)
                if value is not None:
                    total_time += get_duration(value)

            return total_time

        # ----------------------------------------------------------------------

        total_time += CalculateTime(self.execute_results, "TestTime")
        total_time += CalculateTime(self.execute_results, "CoverageTime")
        total_time += CalculateTime(self.test_parse_results, "Time")
        total_time += CalculateTime(self.coverage_validation_results, "Time")

        if as_string:
            total_time = StringSerialization.SerializeItem(dti, total_time)

        return total_time
