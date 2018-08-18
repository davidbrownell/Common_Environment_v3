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

from CommonEnvironment.Interface import staticderived, override, DerivedProperty
from CommonEnvironment.Shell.Commands import Augment, Set
from CommonEnvironment.Shell.Commands.Visitor import Visitor
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
    class CommandVisitor(Visitor):
        # ----------------------------------------------------------------------
        @staticmethod
        @override
        def OnComment(command, *args, **kwargs):
            return "# {}".format(command.Value)

        # ----------------------------------------------------------------------
        @staticmethod
        @override
        def OnMessage(command, *args, **kwargs):
            replacement_chars = [ ( '`', '``' ),
                                  ( "'", "''" ),
                                ]
                                
            output = []
            
            for line in command.Value.split('\n'):
                if not line.strip():
                    output.append("echo.")
                else:
                    for old_char, new_char in replacement_chars:
                        line = line.replace(old_char, new_char)
                        
                    output.append("echo '{}'".format(line))
                    
            return '\n'.join(output)

        # ----------------------------------------------------------------------
        @staticmethod
        @override
        def OnCall(command, *args, **kwargs):
            return 'Invoke-Expression "{}"'.format(command.CommandLine)

        # ----------------------------------------------------------------------
        @staticmethod
        @override
        def OnExecute(command, *args, **kwargs):
            return command.CommandLine

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

            return '$env:{}="{}"'.format(command.Name, WindowsShell.EnvironmentVariableDelimiter.join(command.Values))  # <Class '<name>' has no '<attr>' member> pylint: disable = E1101

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
                                                                   values=WindowsShell.EnvironmentVariableDelimiter.join(command.Values),   # <Class '<name>' has no '<attr>' member> pylint: disable = E1101
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
        def OnRaw(command, *args, **kwargs):
            return command.Value

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
        def OnDelete(command, *args, **kwargs):
            if command.IsDir:
                return 'rmdir /S /Q "{}"'.format(command.FilenameOrDirectory)
            
            return 'del "{}"'.format(command.FilenameOrDirectory)

        # ----------------------------------------------------------------------
        @staticmethod
        @override
        def OnCopy(command, *args, **kwargs):
            return 'copy /T "{source}" "{dest}"'.format( source=command.Source,
                                                         dest=command.Dest,
                                                       )

        # ----------------------------------------------------------------------
        @staticmethod
        @override
        def OnMove(command, *args, **kwargs):
            return 'move /Y "{source}" "{dest}"'.format( source=command.Source,
                                                         dest=command.Dest,
                                                       )

        # ----------------------------------------------------------------------
        @staticmethod
        @override
        def OnPersistError(command, *args, **kwargs):
            return '$env:{}=$?'.format(command.VariableName)

        # ----------------------------------------------------------------------
        @staticmethod
        @override
        def OnPushDirectory(command, *args, **kwargs):
            return 'pushd "{}"'.format(command.Directory)

        # ----------------------------------------------------------------------
        @staticmethod
        @override
        def OnPopDirectory(command, *args, **kwargs):
            return "popd"

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
    @classmethod
    @override
    def IsActive(cls, platform_name):
        return ("windows" in platform_name or platform_name == "nt") and os.getenv(cls.ENVIRONMENT_NAME, None) == "1"

    # ----------------------------------------------------------------------
    @classmethod
    def CreateScriptName(cls, name):
        return 'powershell "{}"'.format(super(WindowsPowerShell, cls).CreateScriptName(name))
    