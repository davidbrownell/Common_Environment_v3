# ----------------------------------------------------------------------
# |
# |  __main__.py
# |
# |  David Brownell <db@DavidBrownell.com>
# |      2019-03-11 08:27:51
# |
# ----------------------------------------------------------------------
# |
# |  Copyright David Brownell 2019
# |  Distributed under the Boost Software License, Version 1.0. See
# |  accompanying file LICENSE_1_0.txt or copy at
# |  http://www.boost.org/LICENSE_1_0.txt.
# |
# ----------------------------------------------------------------------
"""General purpose formatting executor."""

import importlib
import os
import sys
import textwrap
import threading

import inflect as inflect_mod
import six

import CommonEnvironment
from CommonEnvironment.CallOnExit import CallOnExit
from CommonEnvironment import CommandLine
from CommonEnvironment import FileSystem
from CommonEnvironment.StreamDecorator import StreamDecorator
from CommonEnvironment import StringHelpers
from CommonEnvironment import TaskPool

# ----------------------------------------------------------------------
_script_fullpath                            = CommonEnvironment.ThisFullpath()
_script_dir, _script_name                   = os.path.split(_script_fullpath)
# ----------------------------------------------------------------------

if os.getenv("DEVELOPMENT_ENVIRONMENT_FORMATTERS") and os.getenv(
    "DEVELOPMENT_ENVIRONMENT_FUNDAMENTAL",
):
    # Get plugins across multiple repositories
    sys.path.insert(0, os.getenv("DEVELOPMENT_ENVIRONMENT_FUNDAMENTAL"))
    with CallOnExit(lambda: sys.path.pop(0)):
        from RepositoryBootstrap.SetupAndActivate import DynamicPluginArchitecture as DPA

    # ----------------------------------------------------------------------
    def EnumeratePlugins():
        for mod in DPA.EnumeratePlugins("DEVELOPMENT_ENVIRONMENT_FORMATTERS"):
            yield mod

    # ----------------------------------------------------------------------

else:
    # Get plugins relative to this file

    # ----------------------------------------------------------------------
    def EnumeratePlugins():
        plugin_dir = os.path.join(_script_dir, "Plugins")
        assert os.path.isdir(plugin_dir), plugin_dir

        sys.path.insert(0, plugin_dir)
        with CallOnExit(lambda: sys.path.pop(0)):
            for item in os.listdir(plugin_dir):
                fullpath = os.path.join(plugin_dir, item)
                if not os.path.isfile(fullpath):
                    continue

                basename, ext = os.path.splitext(item)

                if ext != ".py":
                    continue

                yield importlib.import_module(basename)

    # ----------------------------------------------------------------------

# ----------------------------------------------------------------------
inflect                                     = inflect_mod.engine()

# ----------------------------------------------------------------------
# ----------------------------------------------------------------------
# ----------------------------------------------------------------------
def _LoadFormatterFromModule(mod):
    for potential_name in ["Formatter", "Plugin"]:
        result = getattr(mod, potential_name, None)
        if result is not None:
            return result

    raise Exception("The module '{}' does not contain a supported formatter".format(mod))


# ----------------------------------------------------------------------
FORMATTERS                                  = [_LoadFormatterFromModule(mod) for mod in EnumeratePlugins()]

# ----------------------------------------------------------------------
# |
# |  Command Line Functionality
# |
# ----------------------------------------------------------------------
_formatter_type_info                        = CommandLine.EnumTypeInfo(
    [formatter.Name for formatter in FORMATTERS] + [str(index) for index in six.moves.range(1, len(FORMATTERS) + 1)],
    arity="?",
)

# ----------------------------------------------------------------------
@CommandLine.EntryPoint(
    filename_or_dir=CommandLine.EntryPoint.Parameter(
        "Filename or directory (used to search for files) to format",
    ),
    formatter=CommandLine.EntryPoint.Parameter("The formatter to use while formatting"),
    overwrite=CommandLine.EntryPoint.Parameter("Overwrite the input files with changes (if any)"),
    quiet=CommandLine.EntryPoint.Parameter(
        "Only output changes (if any). This option is only valid when providing a single file",
    ),
    single_threaded=CommandLine.EntryPoint.Parameter(
        "Run with a single thread. This option is only valid when providing a directory",
    ),
    skip_generated_dirs=CommandLine.EntryPoint.Parameter(
        "Do not include files from directories that include 'generated'",
    ),
    hint_filename=CommandLine.EntryPoint.Parameter(
        "Filename passed as a hint to an underlying formatter; the content to format should still be in 'filename_or_dir'",
    ),
    verbose=CommandLine.EntryPoint.Parameter("Verbose output"),
    preserve_ansi_escape_sequences=CommandLine.EntryPoint.Parameter(
        "Keep ansi escape sequences (used for color and cursor movement) when invoking this script from another one",
    ),
)
@CommandLine.Constraints(
    filename_or_dir=CommandLine.FilenameTypeInfo(
        match_any=True,
    ),
    formatter=_formatter_type_info,
    hint_filename=CommandLine.FilenameTypeInfo(
        arity="?",
    ),
    output_stream=None,
)
def Format(
    filename_or_dir,
    formatter=None,
    overwrite=False,
    quiet=False,
    single_threaded=False,
    skip_generated_dirs=False,
    hint_filename=None,
    output_stream=sys.stdout,
    verbose=False,
    preserve_ansi_escape_sequences=False,
):
    """Formats the given input"""

    original_output_stream = output_stream

    with StreamDecorator.GenerateAnsiSequenceStream(
        None if quiet else output_stream,
        preserve_ansi_escape_sequences=preserve_ansi_escape_sequences,
    ) as output_stream:
        # Ensure correct argument usage
        if os.path.isfile(filename_or_dir):
            if formatter is not None:
                raise CommandLine.UsageException(
                    "The command line option 'formatter' can only be specified when providing an input directory",
                )

            if single_threaded:
                raise CommandLine.UsageException(
                    "The command line option 'single_threaded' can only be specified when providing an input directory",
                )

            if skip_generated_dirs:
                raise CommandLine.UsageException(
                    "The command line option 'skip_generated_dirs' can only be specified when providing an input directory",
                )

        elif os.path.isdir(filename_or_dir):
            if quiet:
                raise CommandLine.UsageException(
                    "The command line option 'quiet' can only be specified when providing an input filename",
                )

            if hint_filename is not None:
                raise CommandLine.UsageException(
                    "The command line option 'hint_filename' can only be specified when providing an input filename",
                )

            # Ensure that we output changes
            if not overwrite:
                verbose = True

        with output_stream.DoneManager(
            line_prefix="",
            prefix="\nResults: ",
            suffix="\n",
        ) as dm:
            if os.path.isfile(filename_or_dir):
                formatter = _GetFormatterByFilename(filename_or_dir)
                if formatter is None:
                    dm.stream.write(
                        "\nERROR: '{}' is not a supported file type.\n".format(filename_or_dir),
                    )
                    dm.result = -1

                    return dm.result

                nonlocals = CommonEnvironment.Nonlocals(
                    has_changes=False,
                )

                dm.stream.write("Formatting '{}'...".format(filename_or_dir))
                with dm.stream.DoneManager(
                    done_suffix=lambda: None if nonlocals.has_changes else "No changes detected",
                ) as this_dm:
                    output, nonlocals.has_changes = formatter.Format(
                        filename_or_dir,
                        hint_filename=hint_filename,
                    )

                    if nonlocals.has_changes:
                        if overwrite:
                            with open(filename, "w") as f:
                                f.write(output)
                        else:
                            (original_output_stream if quiet else this_dm.stream).write(output)

                    return this_dm.result

            # Process the dir
            assert os.path.isdir(filename_or_dir), filename_or_dir

            if formatter is not None:
                formatters = [_GetFormatterByName(formatter)]
            else:
                formatters = FORMATTERS

            dm.stream.write("\n")

            changed_files = []
            changed_files_lock = threading.Lock()

            for formatter_index, formatter in enumerate(formatters):
                dm.stream.write(
                    "Processing with '{}' ({} of {})...".format(
                        formatter.Name,
                        formatter_index + 1,
                        len(formatters),
                    ),
                )
                with dm.stream.DoneManager(
                    suffix="\n",
                ) as this_dm:
                    # ----------------------------------------------------------------------
                    def Invoke(input_filename, output_stream):
                        content, has_changes = formatter.Format(input_filename)
                        if not has_changes:
                            return

                        if overwrite:
                            with open(input_filename, "w") as f:
                                f.write(content)
                        else:
                            output_stream.write(content)

                        with changed_files_lock:
                            changed_files.append(input_filename)

                    # ----------------------------------------------------------------------

                    this_dm.result = _Impl(
                        "Formatting files...",
                        Invoke,
                        this_dm.stream,
                        verbose,
                        formatter,
                        filename_or_dir,
                        single_threaded,
                        skip_generated_dirs,
                    )

            if not changed_files:
                dm.stream.write("\nNo files were changed.\n")
            else:
                dm.stream.write(
                    textwrap.dedent(
                        """\

                        {count} {prefix}written:

                        {names}

                        """,
                    ).format(
                        count=inflect.no("file", len(changed_files)),
                        prefix="" if overwrite else "would be ",
                        names="\n".join(
                            ["    - {}".format(filename) for filename in sorted(changed_files)],
                        ),
                    ),
                )

    return dm.result


# ----------------------------------------------------------------------
@CommandLine.EntryPoint(
    filename_or_dir=CommandLine.EntryPoint.Parameter(
        "Filename or directory (used to search for files) to query for changes",
    ),
    formatter=CommandLine.EntryPoint.Parameter("The formatter to use while querying for changes"),
    single_threaded=CommandLine.EntryPoint.Parameter(
        "Run with a single thread. This option is only valid when providing a directory",
    ),
    skip_generated_dirs=CommandLine.EntryPoint.Parameter(
        "Do not include files from directories that include 'generated'",
    ),
    verbose=CommandLine.EntryPoint.Parameter("Verbose output"),
    preserve_ansi_escape_sequences=CommandLine.EntryPoint.Parameter(
        "Keep ansi escape sequences (used for color and cursor movement) when invoking this script from another one",
    ),
)
@CommandLine.Constraints(
    filename_or_dir=CommandLine.FilenameTypeInfo(
        match_any=True,
    ),
    formatter=_formatter_type_info,
    output_stream=None,
)
def HasChanges(
    filename_or_dir,
    formatter=None,
    single_threaded=False,
    skip_generated_dirs=False,
    output_stream=sys.stdout,
    verbose=False,
    preserve_ansi_escape_sequences=False,
):
    """Determines if changes would be made to the provided input"""

    with StreamDecorator.GenerateAnsiSequenceStream(
        output_stream,
        preserve_ansi_escape_sequences=preserve_ansi_escape_sequences,
    ) as output_stream:
        # Ensure correct argument usage
        if os.path.isfile(filename_or_dir):
            if formatter is not None:
                raise CommandLine.UsageException(
                    "The command line option 'formatter' can only be specified when providing an input directory",
                )

            if single_threaded:
                raise CommandLine.UsageException(
                    "The command line option 'single_threaded' can only be specified when providing an input directory",
                )

            if skip_generated_dirs:
                raise CommandLine.UsageException(
                    "The command line option 'skip_generated_dirs' can only be specified when providing an input directory",
                )

        with output_stream.DoneManager(
            line_prefix="",
            prefix="\nResults: ",
            suffix="\n",
        ) as dm:
            if os.path.isfile(filename_or_dir):
                formatter = _GetFormatterByFilename(filename_or_dir)
                if formatter is None:
                    dm.stream.write(
                        "\nERROR: '{}' is not a supported file type.\n".format(filename_or_dir),
                    )
                    dm.result = -1

                    return dm.result

                dm.stream.write("Detecting changes in '{}'...".format(filename_or_dir))
                with dm.stream.DoneManager() as this_dm:
                    if formatter.HasChanges(filename_or_dir):
                        this_dm.stream.write("***** Has Changes *****\n")
                        this_dm.result = 1

                return dm.result

            # Process the dir
            assert os.path.isdir(filename_or_dir), filename_or_dir

            if formatter is not None:
                formatters = [_GetFormatterByName(formatter)]
            else:
                formatters = FORMATTERS

            dm.stream.write("\n")

            changed_files = []
            changed_files_lock = threading.Lock()

            for formatter_index, formatter in enumerate(formatters):
                dm.stream.write(
                    "Processing with '{}' ({} of {})...".format(
                        formatter.Name,
                        formatter_index + 1,
                        len(formatters),
                    ),
                )
                with dm.stream.DoneManager(
                    suffix="\n",
                ) as this_dm:
                    # ----------------------------------------------------------------------
                    def Invoke(input_filename, output_stream):
                        if formatter.HasChanges(input_filename):
                            with changed_files_lock:
                                changed_files.append(input_filename)

                    # ----------------------------------------------------------------------

                    this_dm.result = _Impl(
                        "Detecting changes...",
                        Invoke,
                        this_dm.stream,
                        verbose,
                        formatter,
                        filename_or_dir,
                        single_threaded,
                        skip_generated_dirs,
                    )

            if not changed_files:
                dm.stream.write("\nNo files would be changed.\n")
            else:
                dm.stream.write(
                    textwrap.dedent(
                        """\

                        There would be {count}:

                        {names}

                        """,
                    ).format(
                        count=inflect.no("change", len(changed_files)),
                        names="\n".join(
                            ["    - {}".format(filename) for filename in sorted(changed_files)],
                        ),
                    ),
                )

            dm.result = 1 if changed_files else 0

            return dm.result


# ----------------------------------------------------------------------
def CommandLineSuffix():
    return StringHelpers.LeftJustify(
        textwrap.dedent(
            """\
            Where...

                <formatter> can be one of these values:

            {formatters}

            """,
        ).format(
            formatters="\n".join(
                [
                    "      - {name:<30}  {desc}".format(
                        name=formatter.Name,
                        desc=formatter.Description,
                    ) for formatter in FORMATTERS
                ],
            ),
        ),
        4,
        skip_first_line=False,
    )


# ----------------------------------------------------------------------
# ----------------------------------------------------------------------
# ----------------------------------------------------------------------
def _GetFormatterByName(formatter_param):
    if formatter_param.isdigit():
        formatter_param = int(formatter_param)
        assert formatter_param < len(FORMATTERS)

        return FORMATTERS[formatter_param]

    for formatter in FORMATTERS:
        if formatter.Name == formatter_param:
            return formatter

    assert False, formatter_param


# ----------------------------------------------------------------------
def _GetFormatterByFilename(filename):
    for formatter in FORMATTERS:
        if formatter.InputTypeInfo.ValidateItemNoThrow(filename) is None:
            return formatter

    return None


# ----------------------------------------------------------------------
def _Impl(
    activity_desc,
    activity_func,
    output_stream,
    verbose,
    formatter,
    input_dir,
    single_threaded,
    skip_generated_dirs,
):
    # activity_func: def Func(input_filename, output_stream) -> result code

    output_stream.write("\nSearching for files in '{}'...".format(input_dir))

    input_filenames = []

    with output_stream.DoneManager(
        done_suffix=lambda: "{} found".format(inflect.no("file", len(input_filenames))),
    ):
        input_filenames += [
            filename
            for filename in FileSystem.WalkFiles(
                input_dir,
                traverse_exclude_dir_names=[lambda name: "generated" in name.lower()] if skip_generated_dirs else [],
            )
            if formatter.InputTypeInfo.ValidateItemNoThrow(filename) is None
        ]

    if not input_filenames:
        return 0

    # ----------------------------------------------------------------------
    def Invoke(task_index, output_stream):
        return activity_func(input_filenames[task_index], output_stream)

    # ----------------------------------------------------------------------

    with output_stream.SingleLineDoneManager(activity_desc) as this_dm:
        this_dm.result = TaskPool.Execute(
            [TaskPool.Task(filename, Invoke) for filename in input_filenames],
            this_dm.stream,
            progress_bar=True,
            num_concurrent_tasks=1 if single_threaded else None,
            verbose=verbose,
        )

    return this_dm.result


# ----------------------------------------------------------------------
# ----------------------------------------------------------------------
# ----------------------------------------------------------------------
if __name__ == "__main__":
    try:
        sys.exit(CommandLine.Main())
    except KeyboardInterrupt:
        pass
