# ----------------------------------------------------------------------
# |  
# |  WindowsPowerShell.py
# |  
# |  Michael Sharp <ms@MichaelGSharp.com>
# |      2018-06-07 16:38:31
# |  
# ----------------------------------------------------------------------
# |  
# |  Copyright Michael Sharp 2018.
# |  Distributed under the Boost Software License, Version 1.0.
# |  (See accompanying file LICENSE_1_0.txt or copy at http://www.boost.org/LICENSE_1_0.txt)
# |  
# ----------------------------------------------------------------------
"""Contains the WindowsPowerShell object."""

import os
import sys

from CommonEnvironment.Interface import staticderived
from CommonEnvironment.Shell import *
from CommonEnvironment.Shell.Commands import *
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
    class CommandVisitor(Visitor):
        # ----------------------------------------------------------------------
        @staticmethod
        def OnComment(command):
            return "# {}".format(command.Value)

        # ----------------------------------------------------------------------
        @staticmethod
        def OnMessage(command):
            replacement_chars = [ ( '`', '``' ),
                                  ( "'", "''" ),
                                ]
                                
            output = []
            
            for line in command.Value.split('\n'):
                if not line.strip():
                    output.append("Write-Output ''")
                else:
                    for old_char, new_char in replacement_chars:
                        line = line.replace(old_char, new_char)
                        
                    output.append("Write-Output '{}'".format(line))
                    
            return '\n'.join(output)

        # ----------------------------------------------------------------------
        @staticmethod
        def OnCall(command):
            return 'Invoke-Expression "{}"'.format(command.CommandLine)

        # ----------------------------------------------------------------------
        @staticmethod
        def OnExecute(command):
            return command.CommandLine

        # ----------------------------------------------------------------------
        @staticmethod
        def OnSymbolicLink(command):
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
        def OnPath(cls, command):
            return cls.OnSet(Set("PATH", command.Values))

        # ----------------------------------------------------------------------
        @classmethod
        def OnAugmentPath(cls, command):
            return cls.OnAugment(Augment("PATH", command.Values))

        # ----------------------------------------------------------------------
        @staticmethod
        def OnSet(command):
            if command.Values is None:
                return "if (Test-Path env:{name}) {{ Remove-Item env:{name} }}".format(name=command.Name)

            assert command.Values

            return '$env:{}="{}"'.format(command.Name, WindowsShell.EnvironmentVariableDelimiter.join(command.Values))

        # ----------------------------------------------------------------------
        @classmethod
        def OnAugment(cls, command):
            if not command.Values:
                return

            current_values = set(WindowsShell.EnumEnvironmentVariable(command.Name))
            
            new_values = [ value.strip() for value in command.Values if value.strip() ]
            new_values = [ value for value in new_values if value not in current_values ]

            if not new_values:
                return

            return '$env:{name}="{values};" + $env:{name}'.format( name=command.Name,
                                                                   values=WindowsShell.EnvironmentVariableDelimiter.join(command.Values),
                                                                 )
            
        # ----------------------------------------------------------------------
        @staticmethod
        def OnExit(command):
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
        def OnExitOnError(command):
            return "if (-not $?){{ exit {}}}".format(command.ReturnCode or "$?")

        # ----------------------------------------------------------------------
        @staticmethod
        def OnRaw(command):
            return command.Value

        # ----------------------------------------------------------------------
        @staticmethod
        def OnEchoOff(command):
            return '$InformationPreference = "Continue"'

        # ----------------------------------------------------------------------
        @staticmethod
        def OnCommandPrompt(command):
            return 'function Global:prompt {{"PS: ({})  $($(Get-Location).path)>"}}'.format(command.Prompt)

        # ----------------------------------------------------------------------
        @staticmethod
        def OnDelete(command):
            if command.IsDir:
                return 'rmdir /S /Q "{}"'.format(command.FilenameOrDirectory)
            
            return 'del "{}"'.format(command.FilenameOrDirectory)

        # ----------------------------------------------------------------------
        @staticmethod
        def OnCopy(command):
            return 'copy /T "{source}" "{dest}"'.format( source=command.Source,
                                                         dest=command.Dest,
                                                       )

        # ----------------------------------------------------------------------
        @staticmethod
        def OnMove(command):
            return 'move /Y "{source}" "{dest}"'.format( source=command.Source,
                                                         dest=command.Dest,
                                                       )

    # ----------------------------------------------------------------------
    # |  
    # |  Public Properties
    # |  
    # ----------------------------------------------------------------------
    Name                                    = "WindowsPowerShell"
    ScriptExtension                         = ".ps1"
    AllArgumentsScriptVariable              = "$args"
    
    # ----------------------------------------------------------------------
    # |  
    # |  Public Methods
    # |  
    # ----------------------------------------------------------------------
    @classmethod
    def IsActive(cls, platform_name):
        return ("windows" in platform_name or platform_name == "nt") and os.getenv(cls.ENVIRONMENT_NAME, None) == "1"

    @staticmethod
    def DecorateInvokeScriptCommandLine(command_line):
        return "powershell " + command_line
