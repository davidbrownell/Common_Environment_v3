# ----------------------------------------------------------------------
# |  
# |  Activate_custom.py
# |  
# |  David Brownell <db@DavidBrownell.com>
# |      2018-05-07 08:59:57
# |  
# ----------------------------------------------------------------------
# |  
# |  Copyright David Brownell 2018-19.
# |  Distributed under the Boost Software License, Version 1.0.
# |  (See accompanying file LICENSE_1_0.txt or copy at http://www.boost.org/LICENSE_1_0.txt)
# |  
# ----------------------------------------------------------------------
"""Functionality to further enhance Common_Environment activation"""

import os
import sys

from collections import OrderedDict

import six

import CommonEnvironment

# ----------------------------------------------------------------------
_script_fullpath = CommonEnvironment.ThisFullpath()
_script_dir, _script_name = os.path.split(_script_fullpath)
# ----------------------------------------------------------------------

sys.path.insert(0, os.getenv("DEVELOPMENT_ENVIRONMENT_FUNDAMENTAL"))
from RepositoryBootstrap.SetupAndActivate import DynamicPluginArchitecture

# Note that other repositories can import CommonEnvironment directly.
from RepositoryBootstrap.Impl import CommonEnvironmentImports

CurrentShell                                = CommonEnvironmentImports.CurrentShell
StringHelpers                               = CommonEnvironmentImports.StringHelpers

del sys.path[0]

# ----------------------------------------------------------------------
def GetCustomActions( output_stream,
                      configuration,
                      version_specs,
                      generated_dir,
                      debug,
                      verbose,
                      fast,
                      repositories,
                      is_mixin_repo,
                    ):
    """
    Returns an action or list of actions that should be invoked as part of the activation process.

    Actions are generic command line statements defined in 
    <Common_Environment>/Libraries/Python/CommonEnvironment/v1.0/CommonEnvironment/Shell/Commands/__init__.py
    that are converted into statements appropriate for the current scripting language (in most
    cases, this is Bash on Linux systems and Batch or Powershell on Windows systems.
    """

    actions = []

    Commands = CurrentShell.Commands

    if fast:
        actions.append(Commands.Message("** FAST: Dynamic tester information has not been activated. ({}) **".format(_script_fullpath)))
    else:
        # Reset any existing values
        os.environ["DEVELOPMENT_ENVIRONMENT_COMPILERS"] = ''
        os.environ["DEVELOPMENT_ENVIRONMENT_TEST_EXECUTORS"] = ''
        os.environ["DEVELOPMENT_ENVIRONMENT_TEST_PARSERS"] = ''
        os.environ["DEVELOPMENT_ENVIRONMENT_CODE_COVERAGE_VALIDATORS"] = ''
        os.environ["DEVELOPMENT_ENVIRONMENT_TESTER_CONFIGURATIONS"] = ''
        os.environ["DEVELOPMENT_ENVIRONMENT_FORMATTERS"] = ""

        actions += [ Commands.Set("DEVELOPMENT_ENVIRONMENT_COMPILERS", None),
                     Commands.Set("DEVELOPMENT_ENVIRONMENT_TEST_EXECUTORS", None),
                     Commands.Set("DEVELOPMENT_ENVIRONMENT_TEST_PARSERS", None),
                     Commands.Set("DEVELOPMENT_ENVIRONMENT_CODE_COVERAGE_VALIDATORS", None),
                     Commands.Set("DEVELOPMENT_ENVIRONMENT_TESTER_CONFIGURATIONS", None),
                     Commands.Set("DEVELOPMENT_ENVIRONMENT_FORMATTERS", None),
                   ]

        actions += DynamicPluginArchitecture.CreateRegistrationStatements( "DEVELOPMENT_ENVIRONMENT_COMPILERS",
                                                                           os.path.join(_script_dir, "Scripts", "Compilers"),
                                                                           lambda fullpath, name, ext: ext == ".py" and (name.endswith("Compiler") or name.endswith("CodeGenerator") or name.endswith("Verifier")),
                                                                         )

        actions += DynamicPluginArchitecture.CreateRegistrationStatements( "DEVELOPMENT_ENVIRONMENT_TEST_EXECUTORS",
                                                                           os.path.join(_script_dir, "Scripts", "TestExecutors"),
                                                                           lambda fullpath, name, ext: ext == ".py" and name.endswith("TestExecutor"),
                                                                         )
        
        actions += DynamicPluginArchitecture.CreateRegistrationStatements( "DEVELOPMENT_ENVIRONMENT_TEST_PARSERS",
                                                                           os.path.join(_script_dir, "Scripts", "TestParsers"),
                                                                           lambda fullpath, name, ext: ext == ".py" and name.endswith("TestParser"),
                                                                         )
        
        actions += DynamicPluginArchitecture.CreateRegistrationStatements( "DEVELOPMENT_ENVIRONMENT_CODE_COVERAGE_VALIDATORS",
                                                                           os.path.join(_script_dir, "Scripts", "CodeCoverageValidators"),
                                                                           lambda fullpath, name, ext: ext == ".py" and name.endswith("CodeCoverageValidator"),
                                                                         )

        actions += DynamicPluginArchitecture.CreateRegistrationStatements( "DEVELOPMENT_ENVIRONMENT_FORMATTERS",
                                                                           os.path.join(_script_dir, "src", "Formatter", "CommonEnvironment_Formatter", "Plugins"),
                                                                           lambda fullpath, name, ext: ext == ".py" and name.endswith("Formatter"),
                                                                         )

    actions.append(Commands.Augment( "DEVELOPMENT_ENVIRONMENT_TESTER_CONFIGURATIONS",
                                     [ "python-compiler-PyLint",
                                       "python-test_parser-PyUnittest",
                                       "python-coverage_executor-PyCoverage",
                                     ],
                                     update_memory=True,
                                   ))

    return actions

# ----------------------------------------------------------------------
def GetCustomScriptExtractors():
    """Returns script parsers used during activation."""

    Commands = CurrentShell.Commands

    # ----------------------------------------------------------------------
    def PythonWrapper(script_filename):
        if os.path.basename(script_filename) == "__init__.py":
            return

        return [ Commands.EchoOff(),
                 Commands.Execute('python "{}" {}'.format( script_filename,
                                                           CurrentShell.AllArgumentsScriptVariable,
                                                         )),
               ]

    # ----------------------------------------------------------------------
    def PythonDocs(script_filename):
        co = compile(open(script_filename, 'rb').read(), script_filename, "exec")

        if co and co.co_consts and isinstance(co.co_consts[0], six.string_types) and co.co_consts[0][0] != '_':
            return StringHelpers.Wrap(co.co_consts[0], 100)

    # ----------------------------------------------------------------------
    def PowershellScriptWrapper(script_filename):
        return Commands.Execute('powershell -executionpolicy unrestricted "{}" {}'.format(script_filename, CurrentShell.AllArgumentsScriptVariable))

    # ----------------------------------------------------------------------
    def EnvironmentScriptWrapper(script_filename):
        return Commands.Execute('"{}" {}'.format(script_filename, CurrentShell.AllArgumentsScriptVariable))

    # ----------------------------------------------------------------------

    return OrderedDict([ ( ".py", ( PythonWrapper, PythonDocs ) ),
                         ( ".ps1", PowershellScriptWrapper ),
                         ( CurrentShell.ScriptExtension, EnvironmentScriptWrapper ),
                       ])
