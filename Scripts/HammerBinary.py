# ----------------------------------------------------------------------
# |
# |  HammerBinary.py
# |
# |  David Brownell <db@DavidBrownell.com>
# |      2020-07-17 08:42:35
# |
# ----------------------------------------------------------------------
# |
# |  Copyright David Brownell 2020
# |  Distributed under the Boost Software License, Version 1.0. See
# |  accompanying file LICENSE_1_0.txt or copy at
# |  http://www.boost.org/LICENSE_1_0.txt.
# |
# ----------------------------------------------------------------------
"""Repeatedly executes a binary (often unit tests) in attempt to reproduce non-deterministic errors"""

import os
import sys

import CommonEnvironment
from CommonEnvironment import CommandLine
from CommonEnvironment import Process
from CommonEnvironment.StreamDecorator import StreamDecorator
from CommonEnvironment import TaskPool

# ----------------------------------------------------------------------
_script_fullpath                            = CommonEnvironment.ThisFullpath()
_script_dir, _script_name                   = os.path.split(_script_fullpath)
# ----------------------------------------------------------------------

@CommandLine.EntryPoint(
    command_line=CommandLine.EntryPoint.Parameter("Command line to execute"),
    iterations=CommandLine.EntryPoint.Parameter("Number of times to execute the command line"),
    repeat=CommandLine.EntryPoint.Parameter("Repeat the number of iterations; this can be useful to baseline expectations around how often a problem generally appears"),
)
@CommandLine.Constraints(
    command_line=CommandLine.StringTypeInfo(),
    iterations=CommandLine.IntTypeInfo(
        min=1,
    ),
    output_stream=None,
)
def Execute(
    command_line,
    iterations,
    repeat=False,
    output_stream=sys.stdout,
):
    with StreamDecorator(output_stream).DoneManager(
        line_prefix="",
        prefix="\nResults: ",
        suffix="\n",
    ) as dm:
        has_error = None # Set below

        # ----------------------------------------------------------------------
        def Execute(task_index):
            nonlocal has_error

            if has_error:
                return 0

            result, output = Process.Execute(command_line)
            if result != 0:
                has_error = True
                return result, output

            return result

        # ----------------------------------------------------------------------

        tasks = [TaskPool.Task(str(index + 1), Execute) for index in range(iterations)]

        repeat_index = 1
        while True:
            has_error = False

            result = TaskPool.Execute(
                tasks,
                dm.stream,
                progress_bar=True,
                display_exception_callstack=False,
                num_concurrent_tasks=1,
            )

            if result != 0:
                dm.result = result

            dm.stream.write("{}) {}\n".format(repeat_index, result))
            repeat_index += 1

            if not repeat:
                break

        return dm.result

# ----------------------------------------------------------------------
# ----------------------------------------------------------------------
# ----------------------------------------------------------------------
if __name__ == "__main__":
    try:
        sys.exit(
            CommandLine.Main()
        )
    except KeyboardInterrupt:
        pass
