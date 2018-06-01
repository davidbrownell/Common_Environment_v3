# ----------------------------------------------------------------------
# |  
# |  ConfigurationFileHelpers.py
# |  
# |  David Brownell <db@DavidBrownell.com>
# |      2018-05-31 21:22:18
# |  
# ----------------------------------------------------------------------
# |  
# |  Copyright David Brownell 2018.
# |  Distributed under the Boost Software License, Version 1.0.
# |  (See accompanying file LICENSE_1_0.txt or copy at http://www.boost.org/LICENSE_1_0.txt)
# |  
# ----------------------------------------------------------------------
"""Tools that help when processing configuration files"""

import os
import sys

from CommonEnvironment import RegularExpression
from CommonEnvironment.Shell.All import CurrentShell

# ----------------------------------------------------------------------
_script_fullpath = os.path.abspath(__file__) if "python" in sys.executable.lower() else sys.executable
_script_dir, _script_name = os.path.split(_script_fullpath)
# ----------------------------------------------------------------------

# ----------------------------------------------------------------------
def ShouldProcessConfigurationInfo( config_info,
                                    compiler,
                                    is_debug,
                                  ):
    """
    Returns True if the configuration info should be processed by looking at requirements
    defined in config_info and information about the current environment.
    """

    for attribute_name, required_value in [ ( "shell_name", CurrentShell.Name ),
                                            ( "shell_category_name", CurrentShell.CategoryName ),
                                            ( "compiler_name", compiler.Name ),
                                            ( "compiler_version", getattr(compiler, "Version", None) ),
                                            ( "configuration", "debug" if is_debug else "release" ),
                                          ]:
        value = getattr(config_info, attribute_name, None)
        if value is not None and value != required_value:
            return False

    return True

# ----------------------------------------------------------------------
def ProcessConfigurationFiles( configuration_filename,                      # Name of configuration file
                               load_configuration_func,                     # def Func(configuration_filename) -> [ source, ... ]
                               apply_source_func,                           # def Func(input_filename, source)
                               input_filenames,
                             ):
    """
    Searches the current folder and all parents of each input filename looking for files named <configuration_filename>.
    The configuration info and the way in which it is loaded is handled by the provided callback functions.

    If source contains the attribute 'name', it will be treated as a wildcard expression to match against the current
    input file. When present, apply_source_func will only be invoked for files that match this expression.
    """

    for input_filename in input_filenames:
        # Get all of the external configuration files that exist within the parent
        # directories of this file.
        configuration_filenames = []

        dirname = os.path.dirname(os.path.abspath(input_filename))
        while True:
            potential_filename = os.path.join(dirname, configuration_filename)
            if os.path.isfile(potential_filename):
                configuration_filenames.append(potential_filename)

            potential_dirname = os.path.dirname(dirname)
            if potential_dirname == dirname:
                break

            dirname = potential_dirname

        # Process the configuration files
        for configuration_filename in configuration_filenames:
            for source in load_configuration_func(configuration_filename):
                name = getattr(source, "name", None)
                if name is not None and not RegularExpression.WildcardSearchToRegularExpression(name.replace('/', os.path.sep)).match(input_filename):
                    continue

                apply_source_func(input_filename, source)
