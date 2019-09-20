# ----------------------------------------------------------------------
# |
# |  Tester.py
# |
# |  David Brownell <db@DavidBrownell.com>
# |      2018-05-21 21:44:34
# |
# ----------------------------------------------------------------------
# |
# |  Copyright David Brownell 2018-19.
# |  Distributed under the Boost Software License, Version 1.0.
# |  (See accompanying file LICENSE_1_0.txt or copy at http://www.boost.org/LICENSE_1_0.txt)
# |
# ----------------------------------------------------------------------
"""General purpose test executor."""

import datetime
import multiprocessing
import os
import re
import sys
import textwrap
import threading
import time
import traceback

from collections import OrderedDict, namedtuple

import colorama
import six
import inflect as inflect_mod

import CommonEnvironment
from CommonEnvironment import Nonlocals, ObjectReprImpl
from CommonEnvironment.CallOnExit import CallOnExit
from CommonEnvironment import CommandLine
from CommonEnvironment import FileSystem
from CommonEnvironment.Shell.All import CurrentShell
from CommonEnvironment import StringHelpers
from CommonEnvironment.StreamDecorator import StreamDecorator
from CommonEnvironment import TaskPool
from CommonEnvironment.TestExecutorImpl import TestExecutorImpl
from CommonEnvironment.TestTypeMetadata import TEST_TYPES

from CommonEnvironment.TypeInfo.FundamentalTypes.DirectoryTypeInfo import (
    DirectoryTypeInfo,
)
from CommonEnvironment.TypeInfo.FundamentalTypes.DurationTypeInfo import DurationTypeInfo
from CommonEnvironment.TypeInfo.FundamentalTypes.FilenameTypeInfo import FilenameTypeInfo
from CommonEnvironment.TypeInfo.FundamentalTypes.Serialization.StringSerialization import (
    StringSerialization,
)

# ----------------------------------------------------------------------
_script_fullpath                            = CommonEnvironment.ThisFullpath()
_script_dir, _script_name                   = os.path.split(_script_fullpath)
# ----------------------------------------------------------------------

assert os.getenv("DEVELOPMENT_ENVIRONMENT_FUNDAMENTAL")
sys.path.insert(0, os.getenv("DEVELOPMENT_ENVIRONMENT_FUNDAMENTAL"))
with CallOnExit(lambda: sys.path.pop(0)):
    from RepositoryBootstrap.SetupAndActivate import DynamicPluginArchitecture as DPA

# ----------------------------------------------------------------------
# <Too many lines in module> pylint: disable = C0302

_TEMP_DIR_OVERRIDE_ENVIRONMENT_NAME         = "DEVELOPMENT_ENVIRONMENT_TESTER_TEMP_DIRECTORY"

StreamDecorator.InitAnsiSequenceStreams()
inflect                                     = inflect_mod.engine()

# ----------------------------------------------------------------------
# ----------------------------------------------------------------------
# ----------------------------------------------------------------------
TEST_IGNORE_FILENAME_TEMPLATE               = "{}-ignore"

# ----------------------------------------------------------------------
def _LoadCompilerFromModule(mod):
    for potential_name in ["Compiler", "CodeGenerator", "Verifier"]:
        result = getattr(mod, potential_name, None)
        if result is not None:
            return result()

    assert False, mod
    return None


# ----------------------------------------------------------------------

COMPILERS                                   = [
    _LoadCompilerFromModule(mod)
    for mod in DPA.EnumeratePlugins("DEVELOPMENT_ENVIRONMENT_COMPILERS")
]
TEST_EXECUTORS                              = [
    mod.TestExecutor()
    for mod in DPA.EnumeratePlugins("DEVELOPMENT_ENVIRONMENT_TEST_EXECUTORS")
]
TEST_PARSERS                                = [
    mod.TestParser()
    for mod in DPA.EnumeratePlugins("DEVELOPMENT_ENVIRONMENT_TEST_PARSERS")
]
CODE_COVERAGE_VALIDATORS                    = [
    mod.CodeCoverageValidator()
    for mod in DPA.EnumeratePlugins("DEVELOPMENT_ENVIRONMENT_CODE_COVERAGE_VALIDATORS")
]

# Extract configuration-specific information from other repositories. This ensures that this file,
# which is in the fundamental repo, doesn't take a dependency on repos that depend on this one.
#
# Expected format is a list of items delimited by the os-specific delimiter stored in an
# environment variable. Each item is in the form:
#
#       "<configuration name>-<compiler|test_parser|coverage_executor|coverage_validator>-<value>"

# ----------------------------------------------------------------------
def _CreateConfigurations():
    configurations = OrderedDict()

    custom_configurations = os.getenv("DEVELOPMENT_ENVIRONMENT_TESTER_CONFIGURATIONS")
    if custom_configurations:
        # ----------------------------------------------------------------------
        class Configuration(object):
            # ----------------------------------------------------------------------
            @classmethod
            def Create(
                cls,
                configuration_name,
                compiler_name,
                test_parser_name,
                coverage_executor_name,
                coverage_validator_name,
            ):
                compiler = next(
                    (
                        compiler
                        for compiler in COMPILERS
                        if compiler.Name == compiler_name
                    ),
                    None,
                )
                if compiler is None:
                    raise Exception(
                        "The compiler '{}' used in the configuration '{}' does not exist".format(
                            compiler_name,
                            configuration_name,
                        ),
                    )

                test_parser = next(
                    (
                        test_parser
                        for test_parser in TEST_PARSERS
                        if test_parser.Name == test_parser_name
                    ),
                    None,
                )
                if test_parser is None:
                    raise Exception(
                        "The test parser '{}' used in the configuration '{}' does not exist".format(
                            test_parser_name,
                            configuration_name,
                        ),
                    )

                if coverage_executor_name:
                    coverage_executor = next(
                        (
                            executor
                            for executor in TEST_EXECUTORS
                            if executor.Name == coverage_executor_name
                        ),
                        None,
                    )
                    if coverage_executor is None:
                        raise Exception(
                            "The test executor '{}' used in the configuration '{}' does not exist".format(
                                coverage_executor_name,
                                configuration_name,
                            ),
                        )
                else:
                    coverage_executor = None

                if coverage_validator_name:
                    coverage_validator = next(
                        (
                            validator
                            for validator in CODE_COVERAGE_VALIDATORS
                            if validator.Name == coverage_validator_name
                        ),
                        None,
                    )
                    if coverage_validator is None:
                        raise Exception(
                            "The coverage validator '{}' used in the configuration '{}' does not exist".format(
                                coverage_validator_name,
                                configuration_name,
                            ),
                        )
                else:
                    coverage_validator = None

                return cls(compiler, test_parser, coverage_executor, coverage_validator)

            # ----------------------------------------------------------------------
            def __init__(
                self,
                compiler,
                test_parser,
                optional_coverage_executor,
                optional_code_coverage_validator=None,
            ):
                assert compiler
                assert test_parser

                self.Compiler                           = compiler
                self.TestParser                         = test_parser
                self.OptionalCoverageExecutor           = (
                    optional_coverage_executor if optional_coverage_executor else None
                )
                self.OptionalCodeCoverageValidator      = (
                    optional_code_coverage_validator
                    if optional_code_coverage_validator
                    else None
                )

        # ----------------------------------------------------------------------

        regex = re.compile(
            textwrap.dedent(
                # <Wrong hanging indentation> pylint: disable = C0330
                r"""(?#
                        )\s*"?(?#
            Name        )(?P<name>.+?)(?#
                        )\s*-\s*(?#
            Type        )(?P<type>(?:compiler|test_parser|coverage_executor|coverage_validator))(?#
                        )\s*-\s*(?#
            Value       )(?P<value>[^"]+)(?#
                        )"?\s*(?#
            )""",
            ),
        )

        configuration_map = OrderedDict()

        for configuration in [
            item for item in custom_configurations.split(os.pathsep) if item.strip()
        ]:
            match = regex.match(configuration)
            assert match, configuration

            configuration_name = match.group("name").lower()
            type_ = match.group("type")
            value = match.group("value")

            if configuration_name not in configuration_map:
                configuration_map[configuration_name] = {}

            if type_ in configuration_map[configuration_name]:
                if not isinstance(configuration_map[configuration_name][type_], list):
                    configuration_map[configuration_name][type_] = [
                        configuration_map[configuration_name][type_],
                    ]

                configuration_map[configuration_name][type_].append(value)
            else:
                configuration_map[configuration_name][type_] = value

        # ----------------------------------------------------------------------
        def GetFirstItem(item_or_items):
            if isinstance(item_or_items, list):
                item_or_items = item_or_items[0]

            return item_or_items

        # ----------------------------------------------------------------------

        for item_key, item_map in six.iteritems(configuration_map):
            # compiler and test parser are required
            if "compiler" not in item_map or "test_parser" not in item_map:
                continue

            if isinstance(item_map["compiler"], list):
                compiler_info = [
                    ("{}-{}".format(item_key, compiler), compiler)
                    for compiler in item_map["compiler"]
                ]
            elif isinstance(item_map["compiler"], six.string_types):
                compiler_info = [(item_key, item_map["compiler"])]
            else:
                assert False, type(item_map["compiler"])

            for compiler_key, compiler in compiler_info:
                configurations[compiler_key] = Configuration.Create(
                    compiler_key,
                    compiler,
                    GetFirstItem(item_map["test_parser"]),
                    GetFirstItem(item_map.get("coverage_executor", None)),
                    GetFirstItem(item_map.get("coverage_validator", None)),
                )
    return configurations


# ----------------------------------------------------------------------

CONFIGURATIONS                              = _CreateConfigurations()
del _CreateConfigurations

# ----------------------------------------------------------------------
# |
# |  Public Types
# |
# ----------------------------------------------------------------------
class Results(object):
    """Results for executing a single test"""

    # ----------------------------------------------------------------------
    # |  Public Types
    TestParseResult                         = namedtuple("TestParseResult", ["Result", "Time"])

    CoverageValidationResult                = namedtuple(
        "CoverageValidationResult",
        ["Result", "Time", "Min"],
    )

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
                                value="{0:0.2f}%".format(percentage),
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
    def TotalTime(self):
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
        def Average(items, attr_name):
            num_items = 0
            total_time = datetime.timedelta(
                seconds=0,
            )

            for item in items:
                value = getattr(item, attr_name, None)
                if value is not None:
                    num_items += 1
                    total_time += get_duration(value)

            if num_items == 0:
                return total_time

            return total_time / num_items

        # ----------------------------------------------------------------------

        total_time += Average(self.execute_results, "TestTime")
        total_time += Average(self.execute_results, "CoverageTime")
        total_time += Average(self.test_parse_results, "Time")
        total_time += Average(self.coverage_validation_results, "Time")

        return StringSerialization.SerializeItem(dti, total_time)


# ----------------------------------------------------------------------
class CompleteResult(object):
    """Results for both debug and release builds"""

    # ----------------------------------------------------------------------
    def __init__(self, item):
        self.Item                           = item
        self.debug                          = Results()
        self.release                        = Results()

    # ----------------------------------------------------------------------
    def __repr__(self):
        return ObjectReprImpl(self)

    # ----------------------------------------------------------------------
    def ResultCode(self):
        result = None

        for results in [self.debug, self.release]:
            this_result = results.ResultCode()
            if this_result is None:
                continue

            if this_result < 0:
                result = this_result
                break
            elif result in [None, 0]:
                result = this_result

        return result

    # ----------------------------------------------------------------------
    def ToString(
        self,
        compiler,
        test_parser,
        optional_test_executor,
        optional_code_coverage_validator,
    ):
        header_length = max(180, len(self.Item) + 4)

        return textwrap.dedent(
            """\
            {color_push}{header}
            |{item:^{item_length}}|
            {header}{color_pop}

            {color_push}DEBUG:{color_pop}
            {debug}

            {color_push}RELEASE:{color_pop}
            {release}

            """,
        ).format(
            color_push="{}{}".format(colorama.Fore.WHITE, colorama.Style.BRIGHT),
            color_pop=colorama.Style.RESET_ALL,
            header="=" * header_length,
            item=self.Item,
            item_length=header_length - 2,
            debug="N/A" if not self.debug else StringHelpers.LeftJustify(
                self.debug.ToString(
                    compiler,
                    test_parser,
                    optional_test_executor,
                    optional_code_coverage_validator,
                ),
                4,
                skip_first_line=False,
            ).rstrip(),
            release="N/A" if not self.release else StringHelpers.LeftJustify(
                self.release.ToString(
                    compiler,
                    test_parser,
                    optional_test_executor,
                    optional_code_coverage_validator,
                ),
                4,
                skip_first_line=False,
            ).rstrip(),
        )


# ----------------------------------------------------------------------
# |
# |  Public Methods
# |
# ----------------------------------------------------------------------
def ExtractTestItems(
    input_dir,
    test_subdir,
    compiler,
    verbose_stream=None,
):
    assert os.path.isdir(input_dir), input_dir
    assert test_subdir
    assert compiler

    verbose_stream = StreamDecorator(
        verbose_stream,
        prefix="\n",
        line_prefix="  ",
    )

    traverse_exclude_dir_names = ["Generated"]

    test_items = []

    if isinstance(compiler.InputTypeInfo, FilenameTypeInfo):
        for fullpath in FileSystem.WalkFiles(
            input_dir,
            include_dir_names=[test_subdir],
            traverse_exclude_dir_names=traverse_exclude_dir_names,
        ):
            if os.path.exists(TEST_IGNORE_FILENAME_TEMPLATE.format(fullpath)):
                continue

            if compiler.IsSupported(fullpath) and compiler.IsSupportedTestItem(fullpath):
                test_items.append(fullpath)
            else:
                verbose_stream.write(
                    "'{}' is not supported by the compiler.\n".format(fullpath),
                )

    elif isinstance(compiler.InputTypeInfo, DirectoryTypeInfo):
        for root, _ in FileSystem.WalkDirs(
            input_dir,
            include_dir_names=[test_subdir],
            traverse_exclude_dir_names=traverse_exclude_dir_names,
        ):
            if os.path.exists(TEST_IGNORE_FILENAME_TEMPLATE.format(root)):
                continue

            if compiler.IsSupported(root) and compiler.IsSupportedTestItem(root):
                test_items.append(root)
            else:
                verbose_stream.write(
                    "'{}' is not supported by the compiler.\n".format(root),
                )

    else:
        assert False, (compiler.Name, compiler.InputTypeInfo)

    return test_items

# ----------------------------------------------------------------------
def GenerateTestResults(
    test_items,
    output_dir,
    compiler,
    test_parser,
    optional_test_executor,
    optional_code_coverage_validator,
    execute_in_parallel,
    iterations,
    debug_on_error,
    continue_iterations_on_error,
    debug_only,
    release_only,
    output_stream,
    verbose,
    no_status,
    max_num_concurrent_tasks=multiprocessing.cpu_count(),
):
    assert test_items
    assert output_dir
    assert compiler
    assert test_parser
    assert iterations > 0, iterations
    assert output_stream
    assert max_num_concurrent_tasks > 0, max_num_concurrent_tasks

    # Check for congruent plugins
    result = compiler.ValidateEnvironment()
    if result:
        output_stream.write(
            "ERROR: The current environment is not supported by the compiler '{}': {}.\n".format(
                compiler.Name,
                result,
            ),
        )
        return None

    if not test_parser.IsSupportedCompiler(compiler):
        raise Exception(
            "The test parser '{}' does not support the compiler '{}'.".format(
                test_parser.Name,
                compiler.Name,
            ),
        )

    if optional_test_executor:
        result = optional_test_executor.ValidateEnvironment()
        if result:
            output_stream.write(
                "ERROR: The current environment is not supported by the test executor '{}': {}.\n".format(
                    optional_test_executor.Name,
                    result,
                ),
            )
            return None

        if not optional_test_executor.IsSupportedCompiler(compiler):
            raise Exception(
                "The test executor '{}' does not support the compiler '{}'.".format(
                    optional_test_executor.Name,
                    compiler.Name,
                ),
            )

    if optional_code_coverage_validator and not optional_test_executor:
        raise Exception(
            "A code coverage validator cannot be used without a test executor",
        )

    FileSystem.MakeDirs(output_dir)

    # Ensure that we only build the debug configuration with code coverage
    if optional_test_executor:
        execute_in_parallel = False

        if compiler.IsCompiler:
            debug_only = True
            release_only = False

    internal_exception_result_code = 54321

    # ----------------------------------------------------------------------
    # |  Prepare the working data
    WorkingData = namedtuple(
        "ResultsWorkingData",
        ["complete_result", "output_dir", "execution_lock"],
    )

    working_data_items = []

    if len(test_items) == 1:
        common_prefix = FileSystem.GetCommonPath(
            test_items[0],
            os.path.abspath(os.getcwd()),
        )
    else:
        common_prefix = FileSystem.GetCommonPath(*test_items)

    for test_item in test_items:
        if not compiler.IsSupported(test_item):
            continue

        # The base name used for all output for this particular test is based on the name of
        # the test itself.
        output_name = FileSystem.TrimPath(test_item, common_prefix)

        for bad_char in [
            "\\",
            "/",
            ":",
            "*",
            "?",
            '"',
            "<",
            ">",
            "|",
        ]:
            output_name = output_name.replace(bad_char, "_")

        working_data_items.append(
            WorkingData(
                CompleteResult(test_item),
                os.path.join(output_dir, output_name),
                threading.Lock(),
            ),
        )

    # ----------------------------------------------------------------------
    # |  Build

    # Prepare the context
    for working_data in working_data_items:
        # ----------------------------------------------------------------------
        def PopulateResults(results, configuration):
            output_dir = os.path.join(working_data.output_dir, configuration)

            FileSystem.RemoveTree(output_dir)
            FileSystem.MakeDirs(output_dir)

            if compiler.IsVerifier:
                results.compiler_binary = working_data.complete_result.Item
            else:
                results.compiler_binary = os.path.join(output_dir, "test")

                ext = getattr(compiler, "BinaryExtension", None)
                if ext:
                    results.compiler_binary += ext

            results.compile_log = os.path.join(output_dir, "compile.txt")
            results.compiler_context = output_dir

        # ----------------------------------------------------------------------

        if not release_only or not compiler.IsCompiler:
            PopulateResults(working_data.complete_result.debug, "Debug")

        if not debug_only and compiler.IsCompiler:
            PopulateResults(working_data.complete_result.release, "Release")

    # Execute the build in parallel
    nonlocals = Nonlocals(
        build_failures=0,
    )
    build_failures_lock = threading.Lock()

    # ----------------------------------------------------------------------
    def BuildThreadProc(task_index, output_stream, on_status_update):
        working_data = working_data_items[task_index % len(working_data_items)]

        if task_index >= len(working_data_items):
            configuration_results = working_data.complete_result.release
            is_debug = False
        else:
            configuration_results = working_data.complete_result.debug
            is_debug = True

        if configuration_results.compiler_context is None:
            return 0

        compile_result = None
        compile_output = ""
        start_time = time.time()

        try:
            # Create the compiler context
            if not no_status:
                on_status_update("Configuring")

            assert os.path.isdir(
                configuration_results.compiler_context,
            ), configuration_results.compiler_context

            configuration_results.compiler_context = compiler.GetContextItem(
                working_data.complete_result.Item,
                six.moves.StringIO(),
                is_debug=is_debug,
                is_profile=bool(optional_test_executor),
                output_filename=configuration_results.compile_binary,
                output_dir=configuration_results.compiler_context,
                force=True,
            )

            if configuration_results.compiler_context is None:
                configuration_results.compile_binary = None
                return None

            if not no_status:
                on_status_update("Waiting")

            with working_data.execution_lock:
                if not no_status:
                    on_status_update("Building")

                sink = six.moves.StringIO()

                if compiler.IsCompiler:
                    compile_result = compiler.Compile(
                        configuration_results.compiler_context,
                        sink,
                        verbose=verbose,
                    )
                    compiler.RemoveTemporaryArtifacts(
                        configuration_results.compiler_context,
                    )
                elif compiler.IsCodeGenerator:
                    compile_result = compiler.Generate(
                        configuration_results.compiler_context,
                        sink,
                        verbose=verbose,
                    )
                elif compiler.IsVerifier:
                    compile_result = compiler.Verify(
                        configuration_results.compiler_context,
                        sink,
                        verbose=verbose,
                    )
                else:
                    assert False, compiler.Name

                compile_output = sink.getvalue()

                if compile_result != 0:
                    output_stream.write(compile_output)

        except:
            compile_result = internal_exception_result_code
            compile_output = traceback.format_exc()

            raise

        finally:
            configuration_results.compile_result = compile_result
            configuration_results.compile_time = str(
                datetime.timedelta(
                    seconds=(time.time() - start_time),
                ),
            )

            with open(configuration_results.compile_log, "w") as f:
                f.write(compile_output.replace("\r\n", "\n"))

            if compile_result != 0:
                with build_failures_lock:
                    nonlocals.build_failures += 1

        return compile_result

    # ----------------------------------------------------------------------

    debug_tasks = []
    release_tasks = []

    for working_data in working_data_items:
        # Rather than add the tasks back-to-back, add all of the debug tasks followed by
        # all of the release tasks. This will help to avoid potential build issues associated
        # with building the same binary that has slightly different output.
        debug_tasks.append(
            TaskPool.Task(
                "{} [Debug]".format(working_data.complete_result.Item),
                BuildThreadProc,
            ),
        )
        release_tasks.append(
            TaskPool.Task(
                "{} [Release]".format(working_data.complete_result.Item),
                BuildThreadProc,
            ),
        )

    with output_stream.SingleLineDoneManager(
        "Building...",
        done_suffix=lambda: inflect.no("build failure", nonlocals.build_failures),
    ) as this_dm:
        result = TaskPool.Execute(
            debug_tasks + release_tasks,
            this_dm.stream,
            progress_bar=True,
            display_errors=verbose,
            num_concurrent_tasks=max_num_concurrent_tasks,
        )

    # ----------------------------------------------------------------------
    # |  Execute

    # ----------------------------------------------------------------------
    def TestThreadProc(
        output_stream,
        on_status_update,
        working_data,
        configuration_results,
        configuration,
        iteration,
    ):
        # Don't continue on error unless explicitly requested
        if not continue_iterations_on_error and configuration_results.has_errors:
            return

        if no_status:
            on_status_update = lambda value: None

        # ----------------------------------------------------------------------
        def Invoke():
            # ----------------------------------------------------------------------
            def WriteLog(log_name, content):
                if content is None:
                    return None

                log_filename = os.path.join(
                    working_data.output_dir,
                    configuration,
                    "{0}.{1:06d}.txt".format(log_name, iteration + 1),
                )

                with open(log_filename, "w") as f:
                    try:
                        content = content.replace("\r\n", "\n")
                    except UnicodeDecodeError:
                        # Use the content unmodified
                        pass

                    f.write(content)

                return log_filename

            # ----------------------------------------------------------------------

            # Run the test...
            on_status_update("Testing")

            execute_result = None
            execute_start_time = time.time()

            try:
                test_command_line = test_parser.CreateInvokeCommandLine(
                    configuration_results.compiler_context,
                    debug_on_error,
                )

                if optional_test_executor:
                    executor = optional_test_executor
                else:
                    executor = next(
                        executor
                        for executor in TEST_EXECUTORS
                        if executor.Name == "Standard",
                    )

                execute_result = executor.Execute(
                    on_status_update,
                    compiler,
                    configuration_results.compiler_context,
                    test_command_line,
                )

                test_parser.RemoveTemporaryArtifacts(
                    configuration_results.compiler_context,
                )

                if (
                    execute_result.TestResult is not None
                    and execute_result.TestResult != 0
                ):
                    output_stream.write(execute_result.TestOutput)

            except:
                execute_result = TestExecutorImpl.ExecuteResult(
                    internal_exception_result_code,
                    traceback.format_exc(),
                    None,                   # Populate below
                )
                raise

            finally:
                assert execute_result

                if execute_result.TestTime is None:
                    execute_result.TestTime = str(
                        datetime.timedelta(
                            seconds=(time.time() - execute_start_time),
                        ),
                    )

                original_test_output = execute_result.TestOutput

                execute_result.TestOutput = WriteLog("test", execute_result.TestOutput)
                execute_result.CoverageOutput = WriteLog(
                    "executor",
                    execute_result.CoverageOutput,
                )

                configuration_results.execute_results[iteration] = execute_result

                if execute_result.TestResult != 0:
                    configuration_results.has_errors = True

            # Parse the results...
            on_status_update("Parsing")

            parse_start_time = time.time()

            try:
                if original_test_output is None:
                    test_parse_result = -1
                else:
                    test_parse_result = test_parser.Parse(original_test_output)

            except:
                test_parse_result = internal_exception_result_code
                raise

            finally:
                test_parse_time = str(
                    datetime.timedelta(
                        seconds=(time.time() - parse_start_time),
                    ),
                )

                configuration_results.test_parse_results[
                    iteration
                ] = Results.TestParseResult(test_parse_result, test_parse_time)

                if test_parse_result != 0:
                    configuration_results.has_errors = True

            # Validate code coverage metrics...
            if optional_code_coverage_validator:
                on_status_update("Validating Code Coverage")

                validate_start_time = time.time()

                try:
                    if execute_result.CoveragePercentage is None:
                        validation_result = -1
                        validation_min = None
                    else:
                        validation_result, validation_min = optional_code_coverage_validator.Validate(
                            working_data.complete_result.Item,
                            execute_result.CoveragePercentage,
                        )
                except:
                    validation_result = internal_exception_result_code
                    validation_min = None

                    raise

                finally:
                    validation_parse_time = str(
                        datetime.timedelta(
                            seconds=(time.time() - validate_start_time),
                        ),
                    )

                    configuration_results.coverage_validation_results[
                        iteration
                    ] = Results.CoverageValidationResult(
                        validation_result,
                        validation_parse_time,
                        validation_min,
                    )

                    if validation_result != 0:
                        configuration_results.has_errors = True

        # ----------------------------------------------------------------------

        on_status_update("Waiting")

        if not execute_in_parallel:
            with working_data.execution_lock:
                Invoke()
        else:
            Invoke()

    # ----------------------------------------------------------------------

    debug_tasks = []
    release_tasks = []

    # ----------------------------------------------------------------------
    def EnqueueTestIfNecessary(
        iteration,
        working_data,
        configuration_results,
        configuration,
    ):
        if (
            configuration_results.compiler_context is None
            or configuration_results.compile_result != 0
        ):
            return

        if iteration == 0:
            configuration_results.execute_results = [None] * iterations
            configuration_results.test_parse_results = [None] * iterations
            configuration_results.coverage_validation_results = [None] * iterations

        if configuration == "Debug":
            task_list = debug_tasks
        elif configuration == "Release":
            task_list = release_tasks
        else:
            assert False, configuration

        # ----------------------------------------------------------------------
        # <Wrong hanging indentation> pylint: disable = C0330
        def TestThreadProcWrapper(
            # The first args must be named explicitly as TaskPool is using Interface.CreateCulledCallback
            output_stream,
            on_status_update,
            # Capture these values
            working_data=working_data,
            configuration_results=configuration_results,
            configuration=configuration,
            iteration=iteration,
        ):
            return TestThreadProc(
                output_stream,
                on_status_update,
                working_data,
                configuration_results,
                configuration,
                iteration,
            )

        # ----------------------------------------------------------------------

        task_list.append(
            TaskPool.Task(
                "{} [{}]{}".format(
                    working_data.complete_result.Item,
                    configuration,
                    "" if iterations == 1 else " <Iteration {}>".format(iteration + 1),
                ),
                TestThreadProcWrapper,
            ),
        )

    # ----------------------------------------------------------------------

    for iteration in six.moves.range(iterations):
        for working_data in working_data_items:
            EnqueueTestIfNecessary(
                iteration,
                working_data,
                working_data.complete_result.debug,
                "Debug",
            )
            EnqueueTestIfNecessary(
                iteration,
                working_data,
                working_data.complete_result.release,
                "Release",
            )

    if debug_tasks or release_tasks:
        # ----------------------------------------------------------------------
        def CountTestFailures():
            failures = 0

            for working_data in working_data_items:
                for results in [
                    working_data.complete_result.debug,
                    working_data.complete_result.release,
                ]:
                    if results.has_errors:
                        failures += 1

            return failures

        # ----------------------------------------------------------------------

        with output_stream.SingleLineDoneManager(
            "Executing...",
            done_suffix=lambda: inflect.no("test failure", CountTestFailures()),
        ) as this_dm:
            TaskPool.Execute(
                debug_tasks + release_tasks,
                this_dm.stream,
                progress_bar=True,
                display_errors=verbose,
                num_concurrent_tasks=max_num_concurrent_tasks if execute_in_parallel else 1,
            )

    return [working_data.complete_result for working_data in working_data_items]

# ----------------------------------------------------------------------
# |
# |  Command Line Functionality
# |
# ----------------------------------------------------------------------
_compiler_type_info                         = CommandLine.EnumTypeInfo(
    [compiler.Name for compiler in COMPILERS]
    + [str(index) for index in six.moves.range(1, len(COMPILERS) + 1)],
)
_test_parser_type_info                      = CommandLine.EnumTypeInfo(
    [test_parser.Name for test_parser in TEST_PARSERS]
    + [str(index) for index in six.moves.range(1, len(TEST_PARSERS) + 1)],
)
_test_executor_type_info                    = CommandLine.EnumTypeInfo(
    [executor.Name for executor in TEST_EXECUTORS] + [
        str(index) for index in six.moves.range(1, len(TEST_EXECUTORS) + 1)
    ],
    arity="?",
)
_code_coverage_validator_type_info          = CommandLine.EnumTypeInfo(
    [ccv.Name for ccv in CODE_COVERAGE_VALIDATORS] + [
        str(index) for index in six.moves.range(1, len(CODE_COVERAGE_VALIDATORS) + 1)
    ],
    arity="?",
)
_configuration_type_info                    = CommandLine.EnumTypeInfo(list(six.iterkeys(CONFIGURATIONS)))

_configuration_param_description                        = CommandLine.EntryPoint.Parameter(
    "Name for a preconfigured set of a compiler, test parser, and test executor.",
)
_input_dir_param_descripiton                            = CommandLine.EntryPoint.Parameter(
    "Input directory used to search for input.",
)
_output_dir_param_description                           = CommandLine.EntryPoint.Parameter(
    "Output directory populated with execution results.",
)
_test_type_param_description                            = CommandLine.EntryPoint.Parameter(
    "Test type that specifies the types of tests to process.",
)
_execute_in_parallel_param_description                  = CommandLine.EntryPoint.Parameter(
    "Execute tests in parallel.",
)
_iterations_param_description                           = CommandLine.EntryPoint.Parameter(
    "Execute all tests N times.",
)
_debug_on_error_param_description                       = CommandLine.EntryPoint.Parameter(
    "Launch debugging functionality upon error (if supported by the compiler).",
)
_continue_iterations_on_error_param_description         = CommandLine.EntryPoint.Parameter(
    "Continue running iterations even when errors are encountered.",
)
_code_coverage_param_description                        = CommandLine.EntryPoint.Parameter(
    "Generate code coverage information when running tests.",
)
_debug_only_param_description                           = CommandLine.EntryPoint.Parameter(
    "Only build and execute debug variants.",
)
_release_only_param_description                         = CommandLine.EntryPoint.Parameter(
    "Only build and execute release variants.",
)
_verbose_param_description                              = CommandLine.EntryPoint.Parameter("Verbose output.")
_quiet_param_description                                = CommandLine.EntryPoint.Parameter("Quiet output.")
_preserve_ansi_escape_sequences_param_description       = CommandLine.EntryPoint.Parameter(
    "Preserve ansi escape sequences when generating output (useful when invoking this functionality from another script).",
)
_no_status_param_description                            = CommandLine.EntryPoint.Parameter(
    "Do not display progress bar status when building and executing.",
)

_compiler_param_description                 = CommandLine.EntryPoint.Parameter(
    "The name or index of the compiler to use.",
)
_compiler_flag_param_description            = CommandLine.EntryPoint.Parameter(
    "Custom flags passed when creating the compiler.",
)

_test_parser_param_description              = CommandLine.EntryPoint.Parameter(
    "The name or index of the test parser to use.",
)
_test_parser_flag_param_description         = CommandLine.EntryPoint.Parameter(
    "Custom flags passed when creating the test parser.",
)

_test_executor_param_description            = CommandLine.EntryPoint.Parameter(
    "The name or index of the test executor to use.",
)
_test_executor_flag_param_description       = CommandLine.EntryPoint.Parameter(
    "Custom flags passed when creating the test executor.",
)

_code_coverage_validator_param_description              = CommandLine.EntryPoint.Parameter(
    "The name or index of the code coverage validator to use.",
)
_code_coverage_validator_flag_param_description         = CommandLine.EntryPoint.Parameter(
    "Custom flags passed when creating the code coverage validator.",
)

# ----------------------------------------------------------------------
@CommandLine.EntryPoint(
    configuration=_configuration_param_description,
    filename_or_dir=CommandLine.EntryPoint.Parameter("Filename or directory to test."),
    output_dir=_output_dir_param_description,
    test_type=_test_type_param_description,
    execute_in_parallel=_execute_in_parallel_param_description,
    iterations=_iterations_param_description,
    debug_on_error=_debug_on_error_param_description,
    continue_iterations_on_error=_continue_iterations_on_error_param_description,
    code_coverage=_code_coverage_param_description,
    debug_only=_debug_only_param_description,
    release_only=_release_only_param_description,
    verbose=_verbose_param_description,
    quiet=_quiet_param_description,
    preserve_ansi_escape_sequences=_preserve_ansi_escape_sequences_param_description,
    no_status=_no_status_param_description,
)
@CommandLine.Constraints(
    configuration=_configuration_type_info,
    filename_or_dir=CommandLine.FilenameTypeInfo(
        match_any=True,
    ),
    output_dir=CommandLine.DirectoryTypeInfo(
        ensure_exists=False,
        arity="?",
    ),
    test_type=CommandLine.StringTypeInfo(
        arity="?",
    ),
    execute_in_parallel=CommandLine.BoolTypeInfo(
        arity="?",
    ),
    iterations=CommandLine.IntTypeInfo(
        min=1,
        arity="?",
    ),
    output_stream=None,
)
def Test(
    configuration,
    filename_or_dir,
    output_dir=None,
    test_type=None,
    execute_in_parallel=None,
    iterations=1,
    debug_on_error=False,
    continue_iterations_on_error=False,
    code_coverage=False,
    debug_only=False,
    release_only=False,
    output_stream=sys.stdout,
    verbose=False,
    quiet=False,
    preserve_ansi_escape_sequences=False,
    no_status=False,
):
    """Tests the given input"""

    configuration = CONFIGURATIONS[configuration]

    if os.path.isfile(filename_or_dir) or (
        os.path.isdir(filename_or_dir)
        and configuration.Compiler.IsSupported(filename_or_dir)
    ):
        if quiet:
            raise CommandLine.UsageException(
                "'quiet' is only used when executing tests via a directory",
            )

        return _ExecuteImpl(
            filename_or_dir,
            configuration.Compiler,
            configuration.TestParser,
            configuration.OptionalCoverageExecutor if code_coverage else None,
            configuration.OptionalCodeCoverageValidator if code_coverage else None,
            execute_in_parallel=execute_in_parallel,
            iterations=iterations,
            debug_on_error=debug_on_error,
            continue_iterations_on_error=continue_iterations_on_error,
            debug_only=debug_only,
            release_only=release_only,
            output_stream=output_stream,
            verbose=verbose,
            preserve_ansi_escape_sequences=preserve_ansi_escape_sequences,
            no_status=no_status,
        )

    if test_type is None:
        raise CommandLine.UsageException(
            "The 'test_type' command line argument must be provided when 'filename_or_dir' is a directory.",
        )

    if output_dir is None:
        raise CommandLine.UsageException(
            "The 'output_dir' command line argument must be provided when 'filename_or_dir' is a directory.",
        )

    return _ExecuteTreeImpl(
        filename_or_dir,
        output_dir,
        test_type,
        configuration.Compiler,
        configuration.TestParser,
        configuration.OptionalCoverageExecutor if code_coverage else None,
        configuration.OptionalCodeCoverageValidator if code_coverage else None,
        execute_in_parallel=execute_in_parallel,
        iterations=iterations,
        debug_on_error=debug_on_error,
        continue_iterations_on_error=continue_iterations_on_error,
        debug_only=debug_only,
        release_only=release_only,
        output_stream=output_stream,
        verbose=verbose,
        quiet=quiet,
        preserve_ansi_escape_sequences=preserve_ansi_escape_sequences,
        no_status=no_status,
    )

# ----------------------------------------------------------------------
@CommandLine.EntryPoint(
    filename_or_directory=CommandLine.EntryPoint.Parameter(
        "Filename or directory to test.",
    ),
    iterations=_iterations_param_description,
    debug_on_error=_debug_on_error_param_description,
    continue_iterations_on_error=_continue_iterations_on_error_param_description,
    code_coverage=_code_coverage_param_description,
    debug_only=_debug_only_param_description,
    release_only=_release_only_param_description,
    verbose=_verbose_param_description,
    preserve_ansi_escape_sequences=_preserve_ansi_escape_sequences_param_description,
    no_status=_no_status_param_description,
)
@CommandLine.Constraints(
    filename_or_directory=CommandLine.FilenameTypeInfo(
        match_any=True,
    ),
    iterations=CommandLine.IntTypeInfo(
        min=1,
        arity="?",
    ),
    output_stream=None,
)
def TestItem(
    filename_or_directory,
    iterations=1,
    debug_on_error=False,
    continue_iterations_on_error=False,
    code_coverage=False,
    debug_only=False,
    release_only=False,
    output_stream=sys.stdout,
    verbose=False,
    preserve_ansi_escape_sequences=False,
    no_status=False,
):
    """Tests the given input file or directory (depending on the compiler invoked)"""

    # ----------------------------------------------------------------------
    def GetConfiguration():
        for key, configuration in six.iteritems(CONFIGURATIONS):
            if configuration.Compiler.IsSupported(filename_or_directory):
                return key

        return None

    # ----------------------------------------------------------------------

    configuration = GetConfiguration()
    if not configuration:
        raise CommandLine.UsageException(
            "Unable to find a configuration with a compiler that supports the input '{}'".format(
                filename_or_directory,
            ),
        )

    return Test(
        configuration,
        filename_or_directory,
        output_dir=None,
        test_type=None,
        execute_in_parallel=False,
        iterations=iterations,
        debug_on_error=debug_on_error,
        continue_iterations_on_error=continue_iterations_on_error,
        code_coverage=code_coverage,
        debug_only=debug_only,
        release_only=release_only,
        output_stream=output_stream,
        verbose=verbose,
        quiet=False,
        preserve_ansi_escape_sequences=preserve_ansi_escape_sequences,
        no_status=no_status,
    )

# ----------------------------------------------------------------------
@CommandLine.EntryPoint(
    configuration=_configuration_param_description,
    input_dir=_input_dir_param_descripiton,
    output_dir=_output_dir_param_description,
    test_type=_test_type_param_description,
    execute_in_parallel=_execute_in_parallel_param_description,
    iterations=_iterations_param_description,
    debug_on_error=_debug_on_error_param_description,
    continue_iterations_on_error=_continue_iterations_on_error_param_description,
    code_coverage=_code_coverage_param_description,
    debug_only=_debug_only_param_description,
    release_only=_release_only_param_description,
    verbose=_verbose_param_description,
    quiet=_quiet_param_description,
    preserve_ansi_escape_sequences=_preserve_ansi_escape_sequences_param_description,
    no_status=_no_status_param_description,
)
@CommandLine.Constraints(
    configuration=_configuration_type_info,
    input_dir=CommandLine.DirectoryTypeInfo(),
    output_dir=CommandLine.DirectoryTypeInfo(
        ensure_exists=False,
    ),
    test_type=CommandLine.StringTypeInfo(),
    execute_in_parallel=CommandLine.BoolTypeInfo(
        arity="?",
    ),
    iterations=CommandLine.IntTypeInfo(
        min=1,
        arity="?",
    ),
    output_stream=None,
)
def TestType(
    configuration,
    input_dir,
    output_dir,
    test_type,
    execute_in_parallel=None,
    iterations=1,
    debug_on_error=False,
    continue_iterations_on_error=False,
    code_coverage=False,
    debug_only=False,
    release_only=False,
    output_stream=sys.stdout,
    verbose=False,
    quiet=False,
    preserve_ansi_escape_sequences=False,
    no_status=False,
):
    """Run tests for the test type with the specified configuration"""

    return Test(
        configuration,
        input_dir,
        output_dir=output_dir,
        test_type=test_type,
        execute_in_parallel=execute_in_parallel,
        iterations=iterations,
        debug_on_error=debug_on_error,
        continue_iterations_on_error=continue_iterations_on_error,
        code_coverage=code_coverage,
        debug_only=debug_only,
        release_only=release_only,
        output_stream=output_stream,
        verbose=verbose,
        quiet=quiet,
        preserve_ansi_escape_sequences=preserve_ansi_escape_sequences,
        no_status=no_status,
    )

# ----------------------------------------------------------------------
@CommandLine.EntryPoint(
    input_dir=_input_dir_param_descripiton,
    output_dir=_output_dir_param_description,
    test_type=_test_type_param_description,
    execute_in_parallel=_execute_in_parallel_param_description,
    iterations=_iterations_param_description,
    debug_on_error=_debug_on_error_param_description,
    continue_iterations_on_error=_continue_iterations_on_error_param_description,
    code_coverage=_code_coverage_param_description,
    debug_only=_debug_only_param_description,
    release_only=_release_only_param_description,
    verbose=_verbose_param_description,
    quiet=_quiet_param_description,
    preserve_ansi_escape_sequences=_preserve_ansi_escape_sequences_param_description,
    no_status=_no_status_param_description,
)
@CommandLine.Constraints(
    input_dir=CommandLine.DirectoryTypeInfo(),
    output_dir=CommandLine.DirectoryTypeInfo(
        ensure_exists=False,
    ),
    test_type=CommandLine.StringTypeInfo(),
    execute_in_parallel=CommandLine.BoolTypeInfo(
        arity="?",
    ),
    iterations=CommandLine.IntTypeInfo(
        min=1,
        arity="?",
    ),
    output_stream=None,
)
def TestAll(
    input_dir,
    output_dir,
    test_type,
    execute_in_parallel=None,
    iterations=1,
    debug_on_error=False,
    continue_iterations_on_error=False,
    code_coverage=False,
    debug_only=False,
    release_only=False,
    output_stream=sys.stdout,
    verbose=False,
    quiet=False,
    preserve_ansi_escape_sequences=False,
    no_status=False,
):
    """Run tests for the test type with all configurations"""

    with StreamDecorator(output_stream).DoneManager(
        line_prefix="",
        prefix="\nResults: ",
        suffix="\n",
    ) as dm:
        for index, configuration in enumerate(six.iterkeys(CONFIGURATIONS)):
            header = "Testing '{}' ({} of {})...".format(
                configuration,
                index + 1,
                len(CONFIGURATIONS),
            )
            dm.stream.write(
                "{sep}\n{header}\n{sep}\n".format(
                    header=header,
                    sep="-" * len(header)
                )
            )
            with dm.stream.DoneManager(
                line_prefix="",
                prefix="\n{} Results: ".format(configuration),
                suffix="\n",
            ) as this_dm:
                this_dm.result = TestType(
                    configuration,
                    input_dir,
                    output_dir,
                    test_type,
                    execute_in_parallel=execute_in_parallel,
                    iterations=iterations,
                    debug_on_error=debug_on_error,
                    continue_iterations_on_error=continue_iterations_on_error,
                    code_coverage=code_coverage,
                    debug_only=debug_only,
                    release_only=release_only,
                    output_stream=this_dm.stream,
                    verbose=verbose,
                    quiet=quiet,
                    preserve_ansi_escape_sequences=preserve_ansi_escape_sequences,
                    no_status=no_status,
                )

        return dm.result

# ----------------------------------------------------------------------
@CommandLine.EntryPoint(
    input_dir=_input_dir_param_descripiton,
    test_type=_test_type_param_description,
    compiler=_compiler_param_description,
    compiler_flag=_compiler_flag_param_description,
    verbose=_verbose_param_description,
)
@CommandLine.Constraints(
    input_dir=CommandLine.DirectoryTypeInfo(),
    test_type=CommandLine.StringTypeInfo(),
    compiler=_compiler_type_info,
    compiler_flag=CommandLine.DictTypeInfo(
        require_exact_match=False,
        arity="?",
    ),
    output_stream=None,
)
def MatchTests(
    input_dir,
    test_type,
    compiler,
    compiler_flag=None,
    output_stream=sys.stdout,
    verbose=False,
):
    """Matches tests to production code for tests found within 'test_type' subdirectories."""

    compiler = _GetFromCommandLineArg(compiler, COMPILERS, compiler_flag)
    assert compiler

    if not isinstance(compiler.InputTypeInfo, FilenameTypeInfo):
        output_stream.write(
            "Tests can only be matched for compilers that operate on individual files.\n",
        )
        return 0

    output_stream = StreamDecorator(output_stream)

    traverse_exclude_dir_names = ["Generated", "Impl", "Details"]

    output_stream.write("Parsing '{}'...".format(input_dir))
    with output_stream.DoneManager(
        suffix="\n",
    ) as dm:
        source_files = list(
            FileSystem.WalkFiles(
                input_dir,
                include_dir_paths=[
                    lambda fullpath: os.path.isdir(os.path.join(fullpath, test_type)),
                ],
                include_full_paths=[compiler.IsSupported],
                exclude_file_names=["Build.py"],
                traverse_exclude_dir_names=traverse_exclude_dir_names,
            ),
        )

        test_items = ExtractTestItems(
            input_dir,
            test_type,
            compiler,
            dm.stream if verbose else None,
        )

        # Remove any test items that correspond to sources that were explicitly removed.
        # We want to run these tests, but don't want to report them as errors.

        # ----------------------------------------------------------------------
        def IsMissingTest(filename):
            parts = filename.split(os.path.sep)

            for part in parts:
                if part in traverse_exclude_dir_names:
                    return False

            return True

        # ----------------------------------------------------------------------

        test_items = [test_item for test_item in test_items if IsMissingTest(test_item)]

    output_stream.write(
        textwrap.dedent(
            """\
            Source Files:   {}
            Test Files:     {}

            """,
        ).format(len(source_files), len(test_items)),
    )

    output_template = "{source:<120} -> {test}\n"

    verbose_stream = StreamDecorator(output_stream if verbose else None)

    index = 0
    while index < len(source_files):
        source_filename = source_files[index]

        test_item = compiler.ItemToTestName(source_filename, test_type)

        if test_item is None or os.path.isfile(test_item):
            # We can't be sure that the test is in the file, as multiple source files may map
            # to the same test file (as in the case of headers with ".h" and ".hpp" extensions).
            if test_item in test_items:
                test_items.remove(test_item)

            del source_files[index]

            verbose_stream.write(
                output_template.format(
                    source=source_filename,
                    test=test_item,
                ),
            )
        else:
            index += 1

    verbose_stream.write("\n\n")

    if source_files:
        header = "{} without corresponding tests".format(
            inflect.no("source file", len(source_files)),
        )

        output_stream.write(
            textwrap.dedent(
                """\
                {header}
                {sep}
                {content}

                """,
            ).format(
                header=header,
                sep="-" * len(header),
                content="\n".join(source_files),
            )
        )

    if test_items:
        header = "{} without corresponding sources".format(
            inflect.no("test file", len(test_items)),
        )

        output_stream.write(
            textwrap.dedent(
                """\
                {header}
                {sep}
                {content}

                """,
            ).format(
                header=header,
                sep="-" * len(header),
                content="\n".join(test_items),
            )
        )

    return 0 if not source_files and not test_items else -1

# ----------------------------------------------------------------------
@CommandLine.EntryPoint(
    input_dir=_input_dir_param_descripiton,
    test_type=_test_type_param_description,
    verbose=_verbose_param_description,
)
@CommandLine.Constraints(
    input_dir=CommandLine.DirectoryTypeInfo(),
    test_type=CommandLine.StringTypeInfo(),
    output_stream=None,
)
def MatchAllTests(
    input_dir,
    test_type,
    output_stream=sys.stdout,
    verbose=False,
):
    """Matches tests for the test type with all configurations"""

    with StreamDecorator(output_stream).DoneManager(
        line_prefix="",
        prefix="\nResults: ",
        suffix="\n",
    ) as dm:
        for index, configuration in enumerate(six.iterkeys(CONFIGURATIONS)):
            header = "Matching '{}' ({} of {})...".format(
                configuration,
                index + 1,
                len(CONFIGURATIONS),
            )
            dm.stream.write(
                "{sep}\n{header}\n{sep}\n".format(
                    header=header,
                    sep="-" * len(header)
                )
            )
            with dm.stream.DoneManager(
                line_prefix="",
                prefix="\n{} Results: ".format(configuration),
                suffix="\n",
            ) as this_dm:
                this_dm.result = MatchTests(
                    input_dir,
                    test_type,
                    configuration.Compiler.Name,
                    output_stream=this_dm.stream,
                    verbose=verbose,
                )

        return dm.result

# ----------------------------------------------------------------------
@CommandLine.EntryPoint(
    input_dir=_input_dir_param_descripiton,
    test_type=_test_type_param_description,
    verbose=_verbose_param_description,
)
@CommandLine.Constraints(
    input_dir=CommandLine.DirectoryTypeInfo(),
    test_type=CommandLine.StringTypeInfo(),
    output_stream=None,
)
def MatchAllTests(
    input_dir,
    test_type,
    output_stream=sys.stdout,
    verbose=False,
):
    """Matches all tests for the test type across all compilers."""

    with StreamDecorator(output_stream).DoneManager(
        line_prefix="",
        prefix="\nResults: ",
        suffix="\n",
    ) as dm:
        for index, configuration in enumerate(six.itervalues(CONFIGURATIONS)):
            dm.stream.write(
                "Matching '{}' ({} of {})...".format(
                    configuration.Compiler.Name,
                    index + 1,
                    len(CONFIGURATIONS),
                ),
            )
            with dm.stream.DoneManager(
                line_prefix="    ",
            ) as this_dm:
                this_dm.result = MatchTests(
                    input_dir,
                    test_type,
                    configuration.Compiler.Name,
                    output_stream=this_dm.stream,
                    verbose=verbose,
                )

        return dm.result

# ----------------------------------------------------------------------
@CommandLine.EntryPoint(
    filename=CommandLine.EntryPoint.Parameter("Filename to execute."),
    compiler=_compiler_param_description,
    test_parser=_test_parser_param_description,
    test_executor=_test_executor_param_description,
    code_coverage_validator=_code_coverage_validator_param_description,
    execute_in_parallel=_execute_in_parallel_param_description,
    iterations=_iterations_param_description,
    debug_on_error=_debug_on_error_param_description,
    continue_iterations_on_error=_continue_iterations_on_error_param_description,
    compiler_flag=_compiler_flag_param_description,
    test_parser_flag=_test_parser_flag_param_description,
    test_executor_flag=_test_executor_flag_param_description,
    code_coverage_validator_flag=_code_coverage_validator_flag_param_description,
    debug_only=_debug_only_param_description,
    release_only=_release_only_param_description,
    verbose=_verbose_param_description,
    preserve_ansi_escape_sequences=_preserve_ansi_escape_sequences_param_description,
    no_status=_no_status_param_description,
)
@CommandLine.Constraints(
    filename=CommandLine.FilenameTypeInfo(),
    compiler=_compiler_type_info,
    test_parser=_test_parser_type_info,
    test_executor=_test_executor_type_info,
    code_coverage_validator=_code_coverage_validator_type_info,
    execute_in_parallel=CommandLine.BoolTypeInfo(
        arity="?",
    ),
    iterations=CommandLine.IntTypeInfo(
        min=1,
        arity="?",
    ),
    compiler_flag=CommandLine.DictTypeInfo(
        require_exact_match=False,
        arity="?",
    ),
    test_parser_flag=CommandLine.DictTypeInfo(
        require_exact_match=False,
        arity="?",
    ),
    test_executor_flag=CommandLine.DictTypeInfo(
        require_exact_match=False,
        arity="?",
    ),
    code_coverage_validator_flag=CommandLine.DictTypeInfo(
        require_exact_match=False,
        arity="?",
    ),
    output_stream=None,
)
def Execute(
    filename,
    compiler,
    test_parser,
    test_executor=None,
    code_coverage_validator=None,
    execute_in_parallel=None,
    iterations=1,
    debug_on_error=False,
    continue_iterations_on_error=False,
    compiler_flag=None,
    test_parser_flag=None,
    test_executor_flag=None,
    code_coverage_validator_flag=None,
    debug_only=False,
    release_only=False,
    output_stream=sys.stdout,
    verbose=False,
    preserve_ansi_escape_sequences=False,
    no_status=False,
):
    """
    Executes a specific test using a specific compiler, test parser, test executor, and code coverage validator. In most
    cases, it is easier to use a Test___ method rather than this one.
    """

    if test_executor_flag and test_executor is None:
        raise CommandLine.UsageException(
            "Test executor flags are only valid when a test executor is specified",
        )

    if code_coverage_validator_flag and code_coverage_validator is None:
        raise CommandLine.UsageException(
            "Code coverage validator flags are only valid when a code coverage validator is specified",
        )

    return _ExecuteImpl(
        filename,
        _GetFromCommandLineArg(compiler, COMPILERS, compiler_flag),
        _GetFromCommandLineArg(test_parser, TEST_PARSERS, test_parser_flag),
        _GetFromCommandLineArg(
            test_executor,
            TEST_EXECUTORS,
            test_executor_flag,
            allow_empty=True,
        ),
        _GetFromCommandLineArg(
            code_coverage_validator,
            CODE_COVERAGE_VALIDATORS,
            code_coverage_validator_flag,
            allow_empty=True,
        ),
        execute_in_parallel=execute_in_parallel,
        iterations=iterations,
        debug_on_error=debug_on_error,
        continue_iterations_on_error=continue_iterations_on_error,
        debug_only=debug_only,
        release_only=release_only,
        output_stream=output_stream,
        verbose=verbose,
        preserve_ansi_escape_sequences=preserve_ansi_escape_sequences,
        no_status=no_status,
    )

# ----------------------------------------------------------------------
@CommandLine.EntryPoint(
    input_dir=_input_dir_param_descripiton,
    output_dir=_output_dir_param_description,
    test_type=_test_type_param_description,
    compiler=_compiler_param_description,
    test_parser=_test_parser_param_description,
    test_executor=_test_executor_param_description,
    code_coverage_validator=_code_coverage_validator_param_description,
    execute_in_parallel=_execute_in_parallel_param_description,
    iterations=_iterations_param_description,
    debug_on_error=_debug_on_error_param_description,
    continue_iterations_on_error=_continue_iterations_on_error_param_description,
    compiler_flag=_compiler_flag_param_description,
    test_parser_flag=_test_parser_flag_param_description,
    test_executor_flag=_test_executor_flag_param_description,
    code_coverage_validator_flag=_code_coverage_validator_flag_param_description,
    debug_only=_debug_only_param_description,
    release_only=_release_only_param_description,
    verbose=_verbose_param_description,
    quiet=_quiet_param_description,
    preserve_ansi_escape_sequences=_preserve_ansi_escape_sequences_param_description,
    no_status=_no_status_param_description,
)
@CommandLine.Constraints(
    input_dir=CommandLine.DirectoryTypeInfo(),
    output_dir=CommandLine.DirectoryTypeInfo(
        ensure_exists=False,
    ),
    test_type=CommandLine.StringTypeInfo(),
    compiler=_compiler_type_info,
    test_parser=_test_parser_type_info,
    test_executor=_test_executor_type_info,
    code_coverage_validator=_code_coverage_validator_type_info,
    execute_in_parallel=CommandLine.BoolTypeInfo(
        arity="?",
    ),
    iterations=CommandLine.IntTypeInfo(
        min=1,
        arity="?",
    ),
    compiler_flag=CommandLine.DictTypeInfo(
        require_exact_match=False,
        arity="?",
    ),
    test_parser_flag=CommandLine.DictTypeInfo(
        require_exact_match=False,
        arity="?",
    ),
    test_executor_flag=CommandLine.DictTypeInfo(
        require_exact_match=False,
        arity="?",
    ),
    code_coverage_validator_flag=CommandLine.DictTypeInfo(
        require_exact_match=False,
        arity="?",
    ),
    output_stream=None,
)
def ExecuteTree(
    input_dir,
    output_dir,
    test_type,
    compiler,
    test_parser,
    test_executor=None,
    code_coverage_validator=None,
    execute_in_parallel=None,
    iterations=1,
    debug_on_error=False,
    continue_iterations_on_error=False,
    compiler_flag=None,
    test_parser_flag=None,
    test_executor_flag=None,
    code_coverage_validator_flag=None,
    debug_only=False,
    release_only=False,
    output_stream=sys.stdout,
    verbose=False,
    quiet=False,
    preserve_ansi_escape_sequences=False,
    no_status=False,
):
    """
    Executes tests found within 'test_type' subdirectories using a specific compiler, test parser, test executor, and code coverage validator. In most
    cases, it is easier to use a Test___ method rather than this one.
    """

    if test_executor_flag and test_executor is None:
        raise CommandLine.UsageException(
            "Test executor flags are only valid when a test executor is specified",
        )

    if code_coverage_validator_flag and code_coverage_validator is None:
        raise CommandLine.UsageException(
            "Code coverage validator flags are only valid when a code coverage validator is specified",
        )

    return _ExecuteTreeImpl(
        input_dir,
        output_dir,
        test_type,
        _GetFromCommandLineArg(compiler, COMPILERS, compiler_flag),
        _GetFromCommandLineArg(test_parser, TEST_PARSERS, test_parser_flag),
        _GetFromCommandLineArg(
            test_executor,
            TEST_EXECUTORS,
            test_executor_flag,
            allow_empty=True,
        ),
        _GetFromCommandLineArg(
            code_coverage_validator,
            CODE_COVERAGE_VALIDATORS,
            code_coverage_validator_flag,
            allow_empty=True,
        ),
        execute_in_parallel=execute_in_parallel,
        iterations=iterations,
        debug_on_error=debug_on_error,
        continue_iterations_on_error=continue_iterations_on_error,
        debug_only=debug_only,
        release_only=release_only,
        output_stream=output_stream,
        verbose=verbose,
        quiet=quiet,
        preserve_ansi_escape_sequences=preserve_ansi_escape_sequences,
        no_status=no_status,
    )

# ----------------------------------------------------------------------
def CommandLineSuffix():
    return StringHelpers.LeftJustify(
        textwrap.dedent(
            # <Wrong hanging indentation> pylint: disable = C0330
            """\
            Where...

                <configuration> can be one of these values:
                      (A configuration provides pre-configured values for <compiler>, <test_parser>, and <test_executor>)

            {configurations}

                Common values for <test_type> are (although these are not required):

            {test_types}

                <compiler> can be:

            {compilers}

                <test_parser> can be:

            {test_parsers}

                <test_executor> can be:

            {test_executors}

                <code_coverage_validator> can be:

            {code_coverage_validators}


            A valid name or index may be used for these command line arguments:

                - <compiler>
                - <test_parser>
                - <test_executor>
                - <code_coverage_validator>

            """,
        ).format(
            configurations="\n".join(
                ["      - {}".format(config) for config in six.iterkeys(CONFIGURATIONS)],
            ),
            test_types="\n".join(
                [
                    "      - {name:<30}  {desc}".format(
                        name=ttmd.Name,
                        desc=ttmd.Description,
                    ) for ttmd in TEST_TYPES
                ],
            ),
            compilers="\n".join(
                [
                    "      {0}) {1:<20} {2}".format(
                        index + 1,
                        compiler.Name,
                        compiler.Description,
                    )
                    for index,
                    compiler in enumerate(COMPILERS)
                ],
            ),
            test_parsers="\n".join(
                [
                    "      {0}) {1:<20} {2}".format(
                        index + 1,
                        compiler.Name,
                        compiler.Description,
                    )
                    for index,
                    compiler in enumerate(TEST_PARSERS)
                ],
            ),
            test_executors="\n".join(
                [
                    "      {0}) {1:<20} {2}".format(
                        index + 1,
                        compiler.Name,
                        compiler.Description,
                    )
                    for index,
                    compiler in enumerate(TEST_EXECUTORS)
                ],
            ),
            code_coverage_validators="\n".join(
                [
                    "      {0}) {1:<20} {2}".format(
                        index + 1,
                        compiler.Name,
                        compiler.Description,
                    )
                    for index,
                    compiler in enumerate(CODE_COVERAGE_VALIDATORS)
                ],
            ),
        ),
        4,
        skip_first_line=False,
    )


# ----------------------------------------------------------------------
# ----------------------------------------------------------------------
# ----------------------------------------------------------------------
def _GetFromCommandLineArg(
    arg,
    items,
    flags,
    allow_empty=False,
):
    if allow_empty and arg is None:
        return None

    assert arg

    try:
        arg = int(arg)
        assert arg < len(items), (arg, len(items))

        item = items[arg]
    except ValueError:
        item = next(item for item in items if item.Name == arg)

    assert item

    # Parser/Compilers/etc are created via default constructors, so we have a concrete
    # instance here. Create a new instance with the provided flags. This is pretty
    # unusual behavior.
    return type(item)(**flags)

# ----------------------------------------------------------------------
def _ExecuteImpl(
    filename_or_dir,
    compiler,
    test_parser,
    test_executor,
    code_coverage_validator,
    execute_in_parallel,
    iterations,
    debug_on_error,
    continue_iterations_on_error,
    debug_only,
    release_only,
    output_stream,
    verbose,
    preserve_ansi_escape_sequences,
    no_status,
):
    if not compiler.IsSupported(filename_or_dir):
        raise CommandLine.UsageException(
            "'{}' is not supported by '{}'".format(filename_or_dir, compiler.Name),
        )

    if (
        test_executor
        and test_executor.Name != "Standard"
        and code_coverage_validator is None
    ):
        code_coverage_validator = next(
            ccv for ccv in CODE_COVERAGE_VALIDATORS if ccv.Name == "Standard",
        )
        code_coverage_validator = code_coverage_validator

    with StreamDecorator.GenerateAnsiSequenceStream(
        output_stream,
        preserve_ansi_escape_sequences=preserve_ansi_escape_sequences,
    ) as output_stream:
        output_stream.write("\n")

        temp_directory = os.getenv(_TEMP_DIR_OVERRIDE_ENVIRONMENT_NAME)
        if not temp_directory:
            temp_directory = CurrentShell.CreateTempDirectory()

        # Append a suffix to the dir
        ctr = 1
        while True:
            potential_directory = os.path.join(temp_directory, "{0:05}".format(ctr))
            if not os.path.isdir(potential_directory):
                temp_directory = potential_directory
                break

            ctr += 1

        complete_results = GenerateTestResults(
            [filename_or_dir],
            temp_directory,
            compiler,
            test_parser,
            test_executor,
            code_coverage_validator,
            execute_in_parallel=execute_in_parallel,
            iterations=iterations,
            debug_on_error=debug_on_error,
            continue_iterations_on_error=continue_iterations_on_error,
            debug_only=debug_only,
            release_only=release_only,
            output_stream=output_stream,
            verbose=verbose,
            no_status=no_status,
        )

        if not complete_results:
            return 0

        assert len(complete_results) == 1, len(complete_results)
        complete_result = complete_results[0]

        output_stream.write("\n")
        output_stream.write(
            complete_result.ToString(
                compiler,
                test_parser,
                test_executor,
                code_coverage_validator,
            ),
        )

        result = complete_result.ResultCode() or 0

        if verbose or result != 0:
            for configuration_results in [complete_result.debug, complete_result.release]:
                if (
                    verbose or configuration_results.compile_result != 0
                ) and configuration_results.compile_log is not None:
                    output_stream.write(
                        textwrap.dedent(
                            """\
                            {header}
                            {filename}
                            {header}
                            {content}

                            """,
                        ).format(
                            filename=configuration_results.compile_log,
                            header=len(configuration_results.compile_log) * "=",
                            content=open(
                                configuration_results.compile_log,
                            ).read().strip(),
                        )
                    )

                for er in configuration_results.execute_results:
                    if (verbose or er.TestResult != 0) and er.TestOutput is not None:
                        output_stream.write(
                            textwrap.dedent(
                                """\
                                {header}
                                {filename}
                                {header}
                                {content}

                                """,
                            ).format(
                                filename=er.TestOutput,
                                header=len(er.TestOutput) * "=",
                                content=open(er.TestOutput).read().strip(),
                            )
                        )

        return result

# ----------------------------------------------------------------------
def _ExecuteTreeImpl(
    input_dir,
    output_dir,
    test_type,
    compiler,
    test_parser,
    test_executor,
    code_coverage_validator,
    execute_in_parallel,
    iterations,
    debug_on_error,
    continue_iterations_on_error,
    debug_only,
    release_only,
    output_stream,
    verbose,
    quiet,
    preserve_ansi_escape_sequences,
    no_status,
):
    if verbose and quiet:
        raise CommandLine.UsageException(
            "'verbose' and 'quiet' are mutually exclusive options and cannot be specified together",
        )

    if (
        test_executor
        and test_executor.Name != "Standard"
        and code_coverage_validator is None
    ):
        code_coverage_validator = next(
            ccv for ccv in CODE_COVERAGE_VALIDATORS if ccv.Name == "Standard",
        )

    with StreamDecorator.GenerateAnsiSequenceStream(
        output_stream,
        preserve_ansi_escape_sequences=preserve_ansi_escape_sequences,
    ) as output_stream:
        output_stream.write("\n")

        with StreamDecorator(output_stream).DoneManager(
            line_prefix="",
            prefix="\nResults: ",
            suffix="\n",
        ) as dm:
            test_items = []

            dm.stream.write("Parsing '{}'...".format(input_dir))
            with dm.stream.DoneManager(
                done_suffix=lambda: "{} found".format(
                    inflect.no("test", len(test_items)),
                ),
                suffix="\n",
            ) as this_dm:
                test_items = ExtractTestItems(
                    input_dir,
                    test_type,
                    compiler,
                    verbose_stream=StreamDecorator(this_dm.stream if verbose else None),
                )

            if not test_items:
                return dm.result

            if execute_in_parallel is None:
                for tt in TEST_TYPES:
                    if tt.Name == test_type:
                        execute_in_parallel = tt.ExecuteInParallel
                        break

                if execute_in_parallel is None:
                    execute_in_parallel = False

            complete_results = GenerateTestResults(
                test_items,
                output_dir,
                compiler,
                test_parser,
                test_executor,
                code_coverage_validator,
                execute_in_parallel=execute_in_parallel,
                iterations=iterations,
                debug_on_error=debug_on_error,
                continue_iterations_on_error=continue_iterations_on_error,
                debug_only=debug_only,
                release_only=release_only,
                output_stream=dm.stream,
                verbose=verbose,
                no_status=no_status,
            )
            if not complete_results:
                return 0

            dm.stream.write("\n")

            if not quiet:
                for complete_result in complete_results:
                    dm.stream.write(
                        complete_result.ToString(
                            compiler,
                            test_parser,
                            test_executor,
                            code_coverage_validator,
                        ),
                    )

            # Print summary
            nonlocals = Nonlocals(
                tests=0,
                failures=0,
            )

            # ----------------------------------------------------------------------
            def Output(test_item, result_type, results):
                result_code = results.ResultCode()
                if result_code is None:
                    return

                nonlocals.tests += 1

                if result_code == 0:
                    dm.stream.write(
                        "{}{}Succeeded:{}".format(
                            colorama.Fore.GREEN,
                            colorama.Style.BRIGHT,
                            colorama.Style.RESET_ALL,
                        ),
                    )
                else:
                    dm.stream.write(
                        "{}{}Failed:   {}".format(
                            colorama.Fore.RED,
                            colorama.Style.BRIGHT,
                            colorama.Style.RESET_ALL,
                        ),
                    )
                    nonlocals.failures += 1

                dm.stream.write(
                    " {}, {}, {}\n".format(test_item, result_type, results.TotalTime()),
                )

            # ----------------------------------------------------------------------

            for complete_result in complete_results:
                Output(complete_result.Item, "Debug", complete_result.debug)
                Output(complete_result.Item, "Release", complete_result.release)

            dm.stream.write(
                "\n{percentage:.02f}% - {total} built and run with {failures}.\n".format(
                    percentage=0.0 if not nonlocals.tests else (
                        (float(nonlocals.tests) - nonlocals.failures) / nonlocals.tests
                    ) * 100,
                    total=inflect.no("test", nonlocals.tests),
                    failures=inflect.no("failure", nonlocals.failures),
                )
            )

            if nonlocals.failures:
                dm.result = -1

            return dm.result

# ----------------------------------------------------------------------
# ----------------------------------------------------------------------
# ----------------------------------------------------------------------
if __name__ == "__main__":
    try:
        sys.exit(CommandLine.Main())
    except KeyboardInterrupt:
        pass
