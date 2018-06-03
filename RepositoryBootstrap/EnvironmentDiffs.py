# ----------------------------------------------------------------------
# |  
# |  EnvironmentDiffs.py
# |  
# |  David Brownell <db@DavidBrownell.com>
# |      2018-06-02 22:19:34
# |  
# ----------------------------------------------------------------------
# |  
# |  Copyright David Brownell 2018.
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

from CommonEnvironment import CommandLine
from CommonEnvironment.Shell.All import CurrentShell

from RepositoryBootstrap import Constants

# ----------------------------------------------------------------------
_script_fullpath = os.path.abspath(__file__) if "python" in sys.executable.lower() else sys.executable
_script_dir, _script_name = os.path.split(_script_fullpath)
# ----------------------------------------------------------------------

# ----------------------------------------------------------------------
@CommandLine.EntryPoint
@CommandLine.Constraints( output_stream=None,
                        )
def EntryPoint( decorate=False,
                output_stream=sys.stdout,
              ):
    # Get the original environment
    generated_dir = os.getenv(Constants.DE_REPO_GENERATED_NAME)
    assert os.path.isdir(generated_dir), generated_dir

    original_environment_filename = os.path.join(generated_dir, Constants.GENERATED_ACTIVATION_ORIGINAL_ENVIRONMENT_FILENAME)
    assert os.path.isfile(original_environment_filename), original_environment_filename

    with open(original_environment_filename) as f:
        original_env = json.load(f)

    # Compare to the current environment
    this_env = dict(os.environ)

    differences = {}

    for k, v in six.iteritems(this_env):
        if ( k not in original_env or
             original_env[k] != v
           ):
            differences[k] = v

    differences = json.dumps(differences)

    if decorate:
        output_stream.write(textwrap.dedent(
            """\
            //--//--//--//--//--//--//--//--//--//--//--//--//--//--//--//
            {}
            //--//--//--//--//--//--//--//--//--//--//--//--//--//--//--//
            """).format(differences))
    else:
        output_stream.write(differences)

    return 0

# ----------------------------------------------------------------------
# ----------------------------------------------------------------------
# ----------------------------------------------------------------------
if __name__ == "__main__":
    try: sys.exit(CommandLine.Main())
    except KeyboardInterrupt: pass