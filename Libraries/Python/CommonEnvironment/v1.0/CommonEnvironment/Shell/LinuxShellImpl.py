# ----------------------------------------------------------------------
# |  
# |  LinuxShellImpl.py
# |  
# |  David Brownell <db@DavidBrownell.com>
# |      2018-05-11 12:50:32
# |  
# ----------------------------------------------------------------------
# |  
# |  Copyright David Brownell 2018.
# |  Distributed under the Boost Software License, Version 1.0.
# |  (See accompanying file LICENSE_1_0.txt or copy at http://www.boost.org/LICENSE_1_0.txt)
# |  
# ----------------------------------------------------------------------
"""Contains the LinuxShellImpl object"""

import os
import sys
import textwrap

from CommonEnvironment.Interface import staticderived
from CommonEnvironment.Shell import Shell
from CommonEnvironment.Shell.Commands import *
from CommonEnvironment.Shell.Commands.Visitor import Visitor

# ----------------------------------------------------------------------
_script_fullpath = os.path.abspath(__file__) if "python" in sys.executable.lower() else sys.executable
_script_dir, _script_name = os.path.split(_script_fullpath)
# ----------------------------------------------------------------------

class LinuxShellImpl(Shell):
    """
    Implements common Linux functionality.

    There are many Linux variations out there; this object can be used as
    a base class when implementating those variations.
    """

    # ----------------------------------------------------------------------
    # |  
    # |  Public Types
    # |  
    # ----------------------------------------------------------------------
    @staticderived
    class CommandVisitor(Visitor):
        # ----------------------------------------------------------------------
        @staticmethod
        def OnComment(command):
            return "# {}".format(command)
    
        # ----------------------------------------------------------------------
        @staticmethod
        def OnMessage(command):
            replacement_chars = [ ( '$', r'\$' ),
                                  ( '"', r'\"' ),
                                ]

            output = []

            for line in command.Value.split('\n'):
                if not line.strip():
                    output.append('echo ""')
                else:
                    for old_char, new_char in replacement_chars:
                        line = line.replace(old_char, new_char)

                    output.append('echo "{}"'.format(line))

            return '\n'.join(output)
    
        # ----------------------------------------------------------------------
        @staticmethod
        def OnCall(command):
            return "source {}".format(command.CommandLine)
    
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
                {remove}ln -fs{dir_flag} "{target}" "{link}"
                """).format( remove='' if not command.RemoveExisting else 'rm -f "{link}"\n'.format(**d),
                             dir_flag='d' if command.IsDir else '',
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
                return "export {}=".format(command.Name)

            assert command.Values

            return "export {}={}".format(command.Name, LinuxShellImpl.EnvironmentVariableDelimiter.join(command.Values))
    
        # ----------------------------------------------------------------------
        @staticmethod
        def OnAugment(command):
            if not command.Values:
                return

            current_values = set(LinuxShellImpl.EnumEnvironmentVariable(command.Name))
            
            new_values = [ value.strip() for value in command.Values if value.strip() ]
            new_values = [ value for value in new_values if value not in current_values ]

            if not new_values:
                return

            return "export {name}={values}:${name}".format( name=command.Name,
                                                            values=LinuxShellImpl.EnvironmentVariableDelimiter.join(command.Values),
                                                          )
    
        # ----------------------------------------------------------------------
        @staticmethod
        def OnExit(command):
            return textwrap.dedent(
                """\
                {success}
                {error}
                return {return_code}
                """).format( success=textwrap.dedent(
                                        """\
                                        if [ $? -eq 0 ]; then
                                            read -p "Press [Enter] to continue"
                                        fi
                                        """) if command.PauseOnSuccess else '',
                             error=textwrap.dedent(
                                        """\
                                        if [ $? -ne 0]; then
                                            read -p "Press [Enter] to continue"
                                        fi
                                        """) if command.PauseOnError else '',
                             return_code=command.ReturnCode or 0,
                           )
    
        # ----------------------------------------------------------------------
        @staticmethod
        def OnExitOnError(command):
            return textwrap.dedent(
                """\
                error_code=$?
                if [ $error_code -ne 0 ]; then
                    return $error_code
                fi
                """)
    
        # ----------------------------------------------------------------------
        @staticmethod
        def OnRaw(command):
            return command.Value
    
        # ----------------------------------------------------------------------
        @staticmethod
        def OnEchoOff(command):
            return ""
    
        # ----------------------------------------------------------------------
        @staticmethod
        def OnCommandPrompt(command):
            return r'PS1="({}) `id -nu`@`hostname -s`:\w$ "'.format(command.Prompt)
    
        # ----------------------------------------------------------------------
        @staticmethod
        def OnDelete(command):
            if command.IsDir:
                return 'rm -Rfd "{}"'.format(command.FilenameOrDirectory)
            
            return 'rm "{}"'.format(command.FilenameOrDirectory)
    
        # ----------------------------------------------------------------------
        @staticmethod
        def OnCopy(command):
            return 'cp "{source}" "{dest}"'.format( source=command.Source,
                                                    dest=command.Dest,
                                                  )
    
        # ----------------------------------------------------------------------
        @staticmethod
        def OnMove(command):
            return 'mv "{source}" "{dest}"'.format( source=command.Source,
                                                    dest=command.Dest,
                                                  )
    
    # ----------------------------------------------------------------------
    # |  
    # |  Public Properties
    # |  
    # ----------------------------------------------------------------------
    CategoryName                            = "Linux"
    ScriptExtension                         = ".sh"
    ExecutableExtension                     = ''
    CompressionExtensions                   = [ ".tgz", ".tar", "gz", ]
    AllArgumentsScriptVariable              = '"$@"'
    EnvironmentVariableDelimiter            = ':'
    HasCaseSensitiveFileSystem              = True
    Architecture                            = "x64"     # I don't know of a reliable, cross-distro way to detect architecture
    UserDirectory                           = os.path.expanduser("~")
    TempDirectory                           = "/tmp"

    # ----------------------------------------------------------------------
    # |  
    # |  Public Methods
    # |  
    # ----------------------------------------------------------------------
    @classmethod
    def IsActive(cls, platform_name):
        return cls.Name.lower() in platform_name

    # ----------------------------------------------------------------------
    @staticmethod
    def RemoveDir(path):
        if os.path.isdir(path):
            os.system('rm -Rfd "{}"'.format(path))

    # ----------------------------------------------------------------------
    # |  
    # |  Private Methods
    # |  
    # ----------------------------------------------------------------------
    @staticmethod
    def _GeneratePrefixCommand():
        return "#!/bin/bash"

    # ----------------------------------------------------------------------
    @staticmethod
    def _GenerateSuffixCommand():
        return
