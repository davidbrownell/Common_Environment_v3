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
import sys
import textwrap
import traceback

import CommonEnvironment
from CommonEnvironment import CommandLine
from CommonEnvironment import StringHelpers

from CommonEnvironment.BlackAndBrown import Executor

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

    executor = Executor(output_stream)

    if is_check:
        return 1 if executor.HasChanges(input_filename) else -1

    original_content = open(input_filename).read()

    try:
        formatted_content, has_changes = executor.Format(input_filename)
    except:
        if not is_diff:
            raise

        # This is a bit strange, but if the caller is expecting a diff we
        # need to display this exception as a diff.
        exception_content = traceback.format_exc()

        formatted_content = textwrap.dedent(
            """\
            ********************************************************************************
            ********************************************************************************
            ********************************************************************************
        
                Exception generated in BlackProxy
        
                    {}
        
            ********************************************************************************
            ********************************************************************************
            ********************************************************************************
            {}
            """,
        ).format(StringHelpers.LeftJustify(exception_content, 8), original_content)

        has_changes = True

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
    elif not has_changes:
        return 0

    sys.stdout.write(formatted_content)
    return 0


# ----------------------------------------------------------------------
# ----------------------------------------------------------------------
# ----------------------------------------------------------------------
if __name__ == "__main__":
    try:
        sys.exit(CommandLine.Main())
    except KeyboardInterrupt:
        pass
