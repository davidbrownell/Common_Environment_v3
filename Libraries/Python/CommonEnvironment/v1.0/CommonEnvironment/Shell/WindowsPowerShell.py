# ----------------------------------------------------------------------
# |  
# |  WindowsPowerShell.py
# |  
# |  David Brownell <db@DavidBrownell.com>
# |      2018-05-07 07:18:00
# |  
# ----------------------------------------------------------------------
# |  
# |  Copyright David Brownell 2018.
# |  Distributed under the Boost Software License, Version 1.0.
# |  (See accompanying file LICENSE_1_0.txt or copy at http://www.boost.org/LICENSE_1_0.txt)
# |  
# ----------------------------------------------------------------------
"""Contains the WindowsPowerShell object."""

import os
import sys

from CommonEnvironment.Interface import staticderived
from CommonEnvironment.Shell.Commands import *
from CommonEnvironment.Shell.Commands.Visitor import Visitor

from CommonEnvironment.Shell.WindowsShell import WindowsShell

# ----------------------------------------------------------------------
_script_fullpath = os.path.abspath(__file__) if "python" in sys.executable.lower() else sys.executable
_script_dir, _script_name = os.path.split(_script_fullpath)
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

    # TODO: Update the visitor for powershell (this is a copy of the WindowsShell CommandVisitor here for reference)
    @staticderived
    class CommandVisitor(Visitor):
        # ----------------------------------------------------------------------
        @staticmethod
        def OnComment(command):
            return "REM {}".format(command.Value)

        # ----------------------------------------------------------------------
        @staticmethod
        def OnMessage(command):
            replacement_chars = [ ( '%', '%%' ),
                                  ( '^', '^^' ),
                                  ( '&', '^&' ),
                                  ( '<', '^<' ),
                                  ( '>', '^>' ),
                                  ( '|', '^|' ),
                                  ( ',', '^,' ),
                                  ( ';', '^;' ),
                                  ( '(', '^(' ),
                                  ( ')', '^)' ),
                                  ( '[', '^[' ),
                                  ( ']', '^]' ),
                                  ( '"', '\"' ),
                                ]
                                
            output = []
            
            for line in command.Value.split('\n'):
                if not line.strip():
                    output.append("echo.")
                else:
                    for old_char, new_char in replacement_chars:
                        line = line.replace(old_char, new_char)
                        
                    output.append("echo {}".format(line))
                    
            return '\n'.join(output)

        # ----------------------------------------------------------------------
        @staticmethod
        def OnCall(command):
            return "call {}".format(command.CommandLine)

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
                {remove}mklink{dir_flag} "{link}" "{target}" > NUL
                """).format( remove='' if not command.RemoveExisting else 'if exist "{link}" ({remove} "{link}")\n'.format( remove="rmdir" if command.IsDir else "del /Q",
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
                return "SET {}=".format(command.Name)

            assert command.Values

            return "SET {}={}".format(command.Name, WindowsShell.EnvironmentVariableDelimiter.join(command.Values))

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

            return "SET {name}={values};%{name}%".format( name=command.Name,
                                                          values=WindowsShell.EnvironmentVariableDelimiter.join(command.Values),
                                                        )
            
        # ----------------------------------------------------------------------
        @staticmethod
        def OnExit(command):
            return textwrap.dedent(
                """\
                {success}
                {error}
                exit /B {return_code}
                """).format( success="if %ERRORLEVEL% EQ 0 ( pause )" if command.PauseOnSuccess else '',
                             error="if %ERRORLEVEL% NEQ 0 ( pause )" if command.PauseOnError else '',
                             return_code=command.ReturnCode or 0,
                           )

        # ----------------------------------------------------------------------
        @staticmethod
        def OnExitOnError(command):
            return "if %ERRORLEVEL% NEQ 0 (exit /B {})".format(command.ReturnCode or "%ERRORLEVEL%")

        # ----------------------------------------------------------------------
        @staticmethod
        def OnRaw(command):
            return command.Value

        # ----------------------------------------------------------------------
        @staticmethod
        def OnEchoOff(command):
            return "@echo off"

        # ----------------------------------------------------------------------
        @staticmethod
        def OnCommandPrompt(command):
            return "set PROMPT=({}) $P$G".format(command.Prompt)

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

    # TODO: Verify these settings are correct. Remove those prefied with "Same as base: " that aren't necessary.

    Name                                    = "WindowsPowerShell"
    # Same as base: CategoryName                            = "Windows"
    # Same as base: ScriptExtension                         = ".cmd"
    ScriptExtension                         = ".ps1"
    # Same as base: ExecutableExtension                     = ".exe"
    # Same as base: CompressionExtensions                   = [ ".zip", ]
    AllArgumentsScriptVariable              = "$args"
    # Same as base: EnvironmentVariableDelimiter            = ";"
    # Same as base: HasCaseSensitiveFileSystem              = False
    # Same as base: Architecture                            = "x64" if os.getenv("ProgramFiles(x86)") else "x86"
    # Same as base: UserDirectory                           = None      # Set in __clsinit__
    # Same as base: TempDirectory                           = os.getenv("TMP")
    
    # ----------------------------------------------------------------------
    # |  
    # |  Public Methods
    # |  
    # ----------------------------------------------------------------------

    # TODO: The environment variable thing is a hack; is there a better way to detect that we are in a powershell environment?
    @classmethod
    def IsActive(cls, platform_name):
        return ("windows" in platform_name or platform_name == "nt") and os.getenv(cls.ENVIRONMENT_NAME, None) == "1"


    # TODO: Use the methods below if necessary, delete them if not used

    # ----------------------------------------------------------------------
    # |  
    # |  Private Methods
    # |  
    # ----------------------------------------------------------------------
    @staticmethod
    def _GeneratePrefixCommand():
        return

    # ----------------------------------------------------------------------
    @staticmethod
    def _GenerateSuffixCommand():
        return
