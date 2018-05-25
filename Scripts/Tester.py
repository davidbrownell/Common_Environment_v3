# ----------------------------------------------------------------------
# |  
# |  Tester.py
# |  
# |  David Brownell <db@DavidBrownell.com>
# |      2018-05-21 21:44:34
# |  
# ----------------------------------------------------------------------
# |  
# |  Copyright David Brownell 2018.
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
import tempfile
import textwrap
import threading
import time
import traceback

from collections import OrderedDict, namedtuple

import colorama
import six
import inflect as inflect_mod

from CommonEnvironment import Nonlocals, ObjectStrImpl
from CommonEnvironment.CallOnExit import CallOnExit
from CommonEnvironment.CodeCoverageExtractorImpl import CodeCoverageExtractorImpl
from CommonEnvironment import CommandLine
from CommonEnvironment import FileSystem
from CommonEnvironment import Process
from CommonEnvironment.Shell.All import CurrentShell
from CommonEnvironment import StringHelpers
from CommonEnvironment.StreamDecorator import StreamDecorator
from CommonEnvironment import TaskPool

from CommonEnvironment.TypeInfo.FundamentalTypes.DirectoryTypeInfo import DirectoryTypeInfo
from CommonEnvironment.TypeInfo.FundamentalTypes.DurationTypeInfo import DurationTypeInfo
from CommonEnvironment.TypeInfo.FundamentalTypes.FilenameTypeInfo import FilenameTypeInfo
from CommonEnvironment.TypeInfo.FundamentalTypes.Serialization.StringSerialization import StringSerialization

# ----------------------------------------------------------------------
_script_fullpath = os.path.abspath(__file__) if "python" in sys.executable.lower() else sys.executable
_script_dir, _script_name = os.path.split(_script_fullpath)
# ----------------------------------------------------------------------

assert os.getenv("DEVELOPMENT_ENVIRONMENT_FUNDAMENTAL")
sys.path.insert(0, os.getenv("DEVELOPMENT_ENVIRONMENT_FUNDAMENTAL"))
with CallOnExit(lambda: sys.path.pop(0)):
    from RepositoryBootstrap.Impl import DynamicPluginArchitecture as DPA

# ----------------------------------------------------------------------
StreamDecorator.InitAnsiSequenceStreams()
inflect                                     = inflect_mod.engine()

# ----------------------------------------------------------------------
# ----------------------------------------------------------------------
# ----------------------------------------------------------------------
TEST_IGNORE_FILENAME_TEMPLATE               = "{}-ignore"

# ----------------------------------------------------------------------
def _LoadCompilerFromModule(mod):
    for potential_name in [ "Compiler", "CodeGenerator", "Verifier", ]:
        result = getattr(mod, potential_name, None)
        if result is not None:
            return result

    assert False, mod

# ----------------------------------------------------------------------

COMPILERS                                   = [ _LoadCompilerFromModule(mod) for mod in DPA.EnumeratePlugins("DEVELOPMENT_ENVIRONMENT_COMPILERS") ]
TEST_PARSERS                                = [ mod.TestParser for mod in DPA.EnumeratePlugins("DEVELOPMENT_ENVIRONMENT_TEST_PARSERS") ]
CODE_COVERAGE_EXTRACTORS                    = [ mod.CodeCoverageExtractor for mod in DPA.EnumeratePlugins("DEVELOPMENT_ENVIRONMENT_CODE_COVERAGE_EXTRACTORS") ]
CODE_COVERAGE_VALIDATORS                    = [ mod.CodeCoverageValidator for mod in DPA.EnumeratePlugins("DEVELOPMENT_ENVIRONMENT_CODE_COVERAGE_VALIDATORS") ]

CONFIGURATIONS                              = OrderedDict()

# Extract configuration-specific information from other repositories. This ensures that this file,
# which is in the fundamental repo, doesn't take a dependency on repos that depend on this one.
#
# Expected format is a list of items delimited by the os-specific delimiter stored in an
# environment variable. Each item is in the form:
#
#       "<configuration name>-<compiler|test_parser|code_coverage>-<value>"

custom_configurations = os.getenv("DEVELOPMENT_ENVIRONMENT_TESTER_CONFIGURATIONS")
if custom_configurations:
    # ----------------------------------------------------------------------
    class Configuration(object):
        # ----------------------------------------------------------------------
        @classmethod
        def Create( cls,
                    configuration_name,
                    compiler_name,
                    test_parser_name,
                    optional_code_coverage_extractor_name,
                  ):
            compiler = next((compiler for compiler in COMPILERS if compiler.Name == compiler_name), None)
            if compiler is None:
                raise Exception("The compiler '{}' used in the configuration '{}' does not exist".format(compiler_name, configuration_name))

            test_parser = next((test_parser for test_parser in TEST_PARSERS if test_parser.Name == test_parser_name), None)
            if test_parser is None:
                raise Exception("The test parser '{}' used in the configuration '{}' does not exist".format(test_parser_name, configuration_name))

            if optional_code_coverage_extractor_name is not None:
                optional_code_coverage_extractor = next((code_coverage_extractor for code_coverage_extractor in CODE_COVERAGE_EXTRACTORS if code_coverage_extractor.Name == optional_code_coverage_extractor_name), None)
                if optional_code_coverage_extractor is None:
                    raise Exception("The code coverage extractor '{}' used in the configuration '{}' does not exist".format(optional_code_coverage_extractor_name, configuration_name))
            else:
                optional_code_coverage_extractor = None

            return cls(compiler, test_parser, optional_code_coverage_extractor)

        # ----------------------------------------------------------------------
        def __init__(self, compiler, test_parser, optional_code_coverage_extractor):
            assert compiler
            assert test_parser

            self.Compiler                               = compiler
            self.TestParser                             = test_parser
            self.OptionalCodeCoverageExtractor          = optional_code_coverage_extractor

    # ----------------------------------------------------------------------
                      
    regex = re.compile(textwrap.dedent(
       r"""(?#
                    )\s*"?(?#
        Name        )(?P<name>.+?)(?#
                    )\s*-\s*(?#
        Type        )(?P<type>(?:compiler|test_parser|code_coverage_extractor))(?#
                    )\s*-\s*(?#
        Value       )(?P<value>[^"]+)(?#
                    )"?\s*(?#
        )"""))

    configuration_map = OrderedDict()

    for configuration in [ item for item in custom_configurations.split(CurrentShell.EnvironmentVariableDelimiter) if item.strip() ]:
        match = regex.match(configuration)
        assert match, configuration

        configuration_name = match.group("name").lower()
        type_ = match.group("type")
        value = match.group("value")

        if configuration_name not in configuration_map:
            configuration_map[configuration_name] = {}

        if type_ in configuration_map[configuration_name]:
            if not isinstance(configuration_map[configuration_name][type_], list):
                configuration_map[configuration_name][type_] = [ configuration_map[configuration_name][type_], ]

            configuration_map[configuration_name][type_].append(value)
        else:
            configuration_map[configuration_name][type_] = value

    for key, item_map in six.iteritems(configuration_map):
        # compiler and test parser are required
        if "compiler" not in item_map or "test_parser" not in item_map:
            continue

        if isinstance(item_map["compiler"], list):
            compiler_info = [ ( "{}-{}".format(key, compiler),
                                compiler,
                              ) for compiler in item_map["compiler"]
                            ]
        elif isinstance(item_map["compiler"], six.string_types):
            compiler_info = [ ( key, item_map["compiler"] ),
                            ]
        else:
            assert False, type(item_map["compiler"])

        for key, compiler in compiler_info:
            CONFIGURATIONS[key] = Configuration.Create( key,
                                                        compiler, 
                                                        item_map["test_parser"],
                                                        item_map.get("code_coverage_extractor", "Noop"),
                                                      )

_UNIVERSAL_BASIC_FLAGS                      = []
_UNIVERSAL_CODE_COVERAGE_FLAGS              = [ "/code_coverage_validator=Standard", ]

TEST_TYPES = [] # BugBug

# ----------------------------------------------------------------------
# |  
# |  Public Types
# |  
# ----------------------------------------------------------------------
class Results(object):
    """Results for executing a single test"""

    # ----------------------------------------------------------------------
    # |  Public Types
    TestParseResult                         = namedtuple( "TestParseResult",
                                                          [ "Result",
                                                            "Time",
                                                          ],
                                                        )

    CoverageValidationResult                = namedtuple( "CoverageValidationResult",
                                                          [ "Result",
                                                            "Time",
                                                            "Min",
                                                          ],
                                                        )

    # ----------------------------------------------------------------------
    def __init__(self):
        self.compiler_context               = None

        self.compile_binary                 = None
        self.compile_result                 = None
        self.compile_log                    = None
        self.compile_time                   = None

        self.has_errors                     = False
        
        self.execute_results                = []        # CodeCoverageExtracotrImpl.ExecuteResult
        self.test_parse_results             = []        # TestParseResult
        self.coverage_validation_results    = []        # CoverageValidationResult
                
    # ----------------------------------------------------------------------
    def __str__(self):
        return ObjectStrImpl(self)

    # ----------------------------------------------------------------------
    def ResultCode(self):
        if self.compile_result is None or self.compile_result < 0:
            return self.compile_result

        nonlocals = Nonlocals(result=self.compile_result)
        
        # ----------------------------------------------------------------------
        def ApplyResult(result):
            if result is not None:
                if result < 0:
                    nonlocals.result = result
                    return False

                if nonlocals.result in [ None, 0, ]:
                    nonlocals.result = result

            return True

        # ----------------------------------------------------------------------

        for execute_result, test_parse_result, coverage_validation_result in zip ( self.execute_results,
                                                                                   self.test_parse_results,
                                                                                   self.coverage_validation_results,
                                                                                 ):
            if execute_result is not None:
                should_continue = True

                for item_result in [ execute_result.TestResult,
                                     execute_result.CoverageResult,
                                   ]:
                    if not ApplyResult(item_result):
                        should_continue = False
                        break

                if not should_continue:
                    break

            if test_parse_result is not None and not ApplyResult(test_parse_result.Result):
                break

            if coverage_validation_result is not None and not ApplyResult(coverage_validation_result.Result):
                break

        return nonlocals.result

    # ----------------------------------------------------------------------
    def ToString( self,
                  optional_compiler,
                  optional_test_parser,
                  optional_code_coverage_extractor,
                  optional_code_coverage_validator,
                ):
        # ----------------------------------------------------------------------
        def ResultToString(result):
            if result is None:     
                result = "{}N/A".format(colorama.Style.DIM)
            elif result == 0:                 
                result = "{}{}Succeeded".format(colorama.Fore.GREEN, colorama.Style.BRIGHT)
            elif result < 0:                  
                result = "{}{}Failed ({})".format(colorama.Fore.RED, colorama.Style.BRIGHT, result)
            elif result > 0:                  
                result = "{}{}Unknown ({})".format(colorama.Fore.YELLOW, colorama.Style.BRIGHT, result)
            else:
                assert False, result

            return "{}{}".format(result, colorama.Style.RESET_ALL)

        # ----------------------------------------------------------------------

        results = [ "{color_push}{compiler}{test_parser}{extractor}{validator}{color_pop}\n\n" \
                        .format( color_push="{}{}".format(colorama.Fore.WHITE, colorama.Style.BRIGHT),
                                 color_pop=colorama.Style.RESET_ALL,
                                 compiler=      "Compiler:                                       {}\n".format(optional_compiler.Name) if optional_compiler else '',
                                 test_parser=   "Test Parser:                                    {}\n".format(optional_test_parser.Name) if optional_test_parser else '',
                                 extractor=     "Code Coverage Extractor:                        {}\n".format(optional_code_coverage_extractor.Name) if optional_code_coverage_extractor else '',
                                 validator=     "Code Coverage Validator:                        {}\n".format(optional_code_coverage_validator.Name) if optional_code_coverage_validator else '',
                               ),
                  ]

        result_code = self.ResultCode()
        if result_code is None:
            return "Result:                                         {}\n".format(ResultToString(result_code))

        

        results.append(textwrap.dedent(
            """\
            Result:                                         {result_code}

            Compile Result:                                 {compile_result}
            Compile Binary:                                 {compile_binary}
            Compile Log Filename:                           {compile_log}
            Compile Time:                                   {compile_time}

            """).format( result_code=ResultToString(result_code),
                         compile_result=ResultToString(self.compile_result),
                         compile_binary=self.compile_binary or "N/A",
                         compile_log=self.compile_log or "N/A",
                         compile_time=self.compile_time or "N/A",
                       ))

        for index, (execute_result, test_parse_result, coverage_validation_result) in enumerate(zip( self.execute_results,
                                                                                                     self.test_parse_results,
                                                                                                     self.coverage_validation_results,
                                                                                                    )):
            if not execute_result and not test_parse_result and not coverage_validation_result:
                continue

            header = "Iteration #{}".format(index + 1)
            results.append("{}\n{}\n".format(header, '-' * len(header)))

            if execute_result:
                results.append(StringHelpers.LeftJustify( textwrap.dedent(
                                                            """\
                                                                Test Execution Result:                      {test_result}
                                                                Test Execution Log Filename:                {test_log}
                                                                Test Execution Time:                        {test_time}

                                                            """).format( test_result=ResultToString(execute_result.TestResult),
                                                                         test_log=execute_result.TestOutput,
                                                                         test_time=execute_result.TestTime,
                                                                       ),
                                                          4,
                                                          skip_first_line=False,
                                                        ))

            if test_parse_result:
                results.append(StringHelpers.LeftJustify( textwrap.dedent(
                                                            """\
                                                            Test Parse Result:                          {test_parse_result}
                                                            Test Parse Time:                            {test_parse_time}

                                                            """).format( test_parse_result=ResultToString(test_parse_result.Result),
                                                                         test_parse_time=test_parse_result.Time,
                                                                       ),
                                                          4,
                                                          skip_first_line=False,
                                                        ))

            if execute_result and execute_result.CoverageResult is not None:
                results.append(StringHelpers.LeftJustify( textwrap.dedent(
                                                            """\
                                                            Code Coverage Result:                       {result}
                                                            Code Coverage Log Filename:                 {log}
                                                            Code Coverage Execution Time:               {time}
                                                            Code Coverage Data Filename:                {data}
                                                            Code Coverage Percentage:                   {percentage}
                                                            Code Coverage Percentages:                  {percentages}

                                                            """).format( result=ResultToString(execute_result.CoverageResult),
                                                                         log=execute_result.CoverageOutput or "N/A",
                                                                         time=execute_result.CoverageTime or "N/A",
                                                                         data=execute_result.CoverageDataFilename or "N/A",
                                                                         percentage="{0:0.2f}%".format(execute_result.CoveragePercentage) if execute_result.CoveragePercentage is not None else "N/A",
                                                                         percentages="N/A" if execute_result.CoveragePercentages is None else "\n{}".format('\n'.join([ "        - [{value:<7}] {name}".format(value="{0:0.2f}%".format(percentage), name=name) for name, percentage in six.iteritems(execute_result.CoveragePercentages) ])),
                                                                       ),
                                                          4,
                                                          skip_first_line=False,
                                                        ))

            if coverage_validation_result:
                results.append(StringHelpers.LeftJustify( textwrap.dedent(
                                                            """\
                                                            Code Coverage Validation Result:            {result}
                                                            Code Coverage Validation Time:              {time}
                                                            Code Coverage Minimum Percentage:           {min}

                                                            """).format( result=ResultToString(coverage_validation_result.Result),
                                                                         time=coverage_validation_result.Time,
                                                                         min="N/A" if coverage_validation_result.Min is None else "{}%".format(coverage_validation_result.Min),
                                                                       ),
                                                          4,
                                                          skip_first_line=False,
                                                        ))
        return ''.join(results)

    # ----------------------------------------------------------------------
    def TotalTime(self):
        dti = DurationTypeInfo()

        total_time = datetime.timedelta(seconds=0)

        get_duration = lambda duration: StringSerialization.DeserializeItem(dti, duration) if duration is not None else datetime.timedelta(seconds=0)

        total_time += get_duration(self.compile_time)
        # BugBug total_time += get_duration(self.test_time)
        # BugBug total_time += get_duration(self.test_parse_time)
        # BugBug total_time += get_duration(self.coverage_time)

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
    def __str__(self):
        return ObjectStrImpl(self)

    # ----------------------------------------------------------------------
    def ResultCode(self):
        result = None

        for results in [ self.debug,
                         self.release,
                       ]:
            this_result = results.ResultCode()
            if this_result is None:
                continue

            if this_result < 0:
                result = this_result
                break
            elif result in [ None, 0, ]:
                result = this_result

        return result

    # ----------------------------------------------------------------------
    def ToString( self,
                  optional_compiler,
                  optional_test_parser,
                  optional_code_coverage_extractor,
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

            """).format( color_push="{}{}".format(colorama.Fore.WHITE, colorama.Style.BRIGHT),
                         color_pop=colorama.Style.RESET_ALL,
                         header='=' * header_length,
                         item=self.Item,
                         item_length=header_length - 2,
                         debug="N/A" if not self.debug else StringHelpers.LeftJustify( self.debug.ToString( optional_compiler,
                                                                                                            optional_test_parser,
                                                                                                            optional_code_coverage_extractor,
                                                                                                            optional_code_coverage_validator,
                                                                                                          ), 
                                                                                       4,
                                                                                       skip_first_line=False,
                                                                                     ).rstrip(),
                         release="N/A" if not self.release else StringHelpers.LeftJustify( self.release.ToString( optional_compiler,
                                                                                                                  optional_test_parser,
                                                                                                                  optional_code_coverage_extractor,
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
def ExtractTestItems( input_dir,
                      test_subdir,
                      compiler,
                      verbose_stream=None,
                    ):
    assert os.path.isdir(input_dir), input_dir
    assert test_subdir
    assert compiler

    verbose_stream = StreamDecorator( verbose_stream, 
                                      prefix='\n', 
                                      line_prefix='  ',
                                    )

    traverse_exclude_dir_names = [ "Generated", ]
    
    test_items = []

    if isinstance(compiler.InputTypeInfo, FilenameTypeInfo):
        for fullpath in FileSystem.WalkFiles( input_dir,
                                              include_dir_names=[ test_subdir, ],
                                              traverse_exclude_dir_names=traverse_exclude_dir_names,
                                            ):
            if os.path.exists(TEST_IGNORE_FILENAME_TEMPLATE.format(fullpath)):
                continue

            if compiler.IsSupported(_script_fullpath) and compiler.IsSupportedTestFile(_script_fullpath):
                test_items.append(fullpath)
            else:
                verbose_stream.write("'{}' is not supported by the compiler.\n".format(fullpath))

    elif isinstance(compiler.InputTypeInfo, DirectoryTypeInfo):
        search_string = ".{}.".format(test_subdir)

        for root, filenames in FileSystem.WalkDirs( input_dir,
                                                    include_dir_names=[ lambda d: search_string in d ],
                                                    traverse_exclude_dir_names=traverse_exclude_dir_names,
                                                  ):
            if os.path.exists(TEST_IGNORE_FILENAME_TEMPLATE.format(root)):
                continue

            if compiler.IsSupported(root):
                test_items.append(root)
            else:
                verbose_stream.write("'{}' is not supported by the compiler.\n".format(_script_fullpath))

    else:
        assert False, (compiler.Name, compiler.InputTypeInfo)

    return test_items

# ----------------------------------------------------------------------
def GenerateTestResults( test_items,
                         output_dir,
                         compiler,
                         test_parser,
                         optional_code_coverage_extractor,
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
                         print_command_line,
                         max_num_concurrent_tasks=multiprocessing.cpu_count(),
                       ):
    assert test_items
    assert output_dir
    assert compiler
    assert test_parser
    assert iterations > 0, iterations
    assert output_stream
    assert max_num_concurrent_tasks > 1, max_num_concurrent_task

    execute_in_parallel = True # BugBug
    continue_iterations_on_error = True # BugBug

    # Check for congruent plugins
    result = compiler.ValidateEnvironment()
    if result:
        output_stream.write("ERROR: The current environment is not supported by the compiler '{}': {}.\n".format(compiler.Name, result))
        return None

    if not test_parser.IsSupportedCompiler(compiler):
        raise Exception("The test parser '{}' does not support the compiler '{}'.".format(test_parser.Name, compiler.Name))

    if optional_code_coverage_extractor:
        result = optional_code_coverage_extractor.ValidateEnvironment()
        if result:
            output_stream.write("ERROR: The current environment is not supported by the code coverage extractor '{}': {}.\n".format(optional_code_coverage_extractor.Name, result))
            return None

        if not optional_code_coverage_extractor.IsSupportedCompiler(compiler):
            raise Exception("The code coverage extractor '{}' does not support the compiler '{}'.".format(optional_code_coverage_extractor.Name, compiler.Name))

    if optional_code_coverage_validator and not optional_code_coverage_extractor:
        raise Exception("A code coverage validator cannot be used without a code coverage extractor")

    FileSystem.MakeDirs(output_dir)

    # Ensure that we only build the debug configuration with code coverage
    if optional_code_coverage_extractor:
        execute_in_parallel = False

        if compiler.IsCompiler:
            debug_only = True
            release_only = False

    # ----------------------------------------------------------------------
    # |  Prepare the working data
    WorkingData                             = namedtuple( "ResultsWorkingData",
                                                          [ "complete_result",
                                                            "output_dir",
                                                            "execution_lock",
                                                          ],
                                                        )

    working_data_items = []

    if len(test_items) == 1:
        common_prefix = FileSystem.GetCommonPath(test_items[0], os.path.abspath(os.getcwd()))
    else:
        common_prefix = FileSystem.GetCommonPath(*test_items)

    for test_item in test_items:
        if not compiler.IsSupported(test_item):
            continue

        # The base name used for all output for this particular test is based on the name of
        # the test itself.
        output_name = FileSystem.TrimPath(test_item, common_prefix)

        for bad_char in [ '\\', '/', ':', '*', '?', '"', '<', '>', '|', ]:
            output_name = output_name.replace(bad_char, '_')

        working_data_items.append(WorkingData( CompleteResult(test_item), 
                                               os.path.join(output_dir, output_name),
                                               threading.Lock(),
                                             ))

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

            results.compiler_context = compiler.GetContextItem( working_data.complete_result.Item,
                                                                is_debug=configuration == "Debug",
                                                                is_profile=bool(optional_code_coverage_extractor),
                                                                output_filename=results.compile_binary,
                                                                force=True,
                                                              )
            # Context may be None if it has been disabled for this specific environment
            if results.compiler_context is None:
                results.compile_binary = None

        # ----------------------------------------------------------------------

        if not release_only or not compiler.IsCompiler:
            PopulateResults(working_data.complete_result.debug, "Debug")

        if not debug_only and compiler.IsCompiler:
            PopulateResults(working_data.complete_result.release, "Release")

    # Execute the build in parallel
    nonlocals = Nonlocals(build_failures=0)
    build_failures_lock = threading.Lock()

    # ----------------------------------------------------------------------
    def BuildThreadProc(task_index, output_stream, on_status_update):
        working_data = working_data_items[task_index % len(working_data_items)]
    
        if task_index >= len(working_data_items):
            configuration_results = working_data.complete_result.release
        else:
            configuration_results = working_data.complete_result.debug

        if configuration_results.compiler_context is None:
            return

        if not no_status:
            on_status_update("Waiting")

        with working_data.execution_lock:
            if not no_status:
                on_status_update("Building")

            compile_result = None
            compile_output = ''
            start_time = time.time()
            
            try:
                sink = six.moves.StringIO()

                if compiler.IsCompiler:
                    compile_result = compiler.Compile(configuration_results.compiler_context, sink, verbose=verbose)
                    compiler.RemoveTemporaryArtifacts(configuration_results.compiler_context)
                elif compiler.IsCodeGenerator:
                    compile_result = compiler.Generate(configuration_results.compiler_context, sink, verbose=verbose)
                elif compiler.IsVerifier:
                    compile_result = compiler.Verify(configuration_results.compiler_context, sink, verbose=verbose)
                else:
                    assert False, compiler.Name

                compile_output = sink.getvalue()

                if compile_result != 0:
                    output_stream.write(compile_output)

            except:
                compile_result = -1
                compile_output = traceback.format_exc()

                raise

            finally:
                configuration_results.compile_result = compile_result
                configuration_results.compile_time = str(datetime.timedelta(seconds=(time.time() - start_time)))

                with open(configuration_results.compile_log, 'w') as f:
                    f.write(compile_output.replace('\r\n', '\n'))

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
        debug_tasks.append(TaskPool.Task("{} [Debug]".format(working_data.complete_result.Item), BuildThreadProc))
        release_tasks.append(TaskPool.Task("{} [Release]".format(working_data.complete_result.Item), BuildThreadProc))

    with output_stream.SingleLineDoneManager( "Building...",
                                              done_suffix=lambda: inflect.no("build failure", nonlocals.build_failures),
                                            ) as this_dm:
        result = TaskPool.Execute( debug_tasks + release_tasks,
                                   this_dm.stream,
                                   progress_bar=True,
                                   display_errors=verbose,
                                   num_concurrent_tasks=max_num_concurrent_tasks if isinstance(compiler.InputTypeInfo, FilenameTypeInfo) else 1,
                                 )

    # ----------------------------------------------------------------------
    # |  Execute
    
    # ----------------------------------------------------------------------
    def TestThreadProc( task_index, 
                        output_stream, 
                        on_status_update,
                        working_data,
                        configuration_results,
                        configuration,
                        iteration,
                      ):
        # Don't continue on error unless explicity requested
        if not continue_iterations_on_error and configuration_results.has_errors:
            return

        if no_status:
            on_status_update = lambda value: None

        # ----------------------------------------------------------------------
        def Invoke():
            internal_exception_result_code = 54321 

            # ----------------------------------------------------------------------
            def WriteLog(log_name, content):
                if content is None:
                    return

                log_filename = os.path.join( working_data.output_dir,
                                             configuration,
                                             "{0}.{1:06d}.txt".format(log_name, iteration),
                                           )

                with open(log_filename, 'w') as f:
                    f.write(content.replace('\r\n', '\n'))

                return log_filename

            # ----------------------------------------------------------------------
        
            # Run the test...
            on_status_update("Testing")

            execute_result = None
            execute_start_time = time.time()

            try:
                test_command_line = test_parser.CreateInvokeCommandLine(configuration_results.compiler_context, debug_on_error)

                if optional_code_coverage_extractor:
                    execute_result = optional_code_coverage_extractor.Execute( compiler,
                                                                               configuration_results.compiler_context,
                                                                               test_command_line,
                                                                             )
                else:
                    result, output = Process.Execute(test_command_line)

                    execute_result = CodeCoverageExtractorImpl.ExecuteResult( result, 
                                                                              output,
                                                                              None, # Populate below
                                                                            )

            except:
                execute_result = CodeCoverageExtractorImpl.ExecuteResult( internal_exception_result_code,
                                                                          None,
                                                                          None, # Populate below
                                                                        )
                raise

            finally:
                assert execute_result
                
                if execute_result.TestTime is None:
                    execute_result.TestTime = str(datetime.timedelta(seconds=(time.time() - execute_start_time)))

                original_test_output = execute_result.TestOutput

                execute_result.TestOutput = WriteLog("test", execute_result.TestOutput)
                execute_result.CoverageOutput = WriteLog("code_coverage_extrator", execute_result.CoverageOutput)

                configuration_results.execute_results[iteration] = execute_result

                if execute_result.TestResult != 0:
                    configuration_results.has_errors = True

            # Parse the results...
            on_status_update("Parsing")

            parse_start_time = time.time()

            try:
                test_parse_result = test_parser.Parse(original_test_output)
                
            except:
                test_parse_result = internal_exception_result_code
                raise

            finally:
                test_parse_time = str(datetime.timedelta(seconds=(time.time() - parse_start_time)))

                configuration_results.test_parse_results[iteration] = Results.TestParseResult( test_parse_result,
                                                                                               test_parse_time,
                                                                                             )

                if test_parse_result != 0:
                    configuration_results.has_errors = True

            # Validate code coverage metrics...
            if optional_code_coverage_validator:
                on_status_update("Validating Code Coverage")

                validate_start_time = time.time()

                try:
                    validation_result, validation_min = optional_code_coverage_validator.Validate( working_data.complete_result.Item,
                                                                                                   execute_result.CoveragePercentage,
                                                                                                 )
                except:
                    validation_result = internal_exception_result_code
                    validation_min = None

                    raise

                finally:
                    validation_parse_time = str(datetime.timedelta(seconds=(time.time() - validate_start_time)))

                    configuration_results.coverage_validation_results[iteration] = Results.CoverageValidationResult( validation_result,
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
    def EnqueueTestIfNecessary( iteration,
                                working_data,
                                configuration_results,
                                configuration,
                              ):
        if configuration_results.compiler_context is None or configuration_results.compile_result != 0:
            return

        if iteration == 0:
            configuration_results.execute_results = [ None, ] * iterations
            configuration_results.test_parse_results = [ None, ] * iterations
            configuration_results.coverage_validation_results = [ None, ] * iterations

        if configuration == "Debug":
            task_list = debug_tasks
        elif configuration == "Release":
            task_list = release_tasks
        else:
            assert False, configuration

        # ----------------------------------------------------------------------
        def TestThreadProcWrapper( # The first args must be named explicitly as TaskPool is using Interface.CreateCulledCallback
                                   task_index, 
                                   output_stream, 
                                   on_status_update,

                                   # Capture these values
                                   working_data=working_data,
                                   configuration_results=configuration_results,
                                   configuration=configuration,
                                   iteration=iteration,
                                 ):
            return TestThreadProc( task_index, 
                                   output_stream, 
                                   on_status_update,
                                   working_data,
                                   configuration_results,
                                   configuration,
                                   iteration,
                                 )

        # ----------------------------------------------------------------------

        task_list.append(TaskPool.Task( "{} [{}]{}".format( working_data.complete_result.Item,
                                                            configuration,
                                                            '' if iterations == 1 else " <Iteration {}>".format(iteration + 1),
                                                          ),
                                         TestThreadProcWrapper,
                                       ))

    # ----------------------------------------------------------------------

    for iteration in six.moves.range(iterations):
        for working_data in working_data_items:
            EnqueueTestIfNecessary(iteration, working_data, working_data.complete_result.debug, "Debug")
            EnqueueTestIfNecessary(iteration, working_data, working_data.complete_result.release, "Release")

    if debug_tasks or release_tasks:
        # ----------------------------------------------------------------------
        def CountTestFailures():
            failures = 0

            for working_data in working_data_items:
                for results in [ working_data.complete_result.debug,
                                 working_data.complete_result.release,
                               ]:
                    if results.has_errors:
                        failures += 1

            return failures

        # ----------------------------------------------------------------------

        with output_stream.SingleLineDoneManager( "Executing...",
                                                  done_suffix=lambda: inflect.no("test failure", CountTestFailures()),
                                                  suffix='\n',
                                                ) as this_dm:
            TaskPool.Execute( debug_tasks + release_tasks,
                              this_dm.stream,
                              progress_bar=True,
                              display_errors=verbose,
                              num_concurrent_tasks=max_num_concurrent_tasks if execute_in_parallel else 1,
                            )

    return [ working_data.complete_result for working_data in working_data_items ]

# ----------------------------------------------------------------------
# |  
# |  Command Line Functionality
# |  
# ----------------------------------------------------------------------
_compiler_type_info                         = CommandLine.EnumTypeInfo([ compiler.Name for compiler in COMPILERS ] + [ str(index) for index in six.moves.range(1, len(COMPILERS) + 1) ])
_test_parser_type_info                      = CommandLine.EnumTypeInfo([ test_parser.Name for test_parser in TEST_PARSERS ] + [ str(index) for index in six.moves.range(1, len(TEST_PARSERS) + 1) ])
_code_coverage_extractor_type_info          = CommandLine.EnumTypeInfo([ cce.Name for cce in CODE_COVERAGE_EXTRACTORS ] + [ str(index) for index in six.moves.range(1, len(CODE_COVERAGE_EXTRACTORS) + 1) ], arity='?')
_code_coverage_validator_type_info          = CommandLine.EnumTypeInfo([ ccv.Name for ccv in CODE_COVERAGE_VALIDATORS ] + [ str(index) for index in six.moves.range(1, len(CODE_COVERAGE_VALIDATORS) + 1) ], arity='?')
_ConfigurationTypeinfo                      = CommandLine.EnumTypeInfo(list(six.iterkeys(CONFIGURATIONS)))

# ----------------------------------------------------------------------
@CommandLine.EntryPoint # BugBug: Descriptions
@CommandLine.Constraints( configuration=_ConfigurationTypeinfo,
                          filename_or_dir=CommandLine.FilenameTypeInfo(match_any=True),
                          test_type=CommandLine.StringTypeInfo(arity='?'),
                          output_dir=CommandLine.DirectoryTypeInfo(ensure_exists=False, arity='?'),
                          execute_in_parallel=CommandLine.BoolTypeInfo(arity='?'),
                          iterations=CommandLine.IntTypeInfo(min=1, arity='?'),
                          output_stream=None,
                        )
def Test( configuration,
          filename_or_dir,
          test_type=None,
          output_dir=None,
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
          print_command_line=False,
       ):
    """Tests the given input"""
    
    configuration = CONFIGURATIONS[configuration]

    if os.path.isdir(filename_or_dir):
        if test_type is None:
            raise CommandLine.UsageException("The 'test_type' command line argument must be provided when 'filename_or_dir' is a directory.")

        if output_dir is None:
            raise CommandLine.UsageException("The 'output_dir' command line argument must be provided when 'filename_or_dir' is a directory.")

        return _ExecuteTreeImpl( filename_or_dir,
                                 test_type,
                                 output_dir,
                                 configuration.Compiler,
                                 configuration.TestParser,
                                 configuration.OptionalCodeCoverageExtractor,
                                 None, # BugBug: code_coverage_validator
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
                                 print_command_line=print_command_line,
                               )

    if quiet:
        raise CommandLine.UsageException("'quiet' is only used when executing tests via a directory")

    return _ExecuteImpl( filename_or_dir,
                         configuration.Compiler,
                         configuration.TestParser,
                         configuration.OptionalCodeCoverageExtractor,
                         None, # BugBug: code_coverage_validator
                         iterations=iterations,
                         debug_on_error=debug_on_error,
                         continue_iterations_on_error=continue_iterations_on_error,
                         debug_only=debug_only,
                         release_only=release_only,
                         output_stream=output_stream,
                         verbose=verbose,
                         preserve_ansi_escape_sequences=preserve_ansi_escape_sequences,
                         no_status=no_status,
                         print_command_line=print_command_line,
                       )

# ----------------------------------------------------------------------
@CommandLine.EntryPoint # BugBug: Descriptions
@CommandLine.Constraints( filename=CommandLine.FilenameTypeInfo(),
                          iterations=CommandLine.IntTypeInfo(min=1, arity='?'),
                          output_stream=None,
                        )
def TestFile( filename,
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
              print_command_line=False,
            ):
    """Tests the given input file"""

    # ----------------------------------------------------------------------
    def GetConfiguration():
        for key, configuration in six.iteritems(CONFIGURATIONS): 
            if configuration.Compiler.IsSupported(filename):
                return key
        
        return None

    # ----------------------------------------------------------------------

    configuration = GetConfiguration()
    if not configuration:
        raise CommandLine.UsageException("Unable to find a configuration with a compiler that supports the file '{}'".format(filename))

    return Test( configuration,
                 filename,
                 test_type=None,
                 output_dir=None,
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
                 print_command_line=print_command_line,
               )
 
# ----------------------------------------------------------------------
@CommandLine.EntryPoint # BugBug: Descriptions
@CommandLine.Constraints( configuration=_ConfigurationTypeinfo,
                          input_dir=CommandLine.DirectoryTypeInfo(),
                          test_type=CommandLine.StringTypeInfo(),
                          output_dir=CommandLine.DirectoryTypeInfo(ensure_exists=False),
                          execute_in_parallel=CommandLine.BoolTypeInfo(arity='?'),
                          iterations=CommandLine.IntTypeInfo(min=1, arity='?'),
                          output_stream=None,
                        )
def TestType( configuration,
              input_dir,
              test_type,
              output_dir,
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
              print_command_line=False,
       ):
    """Run tests for the test type with the specified configuration"""
    
    return Test( configuration,
                 input_dir,
                 test_type=test_type,
                 output_dir=output_dir,
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
                 print_command_line=print_command_line,
               )

# ----------------------------------------------------------------------
@CommandLine.EntryPoint
@CommandLine.Constraints( input_dir=CommandLine.DirectoryTypeInfo(),
                          test_type=CommandLine.StringTypeInfo(),
                          output_dir=CommandLine.DirectoryTypeInfo(ensure_exists=False),
                          execute_in_parallel=CommandLine.BoolTypeInfo(arity='?'),
                          iterations=CommandLine.IntTypeInfo(min=1, arity='?'),
                          output_stream=None,
                        )
def TestAll( input_dir,
             test_type,
             output_dir,
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
             print_command_line=False,
           ):
    """Run tests for the test type with all configurations"""
    
    with StreamDecorator(output_stream).DoneManager( line_prefix='',
                                                     prefix="\nResults: ",
                                                     suffix='\n',
                                                   ) as dm:
        for index, configuration in enumerate(six.iterkeys(CONFIGURATIONS)):
            header = "Testing '{}' ({} of {})...".format( configuration,
                                                          index + 1,
                                                          len(CONFIGURATIONS),
                                                        )
            dm.stream.write("{sep}\n{header}\n{sep}\n".format( header,
                                                               sep='-' * len(header),
                                                             ))
            with dm.stream.DoneManager( line_prefix='',
                                        prefix="\n{} Results: ".format(configuration),
                                        suffix='\n',
                                      ) as this_dm:
                this_dm.result = TestType( configuration,
                                           input_dir,
                                           test_type,
                                           output_dir,
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
                                           print_command_line=print_command_line,
                                         )

        return dm.result

# ----------------------------------------------------------------------
@CommandLine.EntryPoint
@CommandLine.Constraints( input_dir=CommandLine.DirectoryTypeInfo(),
                          test_type=CommandLine.StringTypeInfo(),
                          compiler=_compiler_type_info,
                          compiler_flag=CommandLine.StringTypeInfo(arity='*'),
                          output_stream=None,
                        )
def MatchTests( input_dir,
                test_type,
                compiler,
                compiler_flag=None,
                output_stream=sys.stdout,
                verbose=False,
              ):
    """Matches tests to production code for tests found within 'test_type' subdirectories."""
    pass # BugBug

# ----------------------------------------------------------------------
@CommandLine.EntryPoint
@CommandLine.Constraints( input_dir=CommandLine.DirectoryTypeInfo(),
                          test_type=CommandLine.StringTypeInfo(),
                          output_stream=None,
                        )
def MatchAllTests( input_dir,
                   test_type,
                   output_stream=sys.stdout,
                   verbose=False,
                 ):
    """Matches all tests for the test type across all compilers."""
    
    with StreamDecorator(output_stream).DoneManager( line_prefix='',
                                                     prefix="\nResults: ",
                                                     suffix='\n',
                                                   ) as dm:
        for index, configuration in enumerate(six.itervalues(CONFIGURATIONS)):
            dm.stream.write("Matching '{}' ({} of {})...".format( configuration.compiler,
                                                                  index + 1,
                                                                  len(COMPILERS),
                                                                ))
            with dm.stream.DoneManager(line_prefix="    ") as this_dm:
                this_dm.result = MatchTests( input_dir,
                                             test_type,
                                             configuration.compiler,
                                             output_stream=this_dm.stream,
                                             verbose=verbose,
                                           )

        return dm.result

# ----------------------------------------------------------------------
@CommandLine.EntryPoint
@CommandLine.Constraints( filename=CommandLine.FilenameTypeInfo(),
                          compiler=_compiler_type_info,
                          test_parser=_test_parser_type_info,
                          code_coverage_extractor=_code_coverage_extractor_type_info,
                          code_coverage_validator=_code_coverage_validator_type_info,
                          iterations=CommandLine.IntTypeInfo(min=1, arity='?'),
                          compiler_flag=CommandLine.DictTypeInfo(require_exact_match=False, arity='?'),
                          test_parser_flag=CommandLine.DictTypeInfo(require_exact_match=False, arity='?'),
                          code_coverage_extractor_flag=CommandLine.DictTypeInfo(require_exact_match=False, arity='?'),
                          code_coverage_validator_flag=CommandLine.DictTypeInfo(require_exact_match=False, arity='?'),
                          output_stream=None,
                        )
def Execute( filename,
             compiler,
             test_parser,
             code_coverage_extractor=None,
             code_coverage_validator=None,
             iterations=1,
             debug_on_error=False,
             continue_iterations_on_error=False,
             compiler_flag=None,
             test_parser_flag=None,
             code_coverage_extractor_flag=None,
             code_coverage_validator_flag=None,
             debug_only=False,
             release_only=False,
             output_stream=sys.stdout,
             verbose=False,
             preserve_ansi_escape_sequences=False,
             no_status=False,
             print_command_line=False,
           ):
    """
    Executes a specific test using a specific compiler, test parser, code coverage extractor, and code coverage validator. In most
    cases, it is easier to use a Test___ method rather than this one.
    """

    if code_coverage_extractor_flag and code_coverage_extractor is None:
        raise CommandLine.UsageException("Code coverage extractor flags are only valid when a code coverage extractor is specified")

    if code_coverage_validator_flag and code_coverage_validator is None:
        raise CommandLine.UsageException("Code coverage validator flags are only valid when a code coverage validator is specified")

    return _ExecuteImpl( filename,
                         _GetFromCommandLineArg(compiler, COMPILERS, compiler_flag),
                         _GetFromCommandLineArg(test_parser, TEST_PARSERS, test_parser_flag),
                         _GetFromCommandLineArg(code_coverage_extractor, CODE_COVERAGE_EXTRACTORS, code_coverage_extractor_flag, allow_empty=True),
                         _GetFromCommandLineArg(code_coverage_validator, CODE_COVERAGE_VALIDATORS, code_coverage_validator_flag, allow_empty=True),
                         iterations=iterations,
                         debug_on_error=debug_on_error,
                         continue_iterations_on_error=continue_iterations_on_error,
                         debug_only=debug_only,
                         release_only=release_only,
                         output_stream=output_stream,
                         verbose=verbose,
                         preserve_ansi_escape_sequences=preserve_ansi_escape_sequences,
                         no_status=no_status,
                         print_command_line=print_command_line,
                       )

# ----------------------------------------------------------------------
@CommandLine.EntryPoint
@CommandLine.Constraints( input_dir=CommandLine.DirectoryTypeInfo(),
                          test_type=CommandLine.StringTypeInfo(),
                          output_dir=CommandLine.DirectoryTypeInfo(ensure_exists=False),
                          compiler=_compiler_type_info,
                          test_parser=_test_parser_type_info,
                          code_coverage_extractor=_code_coverage_extractor_type_info,
                          code_coverage_validator=_code_coverage_validator_type_info,
                          execute_in_parallel=CommandLine.BoolTypeInfo(arity='?'),
                          iterations=CommandLine.IntTypeInfo(min=1, arity='?'),
                          compiler_flag=CommandLine.DictTypeInfo(require_exact_match=False, arity='?'),
                          test_parser_flag=CommandLine.DictTypeInfo(require_exact_match=False, arity='?'),
                          code_coverage_extractor_flag=CommandLine.DictTypeInfo(require_exact_match=False, arity='?'),
                          code_coverage_validator_flag=CommandLine.DictTypeInfo(require_exact_match=False, arity='?'),
                          output_stream=None,
                        )
def ExecuteTree( input_dir,
                 test_type,
                 output_dir,
                 compiler,
                 test_parser,
                 code_coverage_extractor=None,
                 code_coverage_validator=None,
                 execute_in_parallel=None,
                 iterations=1,
                 debug_on_error=False,
                 continue_iterations_on_error=False,
                 compiler_flag=None,
                 test_parser_flag=None,
                 code_coverage_extractor_flag=None,
                 code_coverage_validator_flag=None,
                 debug_only=False,
                 release_only=False,
                 output_stream=sys.stdout,
                 verbose=False,
                 quiet=False,
                 preserve_ansi_escape_sequences=False,
                 no_status=False,
                 print_command_line=False,
               ):
    """
    Executes tests found within 'test_type' subdirectories using a specific compiler, test parser, code coverage extractor, and code coverage validator. In most
    cases, it is easier to use a Test___ method rather than this one.
    """
    
    if code_coverage_extractor_flag and code_coverage_extractor is None:
        raise CommandLine.UsageException("Code coverage extractor flags are only valid when a code coverage extractor is specified")

    if code_coverage_validator_flag and code_coverage_validator is None:
        raise CommandLine.UsageException("Code coverage validator flags are only valid when a code coverage validator is specified")

    return _ExecuteTreeImpl( input_dir,
                             test_type,
                             output_dir,
                             _GetFromCommandLineArg(compiler, COMPILERS, compiler_flag),
                             _GetFromCommandLineArg(test_parser, TEST_PARSERS, test_parser_flag),
                             _GetFromCommandLineArg(code_coverage_extractor, CODE_COVERAGE_EXTRACTORS, code_coverage_extractor_flag, allow_empty=True),
                             _GetFromCommandLineArg(code_coverage_validator, CODE_COVERAGE_VALIDATORS, code_coverage_validator_flag, allow_empty=True),
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
                             print_command_line=print_command_line,
                           )

# ----------------------------------------------------------------------
def CommandLineSuffix():
    return StringHelpers.LeftJustify( textwrap.dedent(
                                        """\
                                        Where...

                                            <configuration> can be one of these values:
                                                  (A configuration provides pre-configured values for <compiler>, <test_parser>, and <code_coverage_extractor>)

                                        {configurations}

                                            Common values for <test_type> are (although these are not required):

                                        {test_types}

                                            <compiler> can be:

                                        {compilers}

                                            <test_parser> can be:

                                        {test_parsers}

                                            <code_coverage_extractor> can be:

                                        {code_coverage_extractors}

                                            <code_coverage_validator> can be:

                                        {code_coverage_validators}

                                        
                                        An valid item index or name may be used for these command line arguments:
                                            - <compiler>
                                            - <test_parser>
                                            - <code_coverage_extractor>
                                            - <code_coverage_validator>

                                        """).format( configurations='\n'.join([ "      - {}".format(config) for config in six.iterkeys(CONFIGURATIONS) ]),
                                                     test_types='\n'.join([ "      - {name:<30}  {desc}".format(name=ttmd.Name, desc=ttmd.Description) for ttmd in TEST_TYPES ]),
                                                     compilers='\n'.join([ "      {0}) {1:<20} {2}".format(index + 1, compiler.Name, compiler.Description) for index, compiler in enumerate(COMPILERS) ]),
                                                     test_parsers='\n'.join([ "      {0}) {1:<20} {2}".format(index + 1, compiler.Name, compiler.Description) for index, compiler in enumerate(TEST_PARSERS) ]),
                                                     code_coverage_extractors='\n'.join([ "      {0}) {1:<20} {2}".format(index + 1, compiler.Name, compiler.Description) for index, compiler in enumerate(CODE_COVERAGE_EXTRACTORS) ]),
                                                     code_coverage_validators='\n'.join([ "      {0}) {1:<20} {2}".format(index + 1, compiler.Name, compiler.Description) for index, compiler in enumerate(CODE_COVERAGE_VALIDATORS) ]),
                                                   ),
                                      4,
                                      skip_first_line=False,
                                    )

# ----------------------------------------------------------------------
# ----------------------------------------------------------------------
# ----------------------------------------------------------------------
def _GetFromCommandLineArg(arg, items, flags, allow_empty=False):
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
    return item(**flags)

# ----------------------------------------------------------------------
def _ExecuteImpl( filename_or_dir,
                  compiler,
                  test_parser,
                  code_coverage_extractor,
                  code_coverage_validator,
                  iterations,
                  debug_on_error,
                  continue_iterations_on_error,
                  debug_only,
                  release_only,
                  output_stream,
                  verbose,
                  preserve_ansi_escape_sequences,
                  no_status,
                  print_command_line,
                ):
    assert compiler.IsSupported(filename_or_dir), (compiler.Name, filename_or_dir)

    with StreamDecorator.GenerateAnsiSequenceStream( output_stream,
                                                     preserve_ansi_escape_sequences=preserve_ansi_escape_sequences,
                                                   ) as output_stream:
        output_stream.write('\n')

        temp_filename = tempfile.mkdtemp()

        complete_results = GenerateTestResults( [ filename_or_dir, ],
                                                temp_filename,
                                                compiler,
                                                test_parser,
                                                code_coverage_extractor,
                                                code_coverage_validator,
                                                execute_in_parallel=False,
                                                iterations=iterations,
                                                debug_on_error=debug_on_error,
                                                continue_iterations_on_error=continue_iterations_on_error,
                                                debug_only=debug_only,
                                                release_only=release_only,
                                                output_stream=output_stream,
                                                verbose=verbose,
                                                no_status=no_status,
                                                print_command_line=print_command_line,
                                              )
        FileSystem.RemoveFile(temp_filename)

        if not complete_results:
            return 0
        
        assert len(complete_results) == 1, len(complete_results)
        complete_result = complete_results[0]

        output_stream.write('\n')
        output_stream.write(complete_result.ToString( compiler,
                                                      test_parser,
                                                      code_coverage_extractor,
                                                      code_coverage_validator,
                                                    ))

        return complete_result.ResultCode() or 0

# ----------------------------------------------------------------------
def _ExecuteTreeImpl( input_dir,
                      test_type,
                      output_dir,
                      compiler,
                      test_parser,
                      code_coverage_extractor,
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
                      print_command_line,
                    ):
    if verbose and quiet:
        raise CommandLine.UsageException("'verbose' and 'quiet' are mutually exclusive options and cannot be specified together")

    with StreamDecorator.GenerateAnsiSequenceStream( output_stream,
                                                     preserve_ansi_escape_sequences=preserve_ansi_escape_sequences,
                                                   ) as output_stream:
        output_stream.write('\n')

        with StreamDecorator(output_stream).DoneManager( line_prefix='',
                                                         prefix="\nResults: ",
                                                         suffix='\n',
                                                       ) as dm:
            test_items = []
        
            dm.stream.write("Parsing '{}'...".format(input_dir))
            with dm.stream.DoneManager( done_suffix=lambda: "{} found".format(inflect.no("test", len(test_items))),
                                        suffix='\n',
                                      ) as this_dm:
                test_items = ExtractTestItems( input_dir,
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
        
            complete_results = GenerateTestResults( test_items,
                                                    output_dir,
                                                    compiler,
                                                    test_parser,
                                                    code_coverage_extractor,
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
                                                    print_command_line=print_command_line,
                                                  )
            if not complete_results:
                return 0

            if quiet:
                dm.stream.write('\n')
            else:
                for complete_result in complete_results:
                    dm.stream.write(complete_result.ToString( compiler,
                                                              test_parser,
                                                              code_coverage_extractor,
                                                              code_coverage_validator,
                                                            ))

            # Print summary
            nonlocals = Nonlocals( tests=0,
                                   failures=0,
                                 )

            # ----------------------------------------------------------------------
            def Output(test_item, result_type, results):
                result_code = results.ResultCode()
                if result_code is None:
                    return

                nonlocals.tests += 1

                if result_code == 0:
                    dm.stream.write("{}{}Succeeded:{}".format(colorama.Fore.GREEN, colorama.Style.BRIGHT, colorama.Style.RESET_ALL))
                else:
                    dm.stream.write("{}{}Failed:   {}".format(colorama.Fore.RED, colorama.Style.BRIGHT, colorama.Style.RESET_ALL))
                    nonlocals.failures += 1

                dm.stream.write(" {}, {}, {}\n".format( test_item,
                                                        result_type,
                                                        results.TotalTime(),
                                                      ))

            # ----------------------------------------------------------------------

            for complete_result in complete_results:
                Output(complete_result.Item, "Debug", complete_result.debug)
                Output(complete_result.Item, "Release", complete_result.release)

            dm.stream.write("\n{percentage:.02f}% - {total} build and run with {failures}.\n" \
                                    .format( percentage=0.0 if not nonlocals.tests else ((float(nonlocals.tests) - nonlocals.failures) / nonlocals.tests) * 100,
                                             total=inflect.no("test", nonlocals.tests),
                                             failures=inflect.no("failure", nonlocals.failures),
                                           ))

            if nonlocals.failures:
                dm.result = -1

            return dm.result

# ----------------------------------------------------------------------
# ----------------------------------------------------------------------
# ----------------------------------------------------------------------
if __name__ == "__main__":
    try: sys.exit(CommandLine.Main())
    except KeyboardInterrupt: pass