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
"""\
Updates python source code with the PythonFormatter while presenting an 
interface similar to the Black formatter.

This proxy is useful for tools that are configured to invoke Black (see 
the list below) by presenting a consistent interface. This python script
resides here (rather than in <root>/Scripts) because those tools often
expect to invoke Black as a python module rather than as a script.

The following are instructions to configure different editors to use
this proxy:

VSCODE
------
Update `settings.json` with the following information

{
    "python.formatting.provider": "black",
    "python.formatting.blackPath": "CommonEnvironment.PythonModuleProxies.BlackProxy",
    "editor.formatOnSaveTimeout": 10000
}


"""

import difflib
import os
import sys
import textwrap
import traceback

import CommonEnvironment
from CommonEnvironment import CommandLine
from CommonEnvironment import Process
from CommonEnvironment.Shell.All import CurrentShell
from CommonEnvironment import StringHelpers

# ----------------------------------------------------------------------
_script_fullpath                            = CommonEnvironment.ThisFullpath()
_script_dir, _script_name                   = os.path.split(_script_fullpath)
# ----------------------------------------------------------------------

# ----------------------------------------------------------------------
@CommandLine.EntryPoint(
    arg=CommandLine.EntryPoint.Parameter("Argument passed to Black"),
)
@CommandLine.Constraints(
    arg=CommandLine.StringTypeInfo(
        arity="+",
    ),
    output_stream=None,
)
def Convert(
    arg,
    output_stream=sys.stdout,
):
    """Converts the provided input"""

    args = arg
    del arg

    input_filename = None
    is_diff = False
    is_check = False

    for arg in args:
        if arg == "--diff":
            is_diff = True
        elif arg == "--check":
            is_check = True
        elif arg in ["--quiet"]:
            # Ignore these
            pass
        elif input_filename is None and os.path.isfile(arg):
            input_filename = arg
        else:
            raise Exception("The argument '{}' is not supported".format(arg))

    if input_filename is None:
        raise Exception("Please provide a filename on the command line")

    original_content = open(input_filename).read()

    if is_check:
        command_line_template = '"{script}" HasChanges "{filename}"'
    else:
        command_line_template = '"{script}" Format "{filename}" /quiet'

    result, formatted_content = Process.Execute(
        command_line_template.format(
            script=CurrentShell.CreateScriptName("Formatter"),
            filename=input_filename,
        ),
    )

    if is_check:
        return 1 if result == 1 else -1

    if result != 0:
        if not is_diff:
            output_stream.write(formatted_content)
            return -1

        formatted_content = textwrap.dedent(
            """\
            ********************************************************************************
            ********************************************************************************
            ********************************************************************************

            {}

            ********************************************************************************
            ********************************************************************************
            ********************************************************************************
            {}
            """,
        ).format(formatted_content, original_content)

    if formatted_content:
        if is_diff:
            # ----------------------------------------------------------------------
            def StringToArray(content):
                return ["{}\n".format(line) for line in content.split("\n")]

            # ----------------------------------------------------------------------

            diff = difflib.unified_diff(
                StringToArray(original_content),
                StringToArray(formatted_content),
            )

            formatted_content = "".join(diff)

        output_stream.write(formatted_content)

    return 0


# ----------------------------------------------------------------------
# ----------------------------------------------------------------------
# ----------------------------------------------------------------------
if __name__ == "__main__":
    try:
        sys.exit(CommandLine.Main())
    except KeyboardInterrupt:
        pass
