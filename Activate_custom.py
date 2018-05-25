# ----------------------------------------------------------------------
# |  
# |  Activate_custom.py
# |  
# |  David Brownell <db@DavidBrownell.com>
# |      2018-05-07 08:59:57
# |  
# ----------------------------------------------------------------------
# |  
# |  Copyright David Brownell 2018.
# |  Distributed under the Boost Software License, Version 1.0.
# |  (See accompanying file LICENSE_1_0.txt or copy at http://www.boost.org/LICENSE_1_0.txt)
# |  
# ----------------------------------------------------------------------
"""Functionality to further enhance Common_Enviromnet activation"""

import os
import sys

from collections import OrderedDict

import six

# ----------------------------------------------------------------------
_script_fullpath = os.path.abspath(__file__) if "python" in sys.executable.lower() else sys.executable
_script_dir, _script_name = os.path.split(_script_fullpath)
# ----------------------------------------------------------------------

sys.path.insert(0, os.getenv("DEVELOPMENT_ENVIRONMENT_FUNDAMENTAL"))
from RepositoryBootstrap.Impl import CommonEnvironmentImports
from RepositoryBootstrap.Impl import DynamicPluginArchitecture
del sys.path[0]

# ----------------------------------------------------------------------
def GetCustomActions( output_stream,
                      shell,
                      configuration,
                      version_specs,
                      generated_dir,
                      debug,
                      verbose,
                      fast,
                      repositories,
                      is_tool_repo,
                    ):
    """
    Returns an action or list of actions that should be invoked as part of the activaation process.

    Actions are generic command line statements defined in 
    <Common_Environment>/Libraries/Python/CommonEnvironment/v1.0/CommonEnvironment/Shell/Commands/__init__.py
    that are converted into statements appropriate for the current scripting language (in most
    cases, this is Bash on Linux systems and Batch or Powershell on Windows systems.
    """

    actions = []

    Commands = CommonEnvironmentImports.CurrentShell.Commands

    if fast:
        actions.append(Commands.Message("** FAST: Dynamic tester information has not been activated. ({}) **".format(_script_fullpath)))
    else:
        # Reset any existing values
        os.environ["DEVELOPMENT_ENVIRONMENT_COMPILERS"] = ''
        os.environ["DEVELOPMENT_ENVIRONMENT_TEST_PARSER"] = ''
        os.environ["DEVELOPMENT_ENVIRONMENT_CODE_COVERAGE_EXTRACTORS"] = ''
        os.environ["DEVELOPMENT_ENVIRONMENT_CODE_COVERAGE_VALIDATORS"] = ''

        actions += DynamicPluginArchitecture.CreateRegistrationStatements( "DEVELOPMENT_ENVIRONMENT_COMPILERS",
                                                                           os.path.join(_script_dir, "Scripts", "Compilers"),
                                                                           lambda fullpath, name, ext: ext == ".py" and (name.endswith("Compiler") or name.endswith("CodeGenerator") or name.endswith("Verifier")),
                                                                         )

        actions += DynamicPluginArchitecture.CreateRegistrationStatements( "DEVELOPMENT_ENVIRONMENT_TEST_PARSERS",
                                                                           os.path.join(_script_dir, "Scripts", "TestParsers"),
                                                                           lambda fullpath, name, ext: ext == ".py" and name.endswith("TestParser"),
                                                                         )
        
        # TODO: actions += DynamicPluginArchitecture.CreateRegistrationStatements( "DEVELOPMENT_ENVIRONMENT_CODE_COVERAGE_EXTRACTORS",
        # TODO:                                                                    os.path.join(_script_dir, "Scripts", "CodeCoverageExtractors"),
        # TODO:                                                                    lambda fullpath, name, ext: ext == ".py" and name.endswith("CodeCoverageExtractor"),
        # TODO:                                                                  )
        # TODO: 
        actions += DynamicPluginArchitecture.CreateRegistrationStatements( "DEVELOPMENT_ENVIRONMENT_CODE_COVERAGE_VALIDATORS",
                                                                           os.path.join(_script_dir, "Scripts", "CodeCoverageValidators"),
                                                                           lambda fullpath, name, ext: ext == ".py" and name.endswith("CodeCoverageValidator"),
                                                                         )

    actions.append(Commands.Augment( "DEVELOPMENT_ENVIRONMENT_TESTER_CONFIGURATIONS",
                                     [ "python-compiler-PyLint",
                                       "python-test_parser-Python",
                                       "python-code_coverage_extractor-Python",
                                     ],
                                     update_memory=True,
                                   ))

    return actions

# ----------------------------------------------------------------------
def GetCustomScriptExtractors(shell):
    """Returns script parsers used during activation."""

    # ----------------------------------------------------------------------
    def PythonWrapper(script_filename):
        if os.path.basename(script_filename) == "__init__.py":
            return

        return [ shell.Commands.EchoOff(),
                 shell.Commands.Execute('python "{}" {}'.format( script_filename,
                                                                 shell.AllArgumentsScriptVariable,
                                                               )),
               ]

    # ----------------------------------------------------------------------
    def PythonDocs(script_filename):
        co = compile(open(script_filename, 'rb').read(), script_filename, "exec")

        if co and co.co_consts and isinstance(co.co_consts[0], six.string_types) and co.co_consts[0][0] != '_':
            return CommonEnvironmentImports.StringHelpers.Wrap(co.co_consts[0], 100)

    # ----------------------------------------------------------------------
    def PowershellScriptWrapper(script_filename):
        return shell.Commands.Execute('powershell -executionpolicy unrestricted "{}" {}'.format(script_filename, shell.AllArgumentsScriptVariable))

    # ----------------------------------------------------------------------
    def EnvironmentScriptWrapper(script_filename):
        return shell.Commands.Execute('"{}" {}'.format(script_filename, shell.AllArgumentsScriptVariable))

    # ----------------------------------------------------------------------

    return OrderedDict([ ( ".py", ( PythonWrapper, PythonDocs ) ),
                         ( ".ps1", PowershellScriptWrapper ),
                         ( shell.ScriptExtension, EnvironmentScriptWrapper ),
                       ])

