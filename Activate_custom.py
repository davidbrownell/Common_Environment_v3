# ----------------------------------------------------------------------
# |
# |  Activate_custom.py
# |
# |  David Brownell <db@DavidBrownell.com>
# |      2018-05-07 08:59:57
# |
# ----------------------------------------------------------------------
# |
# |  Copyright David Brownell 2018-20.
# |  Distributed under the Boost Software License, Version 1.0.
# |  (See accompanying file LICENSE_1_0.txt or copy at http://www.boost.org/LICENSE_1_0.txt)
# |
# ----------------------------------------------------------------------
"""Functionality to further enhance Common_Environment activation"""

import os
import sys
import textwrap

from collections import OrderedDict

import six

import CommonEnvironment

# ----------------------------------------------------------------------
_script_fullpath                            = CommonEnvironment.ThisFullpath()
_script_dir, _script_name                   = os.path.split(_script_fullpath)
# ----------------------------------------------------------------------

sys.path.insert(0, os.getenv("DEVELOPMENT_ENVIRONMENT_FUNDAMENTAL"))
from RepositoryBootstrap.SetupAndActivate import DynamicPluginArchitecture

# Note that other repositories can import CommonEnvironment directly.
from RepositoryBootstrap.Impl import CommonEnvironmentImports

CurrentShell                                = CommonEnvironmentImports.CurrentShell
StringHelpers                               = CommonEnvironmentImports.StringHelpers

del sys.path[0]

# ----------------------------------------------------------------------
def GetCustomActions(
    output_stream,
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
        actions.append(
            Commands.Message(
                "** FAST: Dynamic tester information has not been activated. ({}) **".format(
                    _script_fullpath,
                ),
            ),
        )
    else:
        # Reset any existing values
        os.environ["DEVELOPMENT_ENVIRONMENT_COMPILERS"] = ""
        os.environ["DEVELOPMENT_ENVIRONMENT_TEST_EXECUTORS"] = ""
        os.environ["DEVELOPMENT_ENVIRONMENT_TEST_PARSERS"] = ""
        os.environ["DEVELOPMENT_ENVIRONMENT_CODE_COVERAGE_VALIDATORS"] = ""
        os.environ["DEVELOPMENT_ENVIRONMENT_TESTER_CONFIGURATIONS"] = ""
        os.environ["DEVELOPMENT_ENVIRONMENT_FORMATTERS"] = ""

        actions += [
            Commands.Set("DEVELOPMENT_ENVIRONMENT_COMPILERS", None),
            Commands.Set("DEVELOPMENT_ENVIRONMENT_TEST_EXECUTORS", None),
            Commands.Set("DEVELOPMENT_ENVIRONMENT_TEST_PARSERS", None),
            Commands.Set("DEVELOPMENT_ENVIRONMENT_CODE_COVERAGE_VALIDATORS", None),
            Commands.Set("DEVELOPMENT_ENVIRONMENT_TESTER_CONFIGURATIONS", None),
            Commands.Set("DEVELOPMENT_ENVIRONMENT_FORMATTERS", None),
        ]

        actions += DynamicPluginArchitecture.CreateRegistrationStatements(
            "DEVELOPMENT_ENVIRONMENT_COMPILERS",
            os.path.join(_script_dir, "Scripts", "Compilers"),
            lambda fullpath, name, ext: ext == ".py"
            and (
                name.endswith("Compiler")
                or name.endswith("CodeGenerator")
                or name.endswith("Verifier")
            ),
        )

        actions += DynamicPluginArchitecture.CreateRegistrationStatements(
            "DEVELOPMENT_ENVIRONMENT_TEST_EXECUTORS",
            os.path.join(_script_dir, "Scripts", "TestExecutors"),
            lambda fullpath, name, ext: ext == ".py" and name.endswith("TestExecutor"),
        )

        actions += DynamicPluginArchitecture.CreateRegistrationStatements(
            "DEVELOPMENT_ENVIRONMENT_TEST_PARSERS",
            os.path.join(_script_dir, "Scripts", "TestParsers"),
            lambda fullpath, name, ext: ext == ".py" and name.endswith("TestParser"),
        )

        actions += DynamicPluginArchitecture.CreateRegistrationStatements(
            "DEVELOPMENT_ENVIRONMENT_CODE_COVERAGE_VALIDATORS",
            os.path.join(_script_dir, "Scripts", "CodeCoverageValidators"),
            lambda fullpath, name, ext: ext == ".py"
            and name.endswith("CodeCoverageValidator"),
        )

        actions += DynamicPluginArchitecture.CreateRegistrationStatements(
            "DEVELOPMENT_ENVIRONMENT_FORMATTERS",
            os.path.join(
                _script_dir,
                "src",
                "Formatter",
                "CommonEnvironment_Formatter",
                "Plugins",
            ),
            lambda fullpath, name, ext: ext == ".py" and name.endswith("Formatter"),
        )

        # Check to see if developer mode is enabled on Windows
        if CommonEnvironmentImports.CurrentShell.CategoryName == "Windows":
            import winreg

            try:
                hkey = winreg.OpenKey(
                    winreg.HKEY_LOCAL_MACHINE,
                    r"SOFTWARE\Microsoft\Windows\CurrentVersion\AppModelUnlock",
                )
                with CommonEnvironmentImports.CallOnExit(lambda: winreg.CloseKey(hkey)):
                    value = winreg.QueryValueEx(hkey, "AllowDevelopmentWithoutDevLicense")[0]

                    if value != 1:
                        actions.append(
                            Commands.Message(
                                "\n".join(
                                    [
                                        "        {}".format(line) for line in textwrap.dedent(
                                            """\

                                            # ----------------------------------------------------------------------
                                            # ----------------------------------------------------------------------

                                            WARNING:

                                            Windows Developer Mode is not enabled; this is a requirement for the setup process
                                            as Developer Mode allows for the creation of symbolic links without admin privileges.

                                            To enable Developer Mode in Windows:

                                                1) Launch 'Developer settings'
                                                2) Select 'Developer mode'

                                            # ----------------------------------------------------------------------
                                            # ----------------------------------------------------------------------

                                            """,
                                        ).split("\n")
                                    ]
                                ),
                            ),
                        )
            except FileNotFoundError:
                # This key isn't available on all versions of Windows
                pass

            # Check to see if long paths are enabled on Windows
            try:
                # Python imports can begin to break down if long paths aren't enabled
                hkey = winreg.OpenKey(
                    winreg.HKEY_LOCAL_MACHINE,
                    r"SYSTEM\ControlSet001\Control\FileSystem",
                )
                with CommonEnvironmentImports.CallOnExit(lambda: winreg.CloseKey(hkey)):
                    value = winreg.QueryValueEx(hkey, "LongPathsEnabled")[0]

                    if value != 1:
                        actions.append(
                            Commands.Message(
                                "\n".join(
                                    [
                                        "        {}".format(line) for line in textwrap.dedent(
                                            """\

                                            # ----------------------------------------------------------------------
                                            # ----------------------------------------------------------------------

                                            WARNING:

                                            Long path support is not enabled. While this isn't a requirement
                                            for running on Windows, it could present problems with
                                            python imports in deeply nested directory hierarchies.

                                            To enable long path support in Windows:

                                                1) Launch 'regedit'
                                                2) Navigate to 'HKEY_LOCAL_MACHINE\\SYSTEM\\ControlSet001\\Control\\FileSystem'
                                                3) Edit the value 'LongPathsEnabled'
                                                4) Set the value to 1

                                            # ----------------------------------------------------------------------
                                            # ----------------------------------------------------------------------

                                            """,
                                        ).split("\n")
                                    ]
                                ),
                            ),
                        )

            except FileNotFoundError:
                # This key isn't available on all versions of Windows
                pass

    # Check to see if git is installed and if its settings are set to the best defaults
    if "usage: git" in CommonEnvironmentImports.Process.Execute("git")[1] != -1:
        result, git_output = CommonEnvironmentImports.Process.Execute(
            "git config --get core.autocrlf",
        )

        git_output = git_output.strip()

        if result != 0 or git_output != "false":
            actions.append(
                Commands.Message(
                    "\n".join(
                        [
                            "        {}".format(line) for line in textwrap.dedent(
                                """\

                                # ----------------------------------------------------------------------
                                # ----------------------------------------------------------------------

                                WARNING:

                                Git is configured to modify line endings on checkin and/or checkout.
                                While this was the recommended setting in the past, it presents problems
                                when editing code on both Windows and Linux using modern editors.

                                It is recommended that you change this setting to not modify line endings:

                                    1) 'git config --global core.autocrlf false'

                                # ----------------------------------------------------------------------
                                # ----------------------------------------------------------------------

                                """,
                            ).split("\n")
                        ]
                    ),
                ),
            )

    actions.append(
        Commands.Augment(
            "DEVELOPMENT_ENVIRONMENT_TESTER_CONFIGURATIONS",
            [
                "python-compiler-PyLint",
                "python-test_parser-PyUnittest",
                "python-coverage_executor-PyCoverage",
                "pytest-compiler-PyLint",
                "pytest-test_parser-Pytest",
                "pytest-coverage_executor-PyCoverage",
            ],
        ),
    )

    return actions


# ----------------------------------------------------------------------
def GetCustomScriptExtractors():
    """Returns script parsers used during activation."""

    Commands = CurrentShell.Commands

    # ----------------------------------------------------------------------
    def PythonWrapper(script_filename):
        if os.path.basename(script_filename) == "__init__.py":
            return

        return [
            Commands.EchoOff(),
            Commands.Execute(
                'python "{}" {}'.format(
                    script_filename,
                    CurrentShell.AllArgumentsScriptVariable,
                ),
            ),
        ]

    # ----------------------------------------------------------------------
    def PythonDocs(script_filename):
        co = compile(open(script_filename, "rb").read(), script_filename, "exec")

        if (
            co
            and co.co_consts
            and isinstance(co.co_consts[0], six.string_types)
            and co.co_consts[0][0] != "_"
        ):
            return StringHelpers.Wrap(co.co_consts[0], 100)

    # ----------------------------------------------------------------------
    def PowershellScriptWrapper(script_filename):
        return [
            Commands.EchoOff(),
            Commands.Execute(
                'powershell -executionpolicy unrestricted "{}" {}'.format(
                    script_filename,
                    CurrentShell.AllArgumentsScriptVariable,
                ),
            ),
        ]

    # ----------------------------------------------------------------------
    def EnvironmentScriptWrapper(script_filename):
        return [
            Commands.EchoOff(),
            Commands.Execute(
                '"{}" {}'.format(script_filename, CurrentShell.AllArgumentsScriptVariable),
            ),
        ]

    # ----------------------------------------------------------------------

    return OrderedDict(
        [
            (".py", (PythonWrapper, PythonDocs)),
            (".ps1", PowershellScriptWrapper),
            (CurrentShell.ScriptExtension, EnvironmentScriptWrapper),
        ],
    )
