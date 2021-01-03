# ----------------------------------------------------------------------
# |
# |  EnvironmentDiffs.py
# |
# |  David Brownell <db@DavidBrownell.com>
# |      2018-06-02 22:19:34
# |
# ----------------------------------------------------------------------
# |
# |  Copyright David Brownell 2018-21.
# |  Distributed under the Boost Software License, Version 1.0.
# |  (See accompanying file LICENSE_1_0.txt or copy at http://www.boost.org/LICENSE_1_0.txt)
# |
# ----------------------------------------------------------------------
"""Displays changes made by an environment during activation."""

import json
import os
import sys
import textwrap

import six

import CommonEnvironment
from CommonEnvironment import CommandLine
from CommonEnvironment.Shell.All import CurrentShell

from RepositoryBootstrap import Constants

# ----------------------------------------------------------------------
_script_fullpath = CommonEnvironment.ThisFullpath()
_script_dir, _script_name = os.path.split(_script_fullpath)
# ----------------------------------------------------------------------

# ----------------------------------------------------------------------
@CommandLine.EntryPoint
@CommandLine.Constraints( output_stream=None,
                        )
def Before( decorate=False,
            output_stream=sys.stdout,
          ):
    _Display(GetOriginalEnvironment(), output_stream, decorate)
    return 0

# ----------------------------------------------------------------------
@CommandLine.EntryPoint
@CommandLine.Constraints( output_stream=None,
                        )
def After( decorate=False,
           output_stream=sys.stdout,
         ):
    original_env = GetOriginalEnvironment()

    # Compare to the current environment
    this_env = dict(os.environ)

    differences = {}

    for k, v in six.iteritems(this_env):
        if ( k not in original_env or
             original_env[k] != v
           ):
            differences[k] = v

    _Display(differences, output_stream, decorate)
    return 0

# ----------------------------------------------------------------------
# ----------------------------------------------------------------------
# ----------------------------------------------------------------------
def GetOriginalEnvironment():
    # Get the original environment
    generated_dir = os.getenv(Constants.DE_REPO_GENERATED_NAME)
    assert os.path.isdir(generated_dir), generated_dir

    original_environment_filename = os.path.join(generated_dir, Constants.GENERATED_ACTIVATION_ORIGINAL_ENVIRONMENT_FILENAME)
    assert os.path.isfile(original_environment_filename), original_environment_filename

    with open(original_environment_filename) as f:
        return json.load(f)

# ----------------------------------------------------------------------
# ----------------------------------------------------------------------
# ----------------------------------------------------------------------
def _Display(content, output_stream, decorate):
    if not isinstance(content, six.string_types):
        content = json.dumps(content)

    if decorate:
        output_stream.write(textwrap.dedent(
            """\
            //--//--//--//--//--//--//--//--//--//--//--//--//--//--//--//
            {}
            //--//--//--//--//--//--//--//--//--//--//--//--//--//--//--//
            """).format(content))
    else:
        output_stream.write(content)

# ----------------------------------------------------------------------
# ----------------------------------------------------------------------
# ----------------------------------------------------------------------
if __name__ == "__main__":
    try: sys.exit(CommandLine.Main())
    except KeyboardInterrupt: pass
