# ----------------------------------------------------------------------
# |
# |  WindowsPowerShell.py
# |
# |  Michael Sharp <ms@MichaelGSharp.com>
# |      2018-06-07 16:38:31
# |
# ----------------------------------------------------------------------

"""Contains the WindowsPowerShell object."""

import os
import textwrap

from collections import OrderedDict

import CommonEnvironment
from CommonEnvironment.Interface import staticderived, override, DerivedProperty
from CommonEnvironment.Shell.Commands import Augment, Set
from CommonEnvironment.Shell.WindowsShell import WindowsShell

# ----------------------------------------------------------------------
_script_fullpath                            = CommonEnvironment.ThisFullpath()
_script_dir, _script_name                   = os.path.split(_script_fullpath)
# ----------------------------------------------------------------------

# ----------------------------------------------------------------------
@staticderived
class WindowsPowerShell(WindowsShell):

    # ----------------------------------------------------------------------
    # |
    # |  Public Types
    # |
    # ----------------------------------------------------------------------

    # Powershell will be used in Windows environment when this environment variable is set to "1"
    USE_POWERSHELL_ENVIRONMENT_NAME         = "DEVELOPMENT_ENVIRONMENT_USE_WINDOWS_POWERSHELL"

    @staticderived
    @override
    class CommandVisitor(WindowsShell.CommandVisitor):
        # <Parameters differ from overridden 'name' method> pylint: disable = W0221
        # <Unused argument> pylint: disable = W0613

        # ----------------------------------------------------------------------
        @staticmethod
        @override
        def OnComment(command, *args, **kwargs):
            return "# {}".format(command.Value)

        # ----------------------------------------------------------------------
        @staticmethod
        @override
        def OnMessage(command, *args, **kwargs):
            output = []

            for line in command.Value.split("\n"):
                if not line.strip():
                    output.append("Write-Host ''")
                else:
                    output.append("Write-Host '{}'".format(WindowsShell._ProcessEscapedChars(line, OrderedDict([("`", "``"), ("'", "`'")]))))
            return "; ".join(output)

        # ----------------------------------------------------------------------
        @staticmethod
        @override
        def OnCall(command, *args, **kwargs):
            return 'Invoke-Expression "{}"'.format(command.CommandLine)

        # ----------------------------------------------------------------------
        @staticmethod
        @override
        def OnSymbolicLink(command, *args, **kwargs):
            d = {"link": command.LinkFilename, "target": command.Target}

            return textwrap.dedent(
                """\
                {remove}cmd /c mklink{dir_flag} "{link}" "{target}" > NULL
                """,
            ).format(
                remove="" if not command.RemoveExisting else 'if exist "{link}" ({remove} "{link}")\r\n'.format(
                    remove="rmdir" if command.IsDir else "del /Q",
                    **d
                ),
                dir_flag=" /D /J" if command.IsDir else "",
                **d
            )

        # ----------------------------------------------------------------------
        @classmethod
        @override
        def OnPath(cls, command, *args, **kwargs):
            return cls.OnSet(Set("PATH", command.Values))

        # ----------------------------------------------------------------------
        @classmethod
        @override
        def OnAugmentPath(cls, command, *args, **kwargs):
            return cls.OnAugment(Augment("PATH", command.Values))

        # ----------------------------------------------------------------------
        @staticmethod
        @override
        def OnSet(command, *args, **kwargs):
            if command.Values is None:
                return "if (Test-Path env:{name}) {{ Remove-Item env:{name} }}".format(
                    name=command.Name,
                )

            assert command.Values

            return '$env:{}="{}"'.format(command.Name, os.pathsep.join(command.Values)) # <Class '<name>' has no '<attr>' member> pylint: disable = E1101

        # ----------------------------------------------------------------------
        @classmethod
        @override
        def OnAugment(cls, command, *args, **kwargs):
            if not command.Values:
                return None

            if command.IsSpaceDelimitedString:
                new_values = " ".join(command.Values)
                sep = " "
            else:
                new_values = os.pathsep.join(command.Values)
                sep = ";"

            has_old_values = bool(os.getenv(command.Name))

            if has_old_values:
                new_values += sep
                old_values = " + $env:{}".format(command.Name)
            else:
                old_values = ""

            return '$env:{name}="{new_values}"{old_values}'.format(
                name=command.Name,
                new_values=new_values,
                old_values=old_values,
            )

        # ----------------------------------------------------------------------
        @staticmethod
        @override
        def OnExit(command, *args, **kwargs):
            return textwrap.dedent(
                """\
                {success}
                {error}
                exit {return_code}
                """,
            ).format(
                success="if ($?) { pause }" if command.PauseOnSuccess else "",
                error="if (-not $?) { pause }" if command.PauseOnError else "",
                return_code=command.ReturnCode or 0,
            )

        # ----------------------------------------------------------------------
        @staticmethod
        @override
        def OnExitOnError(command, *args, **kwargs):
            variable_name = "$env:{}".format(command.VariableName) if command.VariableName else "$?"

            return "if (-not {}){{ exit {}}}".format(variable_name, command.ReturnCode or variable_name)

        # ----------------------------------------------------------------------
        @staticmethod
        @override
        def OnEchoOff(command, *args, **kwargs):
            return '$InformationPreference = "Continue"'

        # ----------------------------------------------------------------------
        @staticmethod
        @override
        def OnCommandPrompt(command, *args, **kwargs):
            return 'function Global:prompt {{"PS: ({})  $($(Get-Location).path)>"}}'.format(command.Prompt)

        # ----------------------------------------------------------------------
        @staticmethod
        @override
        def OnPersistError(command, *args, **kwargs):
            return "$env:{}=$?".format(command.VariableName)

        # ----------------------------------------------------------------------
        @staticmethod
        @override
        def OnPushDirectory(command):
            directory = command.Directory

            if directory is None:
                directory = "$PSScriptRoot"

            return 'pushd "{}"'.format(directory)

    # ----------------------------------------------------------------------
    # |
    # |  Public Properties
    # |
    # ----------------------------------------------------------------------
    Name                                    = DerivedProperty("WindowsPowerShell")
    ScriptExtension                         = DerivedProperty(".ps1")
    AllArgumentsScriptVariable              = DerivedProperty("$args")

    # ----------------------------------------------------------------------
    # |
    # |  Public Methods
    # |
    # ----------------------------------------------------------------------
    @staticmethod
    @override
    def DecorateEnvironmentVariable(var_name):
        return "$env:{}".format(var_name)

    # ----------------------------------------------------------------------
    @classmethod
    @override
    def IsActive(cls, platform_name):
        return ("windows" in platform_name or platform_name == "nt") and os.getenv(cls.USE_POWERSHELL_ENVIRONMENT_NAME, None) == "1"

    # ----------------------------------------------------------------------
    @classmethod
    def CreateScriptName(
        cls,
        name,
        filename_only=False,
    ):
        filename = super(WindowsPowerShell, cls).CreateScriptName(
            name,
            filename_only=filename_only,
        )
        if filename_only:
            return filename

        return 'powershell "{}"'.format(filename)
