# ----------------------------------------------------------------------
# |
# |  BlackProxy.py
# |
# |  David Brownell <db@DavidBrownell.com>
# |      2018-12-14 21:14:40
# |
# ----------------------------------------------------------------------
# |
# |  Copyright David Brownell 2018
# |  Distributed under the Boost Software License, Version 1.0. See
# |  accompanying file LICENSE_1_0.txt or copy at
# |  http://www.boost.org/LICENSE_1_0.txt.
# |
# ----------------------------------------------------------------------
"""Updates python source code with Black and applies additional formatting (Brown)"""

import difflib
import os
import shutil
import sys

import CommonEnvironment
from CommonEnvironment.CallOnExit import CallOnExit
from CommonEnvironment import CommandLine
from CommonEnvironment import FileSystem
from CommonEnvironment import Process
from CommonEnvironment.Shell.All import CurrentShell

from CommonEnvironment.BlackAndBrown import Executor

# ----------------------------------------------------------------------
_script_fullpath = CommonEnvironment.ThisFullpath()
_script_dir, _script_name = os.path.split(_script_fullpath)
# ----------------------------------------------------------------------


@CommandLine.EntryPoint(
    # BugBug
)
@CommandLine.Constraints(arg=CommandLine.StringTypeInfo(arity="+"), output_stream=None)
def Convert(
    arg,
    output_stream=sys.stdout,
):
    """Converts the provided input"""

    if True: # BugBug try:
        # BugBug: Use argparse to match Black's Interface
        args = arg
        del arg

        input_filename = args.pop()
        args = [arg for arg in args if arg not in ["--diff", "--quiet"]]

        temp_filename = CurrentShell.CreateTempFilename()
        with CallOnExit(lambda: FileSystem.RemoveFile(temp_filename)):
            output = Executor(
                sys.stdout, 
                AlignAssignments=[[45, 57, 77], 7], 
                AlignTrailingComments=[[45, 57, 77]], 
                SplitLongFunctions=[78],
            ).Format(
                input_filename, black_line_length=180
            )

            with open(temp_filename, "w") as f:
                f.write(output)

            # BugBug
            # BugBug # BugBug: Use black module
            # BugBug # Invoke Black and output to a temporary file
            # BugBug result, output = Process.Execute(
            # BugBug     'python -m black {} --quiet "{}"'.format(
            # BugBug         " ".join(args), input_filename
            # BugBug     )
            # BugBug )
            # BugBug if result != 0:
            # BugBug     output_stream.write(output)
            # BugBug     return result
            # BugBug

            # Create a diff of the input and generated file
            diff = difflib.unified_diff(open(input_filename).readlines(), ["{}\n".format(line) for line in output.split("\n")])

            diff = "".join(diff)

            with open(r"C:\Temp\BlackAndBrown.diff", "w") as f:
                f.write(diff)

            output_stream.write(diff)

            return 0
    # BugBug except:
    # BugBug     import traceback
    # BugBug 
    # BugBug     with open(r"C:\Temp\BlackAndBrown.txt", "w") as f:
    # BugBug         f.write(traceback.format_exc())
    # BugBug         return -1


# ----------------------------------------------------------------------
# ----------------------------------------------------------------------
# ----------------------------------------------------------------------
if __name__ == "__main__":
    try:
        sys.exit(CommandLine.Main())
    except KeyboardInterrupt:
        pass
