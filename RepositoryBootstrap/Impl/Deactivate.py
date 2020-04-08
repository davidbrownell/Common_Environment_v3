# ----------------------------------------------------------------------
# |
# |  Deactivate.py
# |
# |  David Brownell <db@DavidBrownell.com>
# |      2020-04-08 12:57:36
# |
# ----------------------------------------------------------------------
# |
# |  Copyright David Brownell 2020
# |  Distributed under the Boost Software License, Version 1.0. See
# |  accompanying file LICENSE_1_0.txt or copy at
# |  http://www.boost.org/LICENSE_1_0.txt.
# |
# ----------------------------------------------------------------------
"""Deactivates a previously activated environment"""

import os
import sys
import textwrap

import six

from RepositoryBootstrap import Constants
from RepositoryBootstrap import EnvironmentDiffs

from RepositoryBootstrap.Impl import CommonEnvironmentImports
from RepositoryBootstrap.Impl import Utilities

# ----------------------------------------------------------------------
_script_fullpath                            = CommonEnvironmentImports.CommonEnvironment.ThisFullpath()
_script_dir, _script_name                   = os.path.split(_script_fullpath)
# ----------------------------------------------------------------------

# ----------------------------------------------------------------------
@CommonEnvironmentImports.CommandLine.EntryPoint(
    output_filename_or_stdout=CommonEnvironmentImports.CommandLine.EntryPoint.Parameter("Created file containing the generated content or stdout of the value is 'stdout'"),
)
@CommonEnvironmentImports.CommandLine.Constraints(
    output_filename_or_stdout=CommonEnvironmentImports.CommandLine.StringTypeInfo(),
    output_stream=None,
)
def Deactivate(
    output_filename_or_stdout,
    debug=False,
    output_stream=sys.stdout,
):
    """Deactivates a repository"""

    # ----------------------------------------------------------------------
    def Execute():
        commands = []

        for k in six.iterkeys(os.environ):
            if k.startswith("_DEACTIVATE"):
                continue

            commands.append(CommonEnvironmentImports.CurrentShell.Commands.Set(k, None))

        original_environment = EnvironmentDiffs.GetOriginalEnvironment()

        for k, v in six.iteritems(original_environment):
            commands.append(CommonEnvironmentImports.CurrentShell.Commands.Set(k, v))

        if CommonEnvironmentImports.CurrentShell.CategoryName == "Linux":
            commands += [
                CommonEnvironmentImports.CurrentShell.Commands.Message(
                    textwrap.dedent(
                        """\

                        I don't know of a good way to restore the original prompt given that the prompt isn't stored as an environment variable.
                        Hopefully, this scenario is uncommon enough that the wonky prompt isn't a significant issue.
                        """,
                    ),
                ),
                CommonEnvironmentImports.CurrentShell.Commands.CommandPrompt("DEACTIVATED"),
            ]

        return commands

    # ----------------------------------------------------------------------

    results, commands = Utilities.GenerateCommands(Execute, debug)

    if output_filename_or_stdout == "stdout":
        output_stream = sys.stdout
        close_stream_func = lambda: None
    else:
        output_stream = open(output_filename_or_stdout, 'w')
        close_stream_func = output_stream.close

    with CommonEnvironmentImports.CallOnExit(close_stream_func):
        output_stream.write(CommonEnvironmentImports.CurrentShell.GenerateCommands(commands))

    return results


# ----------------------------------------------------------------------
# ----------------------------------------------------------------------
# ----------------------------------------------------------------------
if __name__ == "__main__":
    try:
        sys.exit(CommonEnvironmentImports.CommandLine.Main())
    except KeyboardInterrupt:
        pass
