# ----------------------------------------------------------------------
# |  
# |  DynamicPluginArchitecture.py
# |  
# |  David Brownell <db@DavidBrownell.com>
# |      2018-05-21 22:14:27
# |  
# ----------------------------------------------------------------------
# |  
# |  Copyright David Brownell 2018.
# |  Distributed under the Boost Software License, Version 1.0.
# |  (See accompanying file LICENSE_1_0.txt or copy at http://www.boost.org/LICENSE_1_0.txt)
# |  
# ----------------------------------------------------------------------
"""
Contains methods that help when creating dynamic plugin architectures across
repository boundaries.

Repositories often times have to modify how scripts in other repositories operate
in a way that doesn't create a hard dependency from the base repository to the 
extension (or plugin) repository.

For example, Common_Environment defines a script called Tester, where the code is
able to compile tests written in different languages through the use of language-
specific plugins in the form of Compilers. However, these compilers are defined
in repositories outside of Common_Environment.

To address these dependencies, we create a layer of indirection through this module;
the script that is defined in the base repository will define an environment variable
that will be updated by other repositories that provide plugins for that script. When
the script is launched, it will query that environment variable and instantiate all
the plugins that have been associated with it. Care is taken to ensure that the
environment variable can be associated with a large number of plugins.
"""

import importlib
import os
import sys

from RepositoryBootstrap import Constants
from RepositoryBootstrap.Impl import CommonEnvironmentImports

# ----------------------------------------------------------------------
_script_fullpath = CommonEnvironmentImports.CommonEnvironment.ThisFullpath()
_script_dir, _script_name = os.path.split(_script_fullpath)
# ----------------------------------------------------------------------

# ----------------------------------------------------------------------
def EnumeratePlugins(environment_beacon_name):
    """Enumerates all plugins registered with the given name."""
    filename = os.getenv(environment_beacon_name)
    if not filename or not os.path.isfile(filename):
        return 

    lines = [ line.strip() for line in open(filename).readlines() ]

    for module_name in [ line for line in lines if line ]:
        yield LoadModule(module_name)

# ----------------------------------------------------------------------
def LoadModule(filename):
    """Dynamically loads a python module"""

    assert os.path.isfile(filename), filename

    filename = os.path.realpath(filename)

    dirname, basename = os.path.split(filename)
    name = os.path.splitext(basename)[0]

    sys.path.insert(0, dirname)
    with CommonEnvironmentImports.CallOnExit(lambda: sys.path.pop(0)):
        return importlib.import_module(name)

# ----------------------------------------------------------------------
def CreateRegistrationStatements( environment_beacon_name,
                                  directory,
                                  is_valid_func,        # def Func(fullpath, name, ext) -> Bool
                                ):
    """Adds all valid files to a beacon in a given directory"""

    filenames = []

    for item in os.listdir(directory):
        fullpath = os.path.join(directory, item)
        if not os.path.isfile(fullpath):
            continue

        name, ext = os.path.splitext(item)

        if is_valid_func(fullpath, name, ext):
            filenames.append(fullpath)

    if not filenames:
        return []

    commands = []
    new_filenames = set()

    source_filename = os.getenv(environment_beacon_name)
    if not source_filename:
        source_filename = CommonEnvironmentImports.CurrentShell.CreateTempFilename(".DPA{}".format(Constants.TEMPORARY_FILE_EXTENSION))

        commands.append(CommonEnvironmentImports.CurrentShell.Commands.Set(environment_beacon_name, source_filename, update_memory=True))

    elif os.path.isfile(source_filename):
        for line in [ line.strip() for line in open(source_filename).readlines() if line.strip() ]:
            if os.path.isfile(line):
                new_filenames.add(line)

    for filename in filenames:
        if filename not in new_filenames:
            new_filenames.add(filename)

    with open(source_filename, 'w') as f:
        f.write("{}\n".format('\n'.join(sorted(new_filenames))))

    return commands
