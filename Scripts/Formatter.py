# ----------------------------------------------------------------------
# |
# |  Formatter.py
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

assert os.getenv("DEVELOPMENT_ENVIRONMENT_FUNDAMENTAL")
sys.path.insert(0, os.getenv("DEVELOPMENT_ENVIRONMENT_FUNDAMENTAL"))
with CallOnExit(lambda: sys.path.pop(0)):
    from RepositoryBootstrap.SetupAndActivate import DynamicPluginArchitecture as DPA

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
FORMATTERS                                  = [_LoadFormatterFromModule(mod) for mod in DPA.EnumeratePlugins("DEVELOPMENT_ENVIRONMENT_FORMATTERS")]

# ----------------------------------------------------------------------
# |
# |  Command Line Functionality
# |
# ----------------------------------------------------------------------
_formatter_type_info                        = CommandLine.EnumTypeInfo(
    [formatter.Name for formatter in FORMATTERS] + [str(index) for index in six.moves.range(1, len(FORMATTERS) + 1)],
)

# ----------------------------------------------------------------------
@CommandLine.EntryPoint(
    filename=CommandLine.EntryPoint.Parameter("Filename to format"),
    overwrite=CommandLine.EntryPoint.Parameter(
        "The formatted content is written to output unless `overwrite` is provided, in which case the file's content are updated",
    ),
    quiet=CommandLine.EntryPoint.Parameter(
        "Only the formatted content is written to output if provided",
    ),
)
@CommandLine.Constraints(
    filename=CommandLine.FilenameTypeInfo(),
    output_stream=None,
)
def FormatFile(
    filename,
    overwrite=False,
    quiet=False,
    output_stream=sys.stdout,
    preserve_ansi_escape_sequences=False,
):
    """Formats the given input"""

    original_output_stream = output_stream

    with StreamDecorator.GenerateAnsiSequenceStream(
        None if quiet else output_stream,
        preserve_ansi_escape_sequences=preserve_ansi_escape_sequences,
    ) as output_stream:
        with output_stream.DoneManager(
            line_prefix="",
            prefix="\nResults: ",
            suffix="\n",
        ) as dm:
            formatter = _GetFormatterByFilename(filename)
            if formatter is None:
                dm.stream.write("\nERROR: '{}' is not a supported file type.\n".format(filename))
                dm.result = -1

                return dm.result

            dm.stream.write("Formatting '{}'...".format(filename))

            nonlocals = CommonEnvironment.Nonlocals(
                has_changes=False,
            )

            with dm.stream.DoneManager(
                done_suffix=lambda: None if nonlocals.has_changes else "No changes detected",
            ) as this_dm:
                output, nonlocals.has_changes = formatter.Format(filename)

                if nonlocals.has_changes:
                    if overwrite:
                        with open(filename, "w") as f:
                            f.write(output)
                    else:
                        (original_output_stream if quiet else this_dm.stream).write(output)

            return dm.result


# ----------------------------------------------------------------------
@CommandLine.EntryPoint(
    formatter=CommandLine.EntryPoint.Parameter("Formatter name or index to use"),
    input_dir=CommandLine.EntryPoint.Parameter("Search this directory for files to format"),
)
@CommandLine.Constraints(
    formatter=_formatter_type_info,
    input_dir=CommandLine.DirectoryTypeInfo(),
    output_stream=None,
)
def FormatTree(
    formatter,
    input_dir,
    single_threaded=False,
    output_stream=sys.stdout,
    preserve_ansi_escape_sequences=False,
):
    """Formats files in the given directory"""

    with StreamDecorator.GenerateAnsiSequenceStream(
        output_stream,
        preserve_ansi_escape_sequences=preserve_ansi_escape_sequences,
    ) as output_stream:
        with output_stream.DoneManager(
            line_prefix="",
            prefix="\nResults: ",
            suffix="\n",
        ) as dm:
            formatter = _GetFormatterByName(formatter)
            assert formatter

            dm.result = _FormatTreeImpl(
                dm.stream,
                formatter,
                input_dir,
                single_threaded=single_threaded,
            )

            return dm.result


@CommandLine.EntryPoint(
    input_dir=CommandLine.EntryPoint.Parameter("Search this directory for files to format"),
)
@CommandLine.Constraints(
    input_dir=CommandLine.DirectoryTypeInfo(),
    output_stream=None,
)
def FormatAll(
    input_dir,
    single_threaded=False,
    output_stream=sys.stdout,
    preserve_ansi_escape_sequences=False,
):
    """Formats files in the given input"""

    with StreamDecorator.GenerateAnsiSequenceStream(
        output_stream,
        preserve_ansi_escape_sequences=preserve_ansi_escape_sequences,
    ) as output_stream:
        with output_stream.DoneManager(
            line_prefix="",
            prefix="\nResults: ",
            suffix="\n",
        ) as dm:
            for index, formatter in enumerate(FORMATTERS):
                header = "Processing with '{}' ({} of {})...".format(
                    formatter.Name,
                    index + 1,
                    len(FORMATTERS),
                )

                dm.stream.write(
                    "{sep}\n{header}\n{sep}\n".format(
                        header=header,
                        sep="-" * len(header),
                    ),
                )
                with dm.stream.DoneManager(
                    line_prefix="",
                    prefix="\nResults: ",
                    suffix="\n",
                ) as this_dm:
                    this_dm.result = _FormatTreeImpl(
                        this_dm.stream,
                        formatter,
                        input_dir,
                        single_threaded=single_threaded,
                    )

            return dm.result


# ----------------------------------------------------------------------
@CommandLine.EntryPoint(
    filename=CommandLine.EntryPoint.Parameter("Filename to change for formatting changes"),
)
@CommandLine.Constraints(
    filename=CommandLine.FilenameTypeInfo(),
    output_stream=None,
)
def HasChangesFile(
    filename,
    output_stream=sys.stdout,
    preserve_ansi_escape_sequences=False,
):
    """Returns 1 if the given filename would change after formatting"""

    with StreamDecorator.GenerateAnsiSequenceStream(
        output_stream,
        preserve_ansi_escape_sequences=preserve_ansi_escape_sequences,
    ) as output_stream:
        with output_stream.DoneManager(
            line_prefix="",
            prefix="\nResults: ",
            suffix="\n",
        ) as dm:
            formatter = _GetFormatterByFilename(filename)
            if formatter is None:
                dm.stream.write("\nERROR: '{}' is not a supported file type.\n".format(filename))
                dm.result = -1

                return dm.result

            dm.stream.write("Detecting changes in '{}'...".format(filename))
            with dm.stream.DoneManager() as this_dm:
                if formatter.HasChanges(filename):
                    this_dm.stream.write("***** Has Changes *****\n")
                    this_dm.result = 1

            return dm.result


# ----------------------------------------------------------------------
@CommandLine.EntryPoint(
    formatter=CommandLine.EntryPoint.Parameter("Formatter name or index to use"),
    input_dir=CommandLine.EntryPoint.Parameter(
        "Search this directory for files to check for formatting changes",
    ),
)
@CommandLine.Constraints(
    formatter=_formatter_type_info,
    input_dir=CommandLine.DirectoryTypeInfo(),
    output_stream=None,
)
def HasChangesTree(
    formatter,
    input_dir,
    single_threaded=False,
    output_stream=sys.stdout,
    preserve_ansi_escape_sequences=False,
):
    """Returns 1 if files in the given directory would change after formatting"""

    if True:
        output_stream = StreamDecorator(output_stream)
    with StreamDecorator.GenerateAnsiSequenceStream(
        output_stream,
        preserve_ansi_escape_sequences=preserve_ansi_escape_sequences,
    ) as output_stream:
        with output_stream.DoneManager(
            line_prefix="",
            prefix="\nResults: ",
            suffix="\n",
        ) as dm:
            formatter = _GetFormatterByName(formatter)
            assert formatter

            dm.result = _HasChangesTreeImpl(
                dm.stream,
                formatter,
                input_dir,
                single_threaded=single_threaded,
            )

            return dm.result


# ----------------------------------------------------------------------
@CommandLine.EntryPoint(
    input_dir=CommandLine.EntryPoint.Parameter(
        "Search this directory for files to check for formatting changes",
    ),
)
@CommandLine.Constraints(
    input_dir=CommandLine.DirectoryTypeInfo(),
    output_stream=None,
)
def HasChangesAll(
    input_dir,
    single_threaded=False,
    output_stream=sys.stdout,
    preserve_ansi_escape_sequences=False,
):
    """Returns 1 if files in the given input would change after formatting"""

    with StreamDecorator.GenerateAnsiSequenceStream(
        output_stream,
        preserve_ansi_escape_sequences=preserve_ansi_escape_sequences,
    ) as output_stream:
        with output_stream.DoneManager(
            line_prefix="",
            prefix="\nResults: ",
            suffix="\n",
        ) as dm:
            for index, formatter in enumerate(FORMATTERS):
                header = "Processing with '{}' ({} of {})...".format(
                    formatter.Name,
                    index + 1,
                    len(FORMATTERS),
                )

                dm.stream.write(
                    "{sep}\n{header}\n{sep}\n".format(
                        header=header,
                        sep="-" * len(header),
                    ),
                )
                with dm.stream.DoneManager(
                    line_prefix="",
                    prefix="\nResults: ",
                    suffix="\n",
                ) as this_dm:
                    this_dm.result = _HasChangesTreeImpl(
                        this_dm.stream,
                        formatter,
                        input_dir,
                        single_threaded=single_threaded,
                    )

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
def _FormatTreeImpl(
    output_stream,
    formatter,
    input_dir,
    single_threaded=False,
):
    changed_files = []
    changed_files_lock = threading.Lock()

    # ----------------------------------------------------------------------
    def Invoke(input_filename, output_stream):
        content, has_changes = formatter.Format(input_filename)
        if not has_changes:
            return

        with open(input_filename, "w") as f:
            f.write(content)

        with changed_files_lock:
            changed_files.append(input_filename)

    # ----------------------------------------------------------------------

    result = _Impl(
        "Formatting files...",
        Invoke,
        output_stream,
        formatter,
        input_dir,
        single_threaded,
    )

    if result != 0:
        return result

    if not changed_files:
        output_stream.write("\nNo files would be changed.\n")
    else:
        output_stream.write(
            textwrap.dedent(
                """\

                {count} written:

                {names}

                """,
            ).format(
                count=inflect.no("file", len(changed_files)),
                names="\n".join(["    - {}".format(filename) for filename in sorted(changed_files)]),
            ),
        )

    return 0


# ----------------------------------------------------------------------
def _HasChangesTreeImpl(
    output_stream,
    formatter,
    input_dir,
    single_threaded=False,
):
    changed_files = []
    changed_files_lock = threading.Lock()

    # ----------------------------------------------------------------------
    def Invoke(input_filename, output_stream):
        if formatter.HasChanges(input_filename):
            with changed_files_lock:
                changed_files.append(input_filename)

    # ----------------------------------------------------------------------

    result = _Impl(
        "Detecting changes...",
        Invoke,
        output_stream,
        formatter,
        input_dir,
        single_threaded,
    )

    if result != 0:
        return result

    if not changed_files:
        output_stream.write("\nNo files would be changed.\n")
    else:
        output_stream.write(
            textwrap.dedent(
                """\

                These {count} would be changed:

                {names}

                """,
            ).format(
                count=inflect.no("file", len(changed_files)),
                names="\n".join(["    - {}".format(filename) for filename in sorted(changed_files)]),
            ),
        )

    return 1 if changed_files else 0


# ----------------------------------------------------------------------
def _Impl(activity_desc, activity_func, output_stream, formatter, input_dir, single_threaded):
    # activity_func: def Func(input_filename, output_stream) -> result code

    output_stream.write("\nSearching for files in '{}'...".format(input_dir))

    input_filenames = []

    with output_stream.DoneManager(
        done_suffix=lambda: "{} found".format(inflect.no("file", len(input_filenames))),
    ):
        input_filenames += [filename for filename in FileSystem.WalkFiles(input_dir) if formatter.InputTypeInfo.ValidateItemNoThrow(filename) is None]

    if not input_filenames:
        return 0

    # ----------------------------------------------------------------------
    def Invoke(task_index, output_stream):
        return activity_func(input_filenames[task_index], output_stream)

    # ----------------------------------------------------------------------

    with output_stream.SingleLineDoneManager(activity_desc) as this_dm:
        this_dm.result = TaskPool.Execute(
            [TaskPool.Task(filename, Invoke) for filename in input_filenames], this_dm.stream, progress_bar=True, num_concurrent_tasks=1 if single_threaded else None,
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
