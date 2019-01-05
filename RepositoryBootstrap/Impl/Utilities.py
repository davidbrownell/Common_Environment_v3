# ----------------------------------------------------------------------
# |  
# |  Utilities.py
# |  
# |  David Brownell <db@DavidBrownell.com>
# |      2018-05-02 15:57:42
# |  
# ----------------------------------------------------------------------
# |  
# |  Copyright David Brownell 2018-19.
# |  Distributed under the Boost Software License, Version 1.0.
# |  (See accompanying file LICENSE_1_0.txt or copy at http://www.boost.org/LICENSE_1_0.txt)
# |  
# ----------------------------------------------------------------------
"""Utilities used by multiple files within this module."""

import hashlib
import importlib
import os
import re
import sys

from contextlib import contextmanager

import six

from RepositoryBootstrap import Constants
from RepositoryBootstrap.Impl import CommonEnvironmentImports

# ----------------------------------------------------------------------
_script_fullpath = CommonEnvironmentImports.CommonEnvironment.ThisFullpath()
_script_dir, _script_name = os.path.split(_script_fullpath)
# ----------------------------------------------------------------------

# ----------------------------------------------------------------------
def GenerateCommands( functor,              # def Func() -> []
                      is_debug,
                    ):
    """
    Generates shell-specific commands as returned by the provided functor.

    Returns:
        (result, generated_commands)
    """

    assert functor
    
    commands = []

    try:
        result = functor()

        if isinstance(result, int):
            commands = []
        elif isinstance(result, tuple):
            result, commands = result
        else:
            commands = result
            result = 0

    except Exception as ex:
        if is_debug:
            import traceback
            
            error = traceback.format_exc()
        else:
            error = str(ex)

        commands = [ CommonEnvironmentImports.CurrentShell.Commands.Message("\n\nERROR: {}".format(CommonEnvironmentImports.StringHelpers.LeftJustify(error, len("ERROR: ")))),
                     CommonEnvironmentImports.CurrentShell.Commands.Exit(return_code=-1),
                   ]

        result = -1

    if is_debug and commands:
        commands = [ CommonEnvironmentImports.CurrentShell.Commands.Message("{}\n".format(CommonEnvironmentImports.StringHelpers.Prepend( "Debug: ", 
                                                                                                                                          CommonEnvironmentImports.CurrentShell.GenerateCommands(commands),
                                                                                                                                          skip_first_line=False,
                                                                                                                                        ))),
                   ] + commands

    return result, commands

# ----------------------------------------------------------------------
def CalculateFingerprint(repo_dirs, relative_root=None):
    """
    Returns a value that can be used to determine if any configuration info
    has changed for a repo and its dependencies.
    """

    results = {}

    for repo_dir in repo_dirs:
        md5 = hashlib.md5()

        filename = os.path.join(repo_dir, Constants.SETUP_ENVIRONMENT_CUSTOMIZATION_FILENAME)
        if not os.path.isfile(filename):
            continue

        with open(filename, 'rb') as f:
            # Skip the file header, as it has no impact on the file's actual contents.
            in_file_header = True

            for line in f:
                if in_file_header and line.lstrip().startswith(b'#'):
                    continue

                in_file_header = False
                md5.update(line)

        if relative_root:
            repo_dir = CommonEnvironmentImports.FileSystem.GetRelativePath(relative_root, repo_dir)

        results[repo_dir] = md5.hexdigest()

    return results

# ----------------------------------------------------------------------
@contextmanager
def CustomMethodManager(customization_filename, method_name):
    """Attempts to load a customization filename and extract the given method."""

    if not os.path.isfile(customization_filename):
        yield None
        return

    customization_path, customization_name = os.path.split(customization_filename)
    customization_name = os.path.splitext(customization_name)[0]

    sys.path.insert(0, customization_path)
    with CommonEnvironmentImports.CallOnExit(lambda: sys.path.pop(0)):
        mod = importlib.import_module(customization_name)
        with CommonEnvironmentImports.CallOnExit(lambda: sys.modules.pop(customization_name)):
            yield getattr(mod, method_name, None)
