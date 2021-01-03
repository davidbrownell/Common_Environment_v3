# ----------------------------------------------------------------------
# |
# |  RunTests.py
# |
# |  David Brownell <db@DavidBrownell.com>
# |      2020-12-31 14:14:29
# |
# ----------------------------------------------------------------------
# |
# |  Copyright David Brownell 2020-21
# |  Distributed under the Boost Software License, Version 1.0. See
# |  accompanying file LICENSE_1_0.txt or copy at
# |  http://www.boost.org/LICENSE_1_0.txt.
# |
# ----------------------------------------------------------------------
"""Contains the RunTests method"""

import datetime
import multiprocessing
import os
import sys
import textwrap
import threading
import time
import traceback

from collections import namedtuple

import inflect as inflect_mod
import six

import CommonEnvironment
from CommonEnvironment import Nonlocals
from CommonEnvironment.CallOnExit import CallOnExit
from CommonEnvironment import FileSystem
from CommonEnvironment import TaskPool
from CommonEnvironment.TestExecutorImpl import TestExecutorImpl

from CommonEnvironment.TypeInfo.FundamentalTypes.DirectoryTypeInfo import DirectoryTypeInfo

# ----------------------------------------------------------------------
_script_fullpath                            = CommonEnvironment.ThisFullpath()
_script_dir, _script_name                   = os.path.split(_script_fullpath)
# ----------------------------------------------------------------------

from CompleteResult import CompleteResult
from Results import Results

# ----------------------------------------------------------------------
inflect                                     = inflect_mod.engine()


# ----------------------------------------------------------------------
if sys.version_info[0] == 2:
    # The 'readerwriterlock' python library is only available for python3.
    # This is actually OK, as the only compiler that should ever be used
    # in activated python2 environments is the python compiler (which can
    # be invoked in parallel). Create a stub, noop interface here so that
    # the code can be consistent between python2 and python3.
    class RWLock(object):
        # ----------------------------------------------------------------------
        @staticmethod
        def gen_wlock():
            raise Exception(
                textwrap.dedent(
                    """\
                    A write lock should be acquired in python2. Check the compiler
                    method 'ExecuteExclusively' to investigate why this might be
                    happening.

                    The only compiler expected to be invoked in python2 is the
                    python compiler.
                    """,
                ),
            )

        # ----------------------------------------------------------------------
        @classmethod
        def gen_rlock(cls):
            return cls._Lock()

        # ----------------------------------------------------------------------
        # ----------------------------------------------------------------------
        # ----------------------------------------------------------------------
        class _Lock(object):
            # ----------------------------------------------------------------------
            @staticmethod
            def acquire():
                pass

            # ----------------------------------------------------------------------
            @staticmethod
            def release():
                pass

else:
    from readerwriterlock import rwlock

    RWLock = rwlock.RWLockWrite


# ----------------------------------------------------------------------
# ----------------------------------------------------------------------
# ----------------------------------------------------------------------
def CreateRunTestsFunc(standard_test_executor):
    # ----------------------------------------------------------------------
    def RunTests(
        test_items,
        output_dir,
        compiler,
        test_parser,
        optional_test_executor,
        optional_code_coverage_validator,
        execute_tests_in_parallel,
        iterations,
        debug_on_error,
        continue_iterations_on_error,
        debug_only,
        release_only,
        build_only,
        output_stream,
        verbose,
        no_status,
        max_num_concurrent_tasks=None,
    ):
        assert test_items
        assert output_dir
        assert compiler
        assert test_parser
        assert iterations > 0, iterations
        assert output_stream

        max_num_concurrent_tasks = max_num_concurrent_tasks or multiprocessing.cpu_count()
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
        if optional_code_coverage_validator:
            execute_tests_in_parallel = False

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

        build_mutex = RWLock()

        # ----------------------------------------------------------------------
        def BuildThreadProc(task_index, output_stream, on_status_update):
            if no_status:
                on_status_update = lambda value: None

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

                on_status_update("Waiting")

                if compiler.ExecuteExclusively(configuration_results.compiler_context):
                    build_lock = build_mutex.gen_wlock()
                else:
                    build_lock = build_mutex.gen_rlock()

                build_lock.acquire()
                with CallOnExit(build_lock.release):
                    with working_data.execution_lock:
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

        if build_only:
            return [working_data.complete_result for working_data in working_data_items]

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

            on_status_update("Waiting")

            with working_data.execution_lock:
                on_status_update("Testing")

                # ----------------------------------------------------------------------
                def WriteLog(log_name, content):
                    if content is None:
                        return None

                    log_filename = os.path.join(
                        working_data.output_dir,
                        configuration,
                        "{0}.{1:06d}.txt".format(log_name, iteration + 1),
                    )

                    content = content.replace("\r\n", "\n")

                    # Try different techniques to write a variety of stubborn content
                    try:
                        with open(log_filename, "w") as f:
                            f.write(content)
                    except UnicodeEncodeError:
                        byte_content = None

                        for encoding in ["utf-8", "utf-16", "utf-32"]:
                            try:
                                byte_content = content.encode(encoding)
                                break
                            except UnicodeEncodeError:
                                pass

                        if byte_content:
                            with open(log_filename, "wb") as f:
                                f.write(byte_content)
                        else:
                            # We don't have a good way to write this content to a file,
                            # but don't want to lose it either.
                            output_stream.write(
                                "\n\nUnable to write the following content to a log file:\n\n",
                            )
                            output_stream.write(content)
                            output_stream.write("\n\n")

                            with open(log_filename, "w") as f:
                                f.write(
                                    "The content could not be encoded and has been written to stdout.\n",
                                )

                    return log_filename

                # ----------------------------------------------------------------------

                # Run the test...
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
                        executor = standard_test_executor

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
                        None,               # Populate below
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

                    execute_result.TestOutput = WriteLog(
                        "test",
                        execute_result.TestOutput,
                    )
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
            test_parse_benchmarks = []

            try:
                if original_test_output is None:
                    test_parse_result = -1
                else:
                    test_parse_result = test_parser.Parse(original_test_output)

                    if isinstance(test_parse_result, tuple):
                        test_parse_result, test_parse_benchmarks = test_parse_result

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
                ] = Results.TestParseResult(
                    test_parse_result,
                    test_parse_time,
                    test_parse_benchmarks,
                )

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

                    elif isinstance(compiler.InputTypeInfo, DirectoryTypeInfo):
                        # If the compiler processes an entire directory at a time, process the results
                        # individually to determine the final results.
                        validation_result = None
                        validation_min = None

                        for (filename, (percentage, percentage_desc)) in six.iteritems(
                            execute_result.CoveragePercentages,
                        ):
                            if percentage is None:
                                continue

                            this_validation_result, this_validation_min = optional_code_coverage_validator.Validate(
                                filename,
                                percentage,
                            )

                            if validation_result is None:
                                validation_result = this_validation_result
                                validation_min = this_validation_min

                            else:
                                validation_result = (
                                    this_validation_result
                                    if this_validation_result < 0
                                    else validation_result
                                )
                                assert this_validation_min == validation_min, (
                                    this_validation_min,
                                    validation_min,
                                )

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
                    num_concurrent_tasks=max_num_concurrent_tasks if execute_tests_in_parallel else 1,
                )

        return [working_data.complete_result for working_data in working_data_items]

    # ----------------------------------------------------------------------

    return RunTests
