# ----------------------------------------------------------------------
# |
# |  BlackAndBrown.py
# |
# |  David Brownell <db@DavidBrownell.com>
# |      2019-01-04 11:32:25
# |
# ----------------------------------------------------------------------
# |
# |  Copyright David Brownell 2019
# |  Distributed under the Boost Software License, Version 1.0. See
# |  accompanying file LICENSE_1_0.txt or copy at
# |  http://www.boost.org/LICENSE_1_0.txt.
# |
# ----------------------------------------------------------------------
"""Runs the black formatter with modifications ("AndBrown")"""

import os
import re
import sys
import textwrap

import inflect as inflect_mod

import CommonEnvironment
from CommonEnvironment import CommandLine
from CommonEnvironment import FileSystem
from CommonEnvironment.StreamDecorator import StreamDecorator

from CommonEnvironment import BlackAndBrown as BlackAndBrownMod

# ----------------------------------------------------------------------
_script_fullpath                            = CommonEnvironment.ThisFullpath()
_script_dir, _script_name                   = os.path.split(_script_fullpath)
# ----------------------------------------------------------------------

inflect                                     = inflect_mod.engine()

# ----------------------------------------------------------------------
# These methods are similar in the type and number of args taken as input.
# The following objects describe parameters common to all methods.
_common_constraints                                     = {
    "input": CommandLine.FilenameTypeInfo(
        match_any=True,
        arity="+",
    ),
    "black_line_length": CommandLine.IntTypeInfo(
        min=10,
        arity="?",
    ),
    "plugin_dir": CommandLine.DirectoryTypeInfo(
        arity="*",
    ),
    "plugin_arg": CommandLine.DictTypeInfo(
        require_exact_match=False,
        arity="?",
    ),
    "include_plugin": CommandLine.StringTypeInfo(
        arity="*",
    ),
    "exclude_plugin": CommandLine.StringTypeInfo(
        arity="*",
    ),
    "output_stream": None,
}

# ----------------------------------------------------------------------
@CommandLine.EntryPoint()
@CommandLine.Constraints(**_common_constraints)
def Format(
    input,
    overwrite=False,
    black_line_length=None,
    plugin_dir=None,
    plugin_arg=None,
    include_plugin=None,
    exclude_plugin=None,
    debug=False,
    exclude_generated_dirs=False,
    output_stream=sys.stdout,
):
    """Formats the provided input using BlackAndBrown"""

    inputs = input
    del input

    plugin_dirs = plugin_dir
    del plugin_dir

    plugin_args = plugin_arg
    del plugin_arg

    include_plugins = include_plugin or None
    del include_plugin

    exclude_plugins = exclude_plugin or None
    del exclude_plugin

    with StreamDecorator(output_stream).DoneManager(
        line_prefix="",
        prefix="\nResults: ",
        suffix="\n",
    ) as dm:
        input_filenames = []

        dm.stream.write("Resolving input...")
        with dm.stream.DoneManager(
            done_suffix=lambda: "{} found".format(inflect.no("input file", len(input_filenames))),
        ):
            input_filenames += _InputToFilenames(inputs, exclude_generated_dirs)

        executor = BlackAndBrownMod.Executor(dm.stream, *plugin_dirs, **plugin_args)

        dm.stream.write("Processing input files...")
        with dm.stream.DoneManager() as processing_dm:
            nonlocals = CommonEnvironment.Nonlocals(
                content_written=False,
            )

            for index, input_filename in enumerate(input_filenames):
                nonlocals.content_written = False

                processing_dm.stream.write(
                    "'{}' ({} of {})...".format(input_filename, index + 1, len(input_filenames)),
                )
                with processing_dm.stream.DoneManager(
                    suffix=lambda: "\n" if nonlocals.content_written else "",
                ) as this_dm:
                    formatted_content, has_changes = executor.Format(
                        input_filename,
                        black_line_length=black_line_length,
                        include_plugin_names=include_plugins,
                        exclude_plugin_names=exclude_plugins,
                        debug=debug,
                    )

                    if not has_changes:
                        this_dm.result = 1
                    elif overwrite:
                        with open(input_filename, "w") as f:
                            f.write(formatted_content)
                    else:
                        this_dm.stream.write(formatted_content)
                        nonlocals.content_written = True

        return dm.result


# ----------------------------------------------------------------------
@CommandLine.EntryPoint()
@CommandLine.Constraints(**_common_constraints)
def HasChanges(
    input,
    black_line_length=None,
    plugin_dir=None,
    plugin_arg=None,
    include_plugin=None,
    exclude_plugin=None,
    exclude_generated_dirs=False,
    output_stream=sys.stdout,
):
    """Returns 1 if one or more of the inputs would have changes after applying formatting"""

    inputs = input
    del input

    plugin_dirs = plugin_dir
    del plugin_dir

    plugin_args = plugin_arg
    del plugin_arg

    include_plugins = include_plugin or None
    del include_plugin

    exclude_plugins = exclude_plugin or None
    del exclude_plugin

    with StreamDecorator(output_stream).DoneManager(
        line_prefix="",
        prefix="\nResults: ",
        suffix="\n",
    ) as dm:
        input_filenames = []

        dm.stream.write("Resolving input...")
        with dm.stream.DoneManager(
            done_suffix=lambda: "{} found".format(inflect.no("input file", len(input_filenames))),
        ):
            input_filenames += _InputToFilenames(inputs, exclude_generated_dirs)

        executor = BlackAndBrownMod.Executor(dm.stream, *plugin_dirs, **plugin_args)

        invocation_kwargs = {
            "black_line_length": black_line_length,
            "include_plugin_names": include_plugins,
            "exclude_plugin_names": exclude_plugins,
        }

        changed = 0
        unchanged = 0

        dm.stream.write("Processing input files...")
        with dm.stream.DoneManager() as processing_dm:
            for index, input_filename in enumerate(input_filenames):
                processing_dm.stream.write(
                    "'{}' ({} of {})...".format(input_filename, index + 1, len(input_filenames)),
                )
                with processing_dm.stream.DoneManager() as this_dm:
                    if executor.HasChanges(input_filename, **invocation_kwargs):
                        this_dm.stream.write("***** Has Changes *****\n")

                        changed += 1
                        this_dm.result = 1
                    else:
                        unchanged += 1

        total = changed + unchanged

        # ----------------------------------------------------------------------
        def Percentage(value):
            if total == 0:
                return 0.00

            return (float(value) / total) * 100

        # ----------------------------------------------------------------------

        dm.stream.write(
            textwrap.dedent(
                """\

            Files with changes:             {changed} ({changed_percent:.02f}%)
            Files unchanged:                {unchanged} ({unchanged_percent:.02f}%)
            
            """
            ).format(
                changed=changed,
                unchanged=unchanged,
                changed_percent=Percentage(changed),
                unchanged_percent=Percentage(unchanged),
            )
        )

        return dm.result


# ----------------------------------------------------------------------
# ----------------------------------------------------------------------
# ----------------------------------------------------------------------
def _InputToFilenames(inputs, exclude_generated_dirs):
    traverse_exclude_dir_names = []

    if exclude_generated_dirs:
        traverse_exclude_dir_names.append(re.compile("generated.*", re.IGNORECASE))

    input_filenames = []

    for input in inputs:
        if os.path.isfile(input):
            input_filenames.append(input)
        elif os.path.isdir(input):
            input_filenames += FileSystem.WalkFiles(
                input,
                include_file_extensions=[".py"],
                traverse_exclude_dir_names=traverse_exclude_dir_names,
            )
        else:
            assert False, input

    return input_filenames


# ----------------------------------------------------------------------
# ----------------------------------------------------------------------
# ----------------------------------------------------------------------
if __name__ == "__main__":
    try:
        sys.exit(CommandLine.Main())
    except KeyboardInterrupt:
        pass
