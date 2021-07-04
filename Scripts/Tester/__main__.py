# ----------------------------------------------------------------------
# |
# |  Tester.py
# |
# |  David Brownell <db@DavidBrownell.com>
# |      2018-05-21 21:44:34
# |
# ----------------------------------------------------------------------
# |
# |  Copyright David Brownell 2018-21.
# |  Distributed under the Boost Software License, Version 1.0.
# |  (See accompanying file LICENSE_1_0.txt or copy at http://www.boost.org/LICENSE_1_0.txt)
# |
# ----------------------------------------------------------------------
"""General purpose test executor."""

import datetime
import json
import os
import re
import sys
import textwrap

from collections import OrderedDict

import colorama
import six

import CommonEnvironment
from CommonEnvironment import Nonlocals
from CommonEnvironment.CallOnExit import CallOnExit
from CommonEnvironment import CommandLine
from CommonEnvironment import FileSystem
from CommonEnvironment.Shell.All import CurrentShell
from CommonEnvironment import StringHelpers
from CommonEnvironment.StreamDecorator import StreamDecorator
from CommonEnvironment.TestTypeMetadata import TEST_TYPES

from CommonEnvironment.TypeInfo.FundamentalTypes.DateTimeTypeInfo import DateTimeTypeInfo
from CommonEnvironment.TypeInfo.FundamentalTypes.DirectoryTypeInfo import DirectoryTypeInfo
from CommonEnvironment.TypeInfo.FundamentalTypes.DurationTypeInfo import DurationTypeInfo
from CommonEnvironment.TypeInfo.FundamentalTypes.FilenameTypeInfo import FilenameTypeInfo

from CommonEnvironment.TypeInfo.FundamentalTypes.Serialization.StringSerialization import StringSerialization

# ----------------------------------------------------------------------
_script_fullpath                            = CommonEnvironment.ThisFullpath()
_script_dir, _script_name                   = os.path.split(_script_fullpath)
# ----------------------------------------------------------------------

assert os.getenv("DEVELOPMENT_ENVIRONMENT_FUNDAMENTAL")
sys.path.insert(0, os.getenv("DEVELOPMENT_ENVIRONMENT_FUNDAMENTAL"))
with CallOnExit(lambda: sys.path.pop(0)):
    from RepositoryBootstrap.SetupAndActivate import DynamicPluginArchitecture as DPA

from RunTests import CreateRunTestsFunc, inflect

# ----------------------------------------------------------------------
# <Too many lines in module> pylint: disable = C0302

_TEMP_DIR_OVERRIDE_ENVIRONMENT_NAME         = "DEVELOPMENT_ENVIRONMENT_TESTER_TEMP_DIRECTORY"

StreamDecorator.InitAnsiSequenceStreams()

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
                 Name       )(?P<name>.+?)(?#
                            )\s*-\s*(?#
                 Type       )(?P<type>(?:compiler|test_parser|coverage_executor|coverage_validator))(?#
                            )\s*-\s*(?#
                 Value      )(?P<value>[^"]+)(?#
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
# |  Public Methods
# |
# ----------------------------------------------------------------------
def ExtractTestItems(
    input_dir,
    test_subdir,
    compiler,
    verbose_stream=None,
    optional_test_parser=None,
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

            if not compiler.IsSupported(fullpath) or not compiler.IsSupportedTestItem(fullpath):
                verbose_stream.write(
                    "'{}' is not supported by the compiler.\n".format(fullpath),
                )
                continue

            if optional_test_parser and not optional_test_parser.IsSupportedTestItem(fullpath):
                verbose_stream.write(
                    "'{}' is not supported by the test parser.\n".format(fullpath),
                )
                continue

            test_items.append(fullpath)

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
_execute_tests_in_parallel_param_description            = CommandLine.EntryPoint.Parameter(
    "Execute tests in parallel.",
)
_single_threaded_param_description                      = CommandLine.EntryPoint.Parameter(
    "Execute all build and test functionality in a single thread.",
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
_build_only_param_description                           = CommandLine.EntryPoint.Parameter(
    "Build, but do not run tests; this can be helpful when ensuring that all tests can build with older toolsets.",
)
_verbose_param_description                              = CommandLine.EntryPoint.Parameter("Verbose output.")
_quiet_param_description                                = CommandLine.EntryPoint.Parameter("Quiet output.")
_preserve_ansi_escape_sequences_param_description       = CommandLine.EntryPoint.Parameter(
    "Preserve ansi escape sequences when generating output (useful when invoking this functionality from another script).",
)
_no_status_param_description                            = CommandLine.EntryPoint.Parameter(
    "Do not display progress bar status when building and executing.",
)
_junit_xml_output_filename_param_description            = CommandLine.EntryPoint.Parameter(
    "Filename for JUnit XML output; JUnit output will only be generated if this filename is provided on the command line.",
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
    filename_or_directory=CommandLine.EntryPoint.Parameter("Filename or directory to test."),
    output_dir=_output_dir_param_description,
    test_type=_test_type_param_description,
    execute_tests_in_parallel=_execute_tests_in_parallel_param_description,
    single_threaded=_single_threaded_param_description,
    iterations=_iterations_param_description,
    debug_on_error=_debug_on_error_param_description,
    continue_iterations_on_error=_continue_iterations_on_error_param_description,
    code_coverage=_code_coverage_param_description,
    debug_only=_debug_only_param_description,
    release_only=_release_only_param_description,
    build_only=_build_only_param_description,
    verbose=_verbose_param_description,
    quiet=_quiet_param_description,
    preserve_ansi_escape_sequences=_preserve_ansi_escape_sequences_param_description,
    no_status=_no_status_param_description,
    junit_xml_output_filename=_junit_xml_output_filename_param_description,
    code_coverage_validator=_code_coverage_validator_param_description,
    code_coverage_validator_flag=_code_coverage_validator_flag_param_description,
)
@CommandLine.Constraints(
    configuration=_configuration_type_info,
    filename_or_directory=CommandLine.FilenameTypeInfo(
        match_any=True,
    ),
    output_dir=CommandLine.DirectoryTypeInfo(
        ensure_exists=False,
        arity="?",
    ),
    test_type=CommandLine.StringTypeInfo(
        arity="?",
    ),
    execute_tests_in_parallel=CommandLine.BoolTypeInfo(
        arity="?",
    ),
    iterations=CommandLine.IntTypeInfo(
        min=1,
        arity="?",
    ),
    code_coverage_validator=_code_coverage_validator_type_info,
    code_coverage_validator_flag=CommandLine.DictTypeInfo(
        require_exact_match=False,
        arity="*",
    ),
    junit_xml_output_filename=CommandLine.StringTypeInfo(
        arity="?",
    ),
    output_stream=None,
)
def Test(
    configuration,
    filename_or_directory,
    output_dir=None,
    test_type=None,
    execute_tests_in_parallel=None,
    single_threaded=False,
    iterations=1,
    debug_on_error=False,
    continue_iterations_on_error=False,
    code_coverage=False,
    debug_only=False,
    release_only=False,
    build_only=False,
    output_stream=sys.stdout,
    verbose=False,
    quiet=False,
    preserve_ansi_escape_sequences=False,
    no_status=False,
    code_coverage_validator=None,
    code_coverage_validator_flag=None,
    junit_xml_output_filename=None,
):
    """Tests the given input"""

    code_coverage_validator_flags = code_coverage_validator_flag
    del code_coverage_validator_flag

    configuration = CONFIGURATIONS[configuration]

    if code_coverage or code_coverage_validator or code_coverage_validator_flags:
        code_coverage_executor = configuration.OptionalCoverageExecutor

        code_coverage_validator = configuration.OptionalCodeCoverageValidator
        if code_coverage_validator is None:
            for index, ccv in enumerate(CODE_COVERAGE_VALIDATORS):
                if ccv.Name == "Standard":
                    code_coverage_validator = index
                    break

        code_coverage_validator = _GetFromCommandLineArg(
            code_coverage_validator,
            CODE_COVERAGE_VALIDATORS,
            code_coverage_validator_flags,
            allow_empty=True,
        )

    else:
        code_coverage_executor = None

    if os.path.isfile(filename_or_directory) or (
        os.path.isdir(filename_or_directory)
        and configuration.Compiler.IsSupported(filename_or_directory)
    ):
        if quiet:
            if os.path.isfile(filename_or_directory):
                raise CommandLine.UsageException(
                    "'quiet' is only used when executing tests via a directory",
                )
            quiet = False

        if junit_xml_output_filename:
            raise CommandLine.UsageException(
                "'junit_xml_output_filename' is only used when executing tests via a directory",
            )

        return _ExecuteImpl(
            filename_or_directory,
            configuration.Compiler,
            configuration.TestParser,
            code_coverage_executor,
            code_coverage_validator,
            execute_tests_in_parallel=execute_tests_in_parallel,
            iterations=iterations,
            debug_on_error=debug_on_error,
            continue_iterations_on_error=continue_iterations_on_error,
            debug_only=debug_only,
            release_only=release_only,
            build_only=build_only,
            output_stream=output_stream,
            verbose=verbose,
            preserve_ansi_escape_sequences=preserve_ansi_escape_sequences,
            no_status=no_status,
            max_num_concurrent_tasks=1 if single_threaded else None,
        )

    if test_type is None:
        raise CommandLine.UsageException(
            "The 'test_type' command line argument must be provided when 'filename_or_directory' is a directory.",
        )

    if output_dir is None:
        raise CommandLine.UsageException(
            "The 'output_dir' command line argument must be provided when 'filename_or_directory' is a directory.",
        )

    return _ExecuteTreeImpl(
        filename_or_directory,
        output_dir,
        test_type,
        configuration.Compiler,
        configuration.TestParser,
        code_coverage_executor,
        code_coverage_validator,
        execute_tests_in_parallel=execute_tests_in_parallel,
        iterations=iterations,
        debug_on_error=debug_on_error,
        continue_iterations_on_error=continue_iterations_on_error,
        debug_only=debug_only,
        release_only=release_only,
        build_only=build_only,
        output_stream=output_stream,
        verbose=verbose,
        quiet=quiet,
        preserve_ansi_escape_sequences=preserve_ansi_escape_sequences,
        no_status=no_status,
        max_num_concurrent_tasks=1 if single_threaded else None,
        junit_xml_output_filename=junit_xml_output_filename,
    )


# ----------------------------------------------------------------------
@CommandLine.EntryPoint(
    filename_or_directory=CommandLine.EntryPoint.Parameter(
        "Filename or directory to test.",
    ),
    single_threaded=_single_threaded_param_description,
    iterations=_iterations_param_description,
    debug_on_error=_debug_on_error_param_description,
    continue_iterations_on_error=_continue_iterations_on_error_param_description,
    code_coverage=_code_coverage_param_description,
    debug_only=_debug_only_param_description,
    release_only=_release_only_param_description,
    build_only=_build_only_param_description,
    verbose=_verbose_param_description,
    preserve_ansi_escape_sequences=_preserve_ansi_escape_sequences_param_description,
    no_status=_no_status_param_description,
    code_coverage_validator=_code_coverage_validator_param_description,
    code_coverage_validator_flag=_code_coverage_validator_flag_param_description,
)
@CommandLine.Constraints(
    filename_or_directory=CommandLine.FilenameTypeInfo(
        match_any=True,
    ),
    iterations=CommandLine.IntTypeInfo(
        min=1,
        arity="?",
    ),
    code_coverage_validator=_code_coverage_validator_type_info,
    code_coverage_validator_flag=CommandLine.DictTypeInfo(
        require_exact_match=False,
        arity="*",
    ),
    output_stream=None,
)
def TestItem(
    filename_or_directory,
    single_threaded=False,
    iterations=1,
    debug_on_error=False,
    continue_iterations_on_error=False,
    code_coverage=False,
    debug_only=False,
    release_only=False,
    build_only=False,
    output_stream=sys.stdout,
    verbose=False,
    preserve_ansi_escape_sequences=False,
    no_status=False,
    code_coverage_validator=None,
    code_coverage_validator_flag=None,
):
    """Tests the given input file or directory (depending on the compiler invoked)"""

    # ----------------------------------------------------------------------
    def GetConfiguration():
        for key, configuration in six.iteritems(CONFIGURATIONS):
            if (
                configuration.Compiler.IsSupported(filename_or_directory)
                and configuration.Compiler.IsSupportedTestItem(filename_or_directory)
                and configuration.TestParser.IsSupportedTestItem(filename_or_directory)
            ):
                return key

        return None

    # ----------------------------------------------------------------------

    configuration = GetConfiguration()
    if not configuration:
        raise CommandLine.UsageException(
            "Unable to find a configuration with a compiler and test parser that supports the input '{}'".format(
                filename_or_directory,
            ),
        )

    return Test(
        configuration,
        filename_or_directory,
        output_dir=None,
        test_type=None,
        execute_tests_in_parallel=False,
        single_threaded=single_threaded,
        iterations=iterations,
        debug_on_error=debug_on_error,
        continue_iterations_on_error=continue_iterations_on_error,
        code_coverage=code_coverage,
        debug_only=debug_only,
        release_only=release_only,
        build_only=build_only,
        output_stream=output_stream,
        verbose=verbose,
        quiet=False,
        preserve_ansi_escape_sequences=preserve_ansi_escape_sequences,
        no_status=no_status,
        code_coverage_validator=code_coverage_validator,
        code_coverage_validator_flag=code_coverage_validator_flag,
    )


# ----------------------------------------------------------------------
@CommandLine.EntryPoint(
    configuration=_configuration_param_description,
    input_dir=_input_dir_param_descripiton,
    output_dir=_output_dir_param_description,
    test_type=_test_type_param_description,
    execute_tests_in_parallel=_execute_tests_in_parallel_param_description,
    single_threaded=_single_threaded_param_description,
    iterations=_iterations_param_description,
    debug_on_error=_debug_on_error_param_description,
    continue_iterations_on_error=_continue_iterations_on_error_param_description,
    code_coverage=_code_coverage_param_description,
    debug_only=_debug_only_param_description,
    release_only=_release_only_param_description,
    build_only=_build_only_param_description,
    verbose=_verbose_param_description,
    quiet=_quiet_param_description,
    preserve_ansi_escape_sequences=_preserve_ansi_escape_sequences_param_description,
    no_status=_no_status_param_description,
    junit_xml_output_filename=_junit_xml_output_filename_param_description,
    code_coverage_validator=_code_coverage_validator_param_description,
    code_coverage_validator_flag=_code_coverage_validator_flag_param_description,
)
@CommandLine.Constraints(
    configuration=_configuration_type_info,
    input_dir=CommandLine.DirectoryTypeInfo(),
    output_dir=CommandLine.DirectoryTypeInfo(
        ensure_exists=False,
    ),
    test_type=CommandLine.StringTypeInfo(),
    execute_tests_in_parallel=CommandLine.BoolTypeInfo(
        arity="?",
    ),
    iterations=CommandLine.IntTypeInfo(
        min=1,
        arity="?",
    ),
    code_coverage_validator=_code_coverage_validator_type_info,
    code_coverage_validator_flag=CommandLine.DictTypeInfo(
        require_exact_match=False,
        arity="*",
    ),
    junit_xml_output_filename=CommandLine.StringTypeInfo(
        arity="?",
    ),
    output_stream=None,
)
def TestType(
    configuration,
    input_dir,
    output_dir,
    test_type,
    execute_tests_in_parallel=None,
    single_threaded=False,
    iterations=1,
    debug_on_error=False,
    continue_iterations_on_error=False,
    code_coverage=False,
    debug_only=False,
    release_only=False,
    build_only=False,
    output_stream=sys.stdout,
    verbose=False,
    quiet=False,
    preserve_ansi_escape_sequences=False,
    no_status=False,
    code_coverage_validator=None,
    code_coverage_validator_flag=None,
    junit_xml_output_filename=None,
):
    """Run tests for the test type with the specified configuration"""

    return Test(
        configuration,
        input_dir,
        output_dir=output_dir,
        test_type=test_type,
        execute_tests_in_parallel=execute_tests_in_parallel,
        single_threaded=single_threaded,
        iterations=iterations,
        debug_on_error=debug_on_error,
        continue_iterations_on_error=continue_iterations_on_error,
        code_coverage=code_coverage,
        debug_only=debug_only,
        release_only=release_only,
        build_only=build_only,
        output_stream=output_stream,
        verbose=verbose,
        quiet=quiet,
        preserve_ansi_escape_sequences=preserve_ansi_escape_sequences,
        no_status=no_status,
        code_coverage_validator=code_coverage_validator,
        code_coverage_validator_flag=code_coverage_validator_flag,
        junit_xml_output_filename=junit_xml_output_filename,
    )


# ----------------------------------------------------------------------
@CommandLine.EntryPoint(
    input_dir=_input_dir_param_descripiton,
    output_dir=_output_dir_param_description,
    test_type=_test_type_param_description,
    execute_tests_in_parallel=_execute_tests_in_parallel_param_description,
    single_threaded=_single_threaded_param_description,
    iterations=_iterations_param_description,
    debug_on_error=_debug_on_error_param_description,
    continue_iterations_on_error=_continue_iterations_on_error_param_description,
    code_coverage=_code_coverage_param_description,
    debug_only=_debug_only_param_description,
    release_only=_release_only_param_description,
    build_only=_build_only_param_description,
    verbose=_verbose_param_description,
    quiet=_quiet_param_description,
    preserve_ansi_escape_sequences=_preserve_ansi_escape_sequences_param_description,
    no_status=_no_status_param_description,
    junit_xml_output_filename=_junit_xml_output_filename_param_description,
    code_coverage_validator=_code_coverage_validator_param_description,
    code_coverage_validator_flag=_code_coverage_validator_flag_param_description,
)
@CommandLine.Constraints(
    input_dir=CommandLine.DirectoryTypeInfo(),
    output_dir=CommandLine.DirectoryTypeInfo(
        ensure_exists=False,
    ),
    test_type=CommandLine.StringTypeInfo(),
    execute_tests_in_parallel=CommandLine.BoolTypeInfo(
        arity="?",
    ),
    iterations=CommandLine.IntTypeInfo(
        min=1,
        arity="?",
    ),
    code_coverage_validator=_code_coverage_validator_type_info,
    code_coverage_validator_flag=CommandLine.DictTypeInfo(
        require_exact_match=False,
        arity="*",
    ),
    junit_xml_output_filename=CommandLine.StringTypeInfo(
        arity="?",
    ),
    output_stream=None,
)
def TestAll(
    input_dir,
    output_dir,
    test_type,
    execute_tests_in_parallel=None,
    single_threaded=False,
    iterations=1,
    debug_on_error=False,
    continue_iterations_on_error=False,
    code_coverage=False,
    debug_only=False,
    release_only=False,
    build_only=False,
    output_stream=sys.stdout,
    verbose=False,
    quiet=False,
    preserve_ansi_escape_sequences=False,
    no_status=False,
    code_coverage_validator=None,
    code_coverage_validator_flag=None,
    junit_xml_output_filename=None,
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
                    execute_tests_in_parallel=execute_tests_in_parallel,
                    single_threaded=single_threaded,
                    iterations=iterations,
                    debug_on_error=debug_on_error,
                    continue_iterations_on_error=continue_iterations_on_error,
                    code_coverage=code_coverage,
                    debug_only=debug_only,
                    release_only=release_only,
                    build_only=build_only,
                    output_stream=this_dm.stream,
                    verbose=verbose,
                    quiet=quiet,
                    preserve_ansi_escape_sequences=preserve_ansi_escape_sequences,
                    no_status=no_status,
                    code_coverage_validator=code_coverage_validator,
                    code_coverage_validator_flag=code_coverage_validator_flag,
                    junit_xml_output_filename=junit_xml_output_filename,
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
        arity="*",
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
    execute_tests_in_parallel=_execute_tests_in_parallel_param_description,
    single_threaded=_single_threaded_param_description,
    iterations=_iterations_param_description,
    debug_on_error=_debug_on_error_param_description,
    continue_iterations_on_error=_continue_iterations_on_error_param_description,
    compiler_flag=_compiler_flag_param_description,
    test_parser_flag=_test_parser_flag_param_description,
    test_executor_flag=_test_executor_flag_param_description,
    code_coverage_validator_flag=_code_coverage_validator_flag_param_description,
    debug_only=_debug_only_param_description,
    release_only=_release_only_param_description,
    build_only=_build_only_param_description,
    verbose=_verbose_param_description,
    preserve_ansi_escape_sequences=_preserve_ansi_escape_sequences_param_description,
    no_status=_no_status_param_description,
    junit_xml_output_filename=_junit_xml_output_filename_param_description,
)
@CommandLine.Constraints(
    filename=CommandLine.FilenameTypeInfo(),
    compiler=_compiler_type_info,
    test_parser=_test_parser_type_info,
    test_executor=_test_executor_type_info,
    code_coverage_validator=_code_coverage_validator_type_info,
    execute_tests_in_parallel=CommandLine.BoolTypeInfo(
        arity="?",
    ),
    iterations=CommandLine.IntTypeInfo(
        min=1,
        arity="?",
    ),
    compiler_flag=CommandLine.DictTypeInfo(
        require_exact_match=False,
        arity="*",
    ),
    test_parser_flag=CommandLine.DictTypeInfo(
        require_exact_match=False,
        arity="*",
    ),
    test_executor_flag=CommandLine.DictTypeInfo(
        require_exact_match=False,
        arity="*",
    ),
    code_coverage_validator_flag=CommandLine.DictTypeInfo(
        require_exact_match=False,
        arity="*",
    ),
    junit_xml_output_filename=CommandLine.StringTypeInfo(
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
    execute_tests_in_parallel=None,
    single_threaded=False,
    iterations=1,
    debug_on_error=False,
    continue_iterations_on_error=False,
    compiler_flag=None,
    test_parser_flag=None,
    test_executor_flag=None,
    code_coverage_validator_flag=None,
    debug_only=False,
    release_only=False,
    build_only=False,
    output_stream=sys.stdout,
    verbose=False,
    preserve_ansi_escape_sequences=False,
    no_status=False,
    junit_xml_output_filename=None,
):
    """
    Executes a specific test using a specific compiler, test parser, test executor, and code coverage validator. In most
    cases, it is easier to use a Test___ method rather than this one (as those methods will auto-detect these settings).
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
        execute_tests_in_parallel=execute_tests_in_parallel,
        iterations=iterations,
        debug_on_error=debug_on_error,
        continue_iterations_on_error=continue_iterations_on_error,
        debug_only=debug_only,
        release_only=release_only,
        build_only=build_only,
        output_stream=output_stream,
        verbose=verbose,
        preserve_ansi_escape_sequences=preserve_ansi_escape_sequences,
        no_status=no_status,
        max_num_concurrent_tasks=1 if single_threaded else None,
        junit_xml_output_filename=junit_xml_output_filename,
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
    execute_tests_in_parallel=_execute_tests_in_parallel_param_description,
    single_threaded=_single_threaded_param_description,
    iterations=_iterations_param_description,
    debug_on_error=_debug_on_error_param_description,
    continue_iterations_on_error=_continue_iterations_on_error_param_description,
    compiler_flag=_compiler_flag_param_description,
    test_parser_flag=_test_parser_flag_param_description,
    test_executor_flag=_test_executor_flag_param_description,
    code_coverage_validator_flag=_code_coverage_validator_flag_param_description,
    debug_only=_debug_only_param_description,
    release_only=_release_only_param_description,
    build_only=_build_only_param_description,
    verbose=_verbose_param_description,
    quiet=_quiet_param_description,
    preserve_ansi_escape_sequences=_preserve_ansi_escape_sequences_param_description,
    no_status=_no_status_param_description,
    junit_xml_output_filename=_junit_xml_output_filename_param_description,
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
    execute_tests_in_parallel=CommandLine.BoolTypeInfo(
        arity="?",
    ),
    iterations=CommandLine.IntTypeInfo(
        min=1,
        arity="?",
    ),
    compiler_flag=CommandLine.DictTypeInfo(
        require_exact_match=False,
        arity="*",
    ),
    test_parser_flag=CommandLine.DictTypeInfo(
        require_exact_match=False,
        arity="*",
    ),
    test_executor_flag=CommandLine.DictTypeInfo(
        require_exact_match=False,
        arity="*",
    ),
    code_coverage_validator_flag=CommandLine.DictTypeInfo(
        require_exact_match=False,
        arity="*",
    ),
    junit_xml_output_filename=CommandLine.StringTypeInfo(
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
    execute_tests_in_parallel=None,
    single_threaded=False,
    iterations=1,
    debug_on_error=False,
    continue_iterations_on_error=False,
    compiler_flag=None,
    test_parser_flag=None,
    test_executor_flag=None,
    code_coverage_validator_flag=None,
    debug_only=False,
    release_only=False,
    build_only=False,
    output_stream=sys.stdout,
    verbose=False,
    quiet=False,
    preserve_ansi_escape_sequences=False,
    no_status=False,
    junit_xml_output_filename=None,
):
    """
    Executes tests found within 'test_type' subdirectories using a specific compiler, test parser, test executor, and code coverage validator. In most
    cases, it is easier to use a Test___ method rather than this one (as those methods will auto-detect these settings).
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
        execute_tests_in_parallel=execute_tests_in_parallel,
        iterations=iterations,
        debug_on_error=debug_on_error,
        continue_iterations_on_error=continue_iterations_on_error,
        debug_only=debug_only,
        release_only=release_only,
        build_only=build_only,
        output_stream=output_stream,
        verbose=verbose,
        quiet=quiet,
        preserve_ansi_escape_sequences=preserve_ansi_escape_sequences,
        no_status=no_status,
        max_num_concurrent_tasks=1 if single_threaded else None,
        junit_xml_output_filename=junit_xml_output_filename,
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

                Common values for <test_type> are (note that a value is not required to be in this list):

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

    assert arg is not None

    try:
        arg = int(arg)
        assert arg < len(items), (arg, len(items))

        item = items[arg]
    except ValueError:
        item = next(item for item in items if item.Name == arg)

    assert item

    # The flags are read as strings from the command line, however the classes
    # may be expecting different types. Try to make a best guess for each type.

    # ----------------------------------------------------------------------
    def ConvertString(value):
        if not isinstance(value, six.string_types):
            return value

        value_lower = value.lower()

        # Bool
        if value_lower in [
            "true",
            "false",
            "yes",
            "no",
        ]:
            return value_lower in ["true", "yes"]

        # Float
        if "." in value:
            try:
                return float(value)
            except ValueError:
                pass

        # Integer
        try:
            return int(value)
        except ValueError:
            pass

        # Keep the current value
        return value

    # ----------------------------------------------------------------------

    for k, v in six.iteritems(flags):
        flags[k] = ConvertString(v)

    # Parser/Compilers/etc are created via default constructors, so we have a concrete
    # instance here. Create a new instance with the provided flags. This is pretty
    # unusual behavior.
    return type(item)(**flags)


# ----------------------------------------------------------------------
def _ExecuteImpl(
    filename_or_directory,
    compiler,
    test_parser,
    test_executor,
    code_coverage_validator,
    execute_tests_in_parallel,
    iterations,
    debug_on_error,
    continue_iterations_on_error,
    debug_only,
    release_only,
    build_only,
    output_stream,
    verbose,
    preserve_ansi_escape_sequences,
    no_status,
    max_num_concurrent_tasks=None,
):
    if not compiler.IsSupported(filename_or_directory):
        raise CommandLine.UsageException(
            "'{}' is not supported by '{}'".format(filename_or_directory, compiler.Name),
        )

    if (
        test_executor
        and test_executor.Name != "Standard"
        and code_coverage_validator is None
    ):
        code_coverage_validator = next(
            ccv for ccv in CODE_COVERAGE_VALIDATORS if ccv.Name == "Standard"
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

        run_tests_func = CreateRunTestsFunc(
            next(
                executor
                for executor in TEST_EXECUTORS
                if executor.Name == "Standard"
            ),
        )

        complete_results = run_tests_func(
            [filename_or_directory],
            temp_directory,
            compiler,
            test_parser,
            test_executor,
            code_coverage_validator,
            execute_tests_in_parallel=execute_tests_in_parallel,
            iterations=iterations,
            debug_on_error=debug_on_error,
            continue_iterations_on_error=continue_iterations_on_error,
            debug_only=debug_only,
            release_only=release_only,
            build_only=build_only,
            output_stream=output_stream,
            verbose=verbose,
            no_status=no_status,
            max_num_concurrent_tasks=max_num_concurrent_tasks,
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
                include_benchmarks=True,
                include_subresults=True,
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
                    if er is None:
                        continue

                    if (
                        verbose or er.CoverageResult != 0
                    ) and er.CoverageOutput is not None:
                        output_stream.write(
                            textwrap.dedent(
                                """\
                                {header}
                                {filename}
                                {header}
                                {content}

                                """,
                            ).format(
                                filename=er.CoverageOutput,
                                header=len(er.CoverageOutput) * "=",
                                content=open(er.CoverageOutput).read().strip(),
                            )
                        )

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
    execute_tests_in_parallel,
    iterations,
    debug_on_error,
    continue_iterations_on_error,
    debug_only,
    release_only,
    build_only,
    output_stream,
    verbose,
    quiet,
    preserve_ansi_escape_sequences,
    no_status,
    max_num_concurrent_tasks=None,
    junit_xml_output_filename=None,
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
            ccv for ccv in CODE_COVERAGE_VALIDATORS if ccv.Name == "Standard"
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
                    inflect.no("supported '{}' test".format(test_type), len(test_items)),
                ),
                suffix="\n",
            ) as this_dm:
                test_items = ExtractTestItems(
                    input_dir,
                    test_type,
                    compiler,
                    verbose_stream=StreamDecorator(this_dm.stream if verbose else None),
                    optional_test_parser=test_parser,
                )

            if not test_items:
                return dm.result

            if execute_tests_in_parallel is None:
                for tt in TEST_TYPES:
                    if tt.Name == test_type:
                        execute_tests_in_parallel = tt.ExecuteInParallel
                        break

                if execute_tests_in_parallel is None:
                    execute_tests_in_parallel = False

            run_tests_func = CreateRunTestsFunc(
                next(
                    executor
                    for executor in TEST_EXECUTORS
                    if executor.Name == "Standard"
                ),
            )

            complete_results = run_tests_func(
                test_items,
                output_dir,
                compiler,
                test_parser,
                test_executor,
                code_coverage_validator,
                execute_tests_in_parallel=execute_tests_in_parallel,
                iterations=iterations,
                debug_on_error=debug_on_error,
                continue_iterations_on_error=continue_iterations_on_error,
                debug_only=debug_only,
                release_only=release_only,
                build_only=build_only,
                output_stream=dm.stream,
                verbose=verbose,
                no_status=no_status,
                max_num_concurrent_tasks=max_num_concurrent_tasks,
            )
            if not complete_results:
                return 0

            dm.stream.write("\n")

            # Persist the benchmarks
            benchmark_filename = os.path.join(output_dir, "benchmarks.json")

            dm.stream.write("Creating '{}'...".format(benchmark_filename))
            with dm.stream.DoneManager():
                _CreateBenchmarks(input_dir, benchmark_filename, complete_results)

            # Persist JUnit output (if requested)
            if junit_xml_output_filename:
                junit_xml_output_filename = os.path.join(output_dir, junit_xml_output_filename)

                dm.stream.write("Creating '{}'...".format(junit_xml_output_filename))
                with dm.stream.DoneManager():
                    _CreateJUnit(input_dir, junit_xml_output_filename, complete_results)

            dm.stream.write("\n")

            # Display the results
            if not quiet:
                for complete_result in complete_results:
                    dm.stream.write(
                        complete_result.ToString(
                            compiler,
                            test_parser,
                            test_executor,
                            code_coverage_validator,
                            include_benchmarks=False,
                            include_subresults=True,
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
                    " {}, {}, {}".format(test_item, result_type, results.TotalTime()),
                )

                if (
                    results.execute_results
                    and results.execute_results[0].CoveragePercentage is not None
                ):
                    dm.stream.write(", {0:0.2f}%".format(results.execute_results[0].CoveragePercentage))

                dm.stream.write("\n")

            # ----------------------------------------------------------------------

            for complete_result in complete_results:
                Output(complete_result.Item, "Debug", complete_result.debug)
                Output(complete_result.Item, "Release", complete_result.release)

            dm.stream.write(
                "\n{percentage:.02f}% - {total} built{run} with {failures}.\n".format(
                    percentage=0.0 if not nonlocals.tests else (
                        (float(nonlocals.tests) - nonlocals.failures) / nonlocals.tests
                    ) * 100,
                    total=inflect.no("test", nonlocals.tests),
                    failures=inflect.no("failure", nonlocals.failures),
                    run="" if build_only else " and run",
                )
            )

            if nonlocals.failures:
                dm.result = -1

            return dm.result


# ----------------------------------------------------------------------
# ----------------------------------------------------------------------
# ----------------------------------------------------------------------
def _CreateBenchmarks(input_dir, filename, complete_results):
    benchmarks = OrderedDict()

    for complete_result in complete_results:
        these_benchmarks = OrderedDict()

        for configuration in ["debug", "release"]:
            configuration_benchmarks = OrderedDict()

            for test_parse_result in getattr(
                complete_result,
                configuration,
            ).test_parse_results:
                if test_parse_result is None:
                    continue

                if test_parse_result.Benchmarks:
                    for k, v in six.iteritems(test_parse_result.Benchmarks):
                        if k not in configuration_benchmarks:
                            configuration_benchmarks[k] = []

                        configuration_benchmarks[k] += v

            if configuration_benchmarks:
                these_benchmarks[configuration] = configuration_benchmarks

        if these_benchmarks:
            key = FileSystem.TrimPath(complete_result.Item, input_dir)

            benchmarks[key] = these_benchmarks

    with open(filename, "w") as f:
        # ----------------------------------------------------------------------
        class JsonEncoder(json.JSONEncoder):
            def default(self, o):
                return getattr(o, "__dict__", o)

        # ----------------------------------------------------------------------

        json.dump(
            benchmarks,
            f,
            cls=JsonEncoder,
        )


# ----------------------------------------------------------------------
def _CreateJUnit(input_dir, filename, complete_results):
    # TODO: Eventually, we should serialize this content based on XML code generated
    #       via JUnit.SimpleSchema and the PythonXmlPlugin. However, that code has problems
    #       with collections and is not ready for prime time. Therefore, we are creating the
    #       XML manually here.
    #
    #       Update this code once the issues in PythonXmlPlugin have been addressed.

    import socket
    from xml.etree import ElementTree as ET

    dti = DurationTypeInfo()

    root = ET.Element("testsuites")

    hostname = socket.gethostname()
    timestamp = StringSerialization.SerializeItem(DateTimeTypeInfo(), datetime.datetime.now())

    for index, complete_result in enumerate(complete_results):
        suite = ET.Element("testsuite")

        suite.set("id", str(index))
        suite.set("name", FileSystem.TrimPath(complete_result.Item, input_dir).replace(os.path.sep, "/"))
        suite.set("hostname", hostname)
        suite.set("timestamp", timestamp)

        suite.set(
            "time",
            StringSerialization.SerializeItem(
                dti,
                complete_result.TotalTime(
                    as_string=False,
                ),
                regex_index=2,
            ),
        )

        num_tests, num_failures, num_skipped = complete_result.ResultInfo()

        suite.set("tests", str(num_tests))
        suite.set("failures", str(num_failures))
        suite.set("skipped", str(num_skipped))

        for configuration, results in [
            ("Debug", complete_result.debug),
            ("Release", complete_result.release),
        ]:
            if results is None or results.compile_result is None:
                continue

            testcase = ET.Element("testcase")

            testcase.set("name", configuration)

            testcase.set(
                "time",
                StringSerialization.SerializeItem(
                    dti,
                    results.TotalTime(
                        as_string=False,
                    ),
                    regex_index=2,
                ),
            )

            for result in results.test_parse_results:
                if result.SubResults:
                    for subresult_name, (subresult_result, subresult_time) in six.iteritems(result.SubResults):
                        if subresult_result == 0:
                            continue

                        failure = ET.Element("failure")

                        failure.text = "{} ({}, {})".format(subresult_name, subresult_result, subresult_time)

                        failure.set("message", failure.text)
                        failure.set("type", "SubResult failure")

                        testcase.append(failure)

            suite.append(testcase)

        root.append(suite)

    FileSystem.MakeDirs(os.path.dirname(filename))

    with open(filename, "w") as f:
        f.write(
            ET.tostring(
                root,
                encoding="unicode",
            ),
        )


# ----------------------------------------------------------------------
# ----------------------------------------------------------------------
# ----------------------------------------------------------------------
if __name__ == "__main__":
    try:
        sys.exit(CommandLine.Main())
    except KeyboardInterrupt:
        pass
