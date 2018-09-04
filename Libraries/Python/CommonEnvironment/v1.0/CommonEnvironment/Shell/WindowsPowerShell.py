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
import sys
import textwrap

from collections import OrderedDict

from CommonEnvironment.Interface import staticderived, override, DerivedProperty
from CommonEnvironment.Shell.Commands import Augment, Set
from CommonEnvironment.Shell.WindowsShell import WindowsShell

# ----------------------------------------------------------------------
_script_fullpath = os.path.abspath(__file__) if "python" in sys.executable.lower() else sys.executable
_script_dir, _script_name = os.path.split(_script_fullpath)
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
    ENVIRONMENT_NAME                        = "DEVELOPMENT_ENVIRONMENT_USE_WINDOWS_POWERSHELL"

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

            for line in command.Value.split('\n'):
                if not line.strip():
                    output.append("Write-Host ''")
                else:
                    output.append("Write-Host '{}'".format(WindowsShell._ProcessEscapedChars( line,
                                                                                              OrderedDict([ ( '`', '``' ),
                                                                                                            ( "'", "`'" ),
                                                                                                          ]),
                                                                                            )))
            return '; '.join(output)

        # ----------------------------------------------------------------------
        @staticmethod
        @override
        def OnCall(command, *args, **kwargs):
            return 'Invoke-Expression "{}"'.format(command.CommandLine)

        # ----------------------------------------------------------------------
        @staticmethod
        @override
        def OnSymbolicLink(command, *args, **kwargs):
            d = { "link" : command.LinkFilename,
                  "target" : command.Target,
                }

            return textwrap.dedent(
                """\
                {remove}cmd /c mklink{dir_flag} "{link}" "{target}" > NULL
                """).format( remove='' if not command.RemoveExisting else 'if exist "{link}" ({remove} "{link}")\r\n'.format( remove="rmdir" if command.IsDir else "del /Q",
                                                                                                                              **d
                                                                                                                            ),
                             dir_flag=" /D /J" if command.IsDir else '',
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
                return "if (Test-Path env:{name}) {{ Remove-Item env:{name} }}".format(name=command.Name)

            assert command.Values

            return '$env:{}="{}"'.format(command.Name, os.pathsep.join(command.Values))  # <Class '<name>' has no '<attr>' member> pylint: disable = E1101

        # ----------------------------------------------------------------------
        @classmethod
        @override
        def OnAugment(cls, command, *args, **kwargs):
            if not command.Values:
                return None

            current_values = set(WindowsShell.EnumEnvironmentVariable(command.Name))
            
            new_values = [ value.strip() for value in command.Values if value.strip() ]
            new_values = [ value for value in new_values if value not in current_values ]

            if not new_values:
                return None

            return '$env:{name}="{values};" + $env:{name}'.format( name=command.Name,
                                                                   values=os.pathsep.join(command.Values),   # <Class '<name>' has no '<attr>' member> pylint: disable = E1101
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
                """).format( success="if ($?) { pause }" if command.PauseOnSuccess else '',
                             error="if (-not $?) { pause }" if command.PauseOnError else '',
                             return_code=command.ReturnCode or 0,
                           )

        # ----------------------------------------------------------------------
        @staticmethod
        @override
        def OnExitOnError(command, *args, **kwargs):
            variable_name = "$env:{}".format(command.VariableName) if command.VariableName else "$?"

            return "if (-not {}){{ exit {}}}".format( variable_name,
                                                      command.ReturnCode or variable_name,
                                                    )

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
            return '$env:{}=$?'.format(command.VariableName)

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
        return ("windows" in platform_name or platform_name == "nt") and os.getenv(cls.ENVIRONMENT_NAME, None) == "1"

    # ----------------------------------------------------------------------
    @classmethod
    def CreateScriptName(cls, name, filename_only=False):
        filename = super(WindowsPowerShell, cls).CreateScriptName(name, filename_only=filename_only)
        if filename_only:
            return filename

        return 'powershell "{}"'.format(filename)
    