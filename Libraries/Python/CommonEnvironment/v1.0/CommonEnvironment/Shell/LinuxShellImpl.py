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

from collections import OrderedDict

from CommonEnvironment.Interface import staticderived, override, DerivedProperty
from CommonEnvironment.Shell import Shell
from CommonEnvironment.Shell.Commands import Set, Augment
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
    @override
    class CommandVisitor(Visitor):
        
        # <Parameters differ from overridden '<...>' method> pylint: disable = W0221

        # ----------------------------------------------------------------------
        @staticmethod
        @override
        def OnComment(command):
            return "# {}".format(command)
    
        # ----------------------------------------------------------------------
        @staticmethod
        @override
        def OnMessage(command):
            output = []

            for line in command.Value.split('\n'):
                if not line.strip():
                    output.append('echo ""')
                else:
                    output.append('echo "{}"'.format(LinuxShellImpl._ProcessEscapedChars( line,
                                                                                          OrderedDict([ ( '$', r'\$' ),
                                                                                                        ( '"', r'\"' ),
                                                                                                      ]),
                                                                                        )))
            return ' && '.join(output)
    
        # ----------------------------------------------------------------------
        @staticmethod
        @override
        def OnCall(command):
            return "source {}".format(command.CommandLine)
    
        # ----------------------------------------------------------------------
        @staticmethod
        @override
        def OnExecute(command):
            return command.CommandLine
    
        # ----------------------------------------------------------------------
        @staticmethod
        @override
        def OnSymbolicLink(command):
            return textwrap.dedent(
                """\
                ln -{force_flag}s{dir_flag} "{target}" "{link}"
                """).format( force_flag='' if not command.RemoveExisting else 'f',
                             dir_flag='d' if command.IsDir else '',
                             target=command.Target,
                             link=command.LinkFilename,
                           )
    
        # ----------------------------------------------------------------------
        @classmethod
        @override
        def OnPath(cls, command):
            return cls.OnSet(Set("PATH", command.Values))
    
        # ----------------------------------------------------------------------
        @classmethod
        @override
        def OnAugmentPath(cls, command):
            return cls.OnAugment(Augment("PATH", command.Values))
    
        # ----------------------------------------------------------------------
        @staticmethod
        @override
        def OnSet(command):
            if command.Values is None:
                return "export {}=".format(command.Name)

            assert command.Values

            return "export {}={}".format(command.Name, os.pathsep.join(command.Values))    # <Class '<name>' has no '<attr>' member> pylint: disable = E1101
    
        # ----------------------------------------------------------------------
        @staticmethod
        @override
        def OnAugment(command):
            if not command.Values:
                return None

            current_values = set(LinuxShellImpl.EnumEnvironmentVariable(command.Name))
            
            new_values = [ value.strip() for value in command.Values if value.strip() ]
            new_values = [ value for value in new_values if value not in current_values ]

            if not new_values:
                return None

            return "export {name}={values}:${name}".format( name=command.Name,
                                                            values=os.pathsep.join(command.Values),    # <Class '<name>' has no '<attr>' member> pylint: disable = E1101
                                                          )
    
        # ----------------------------------------------------------------------
        @staticmethod
        @override
        def OnExit(command):
            return textwrap.dedent(
                """\
                {success}
                {error}
                return {return_code}
                """).format( success=textwrap.dedent(
                                        # <Wrong hanging indentation> pylint: disable = C0330
                                        """\
                                        if [[ $? -eq 0 ]]
                                        then
                                            read -p "Press [Enter] to continue"
                                        fi
                                        """) if command.PauseOnSuccess else '',
                             error=textwrap.dedent(
                                        # <Wrong hanging indentation> pylint: disable = C0330
                                        """\
                                        if [[ $? -ne 0]] 
                                        then
                                            read -p "Press [Enter] to continue"
                                        fi
                                        """) if command.PauseOnError else '',
                             return_code=command.ReturnCode or 0,
                           )
    
        # ----------------------------------------------------------------------
        @staticmethod
        @override
        def OnExitOnError(command):
            variable_name = "${}".format(command.VariableName) if command.VariableName else "$?"

            return textwrap.dedent(
                """\
                error_code={}
                if [[ $error_code -ne 0 ]]
                then
                    exit {}
                fi
                """).format( variable_name,
                             command.ReturnCode or "$error_code",
                           )
    
        # ----------------------------------------------------------------------
        @staticmethod
        @override
        def OnRaw(command):
            return command.Value
    
        # ----------------------------------------------------------------------
        @staticmethod
        @override
        def OnEchoOff(command):
            return ""
    
        # ----------------------------------------------------------------------
        @staticmethod
        @override
        def OnCommandPrompt(command):
            return r'PS1="({}) `id -nu`@`hostname -s`:\w$ "'.format(command.Prompt)
    
        # ----------------------------------------------------------------------
        @staticmethod
        @override
        def OnDelete(command):
            if command.IsDir:
                return 'rm -Rfd "{}"'.format(command.FilenameOrDirectory)
            
            return 'rm "{}"'.format(command.FilenameOrDirectory)
    
        # ----------------------------------------------------------------------
        @staticmethod
        @override
        def OnCopy(command):
            return 'cp "{source}" "{dest}"'.format( source=command.Source,
                                                    dest=command.Dest,
                                                  )
    
        # ----------------------------------------------------------------------
        @staticmethod
        @override
        def OnMove(command):
            return 'mv "{source}" "{dest}"'.format( source=command.Source,
                                                    dest=command.Dest,
                                                  )
    
        # ----------------------------------------------------------------------
        @staticmethod
        @override
        def OnPersistError(command):
            return "{}=$?".format(command.VariableName)

        # ----------------------------------------------------------------------
        @staticmethod
        @override
        def OnPushDirectory(command):
            return 'pushd "{}" > /dev/null'.format(command.Directory)

        # ----------------------------------------------------------------------
        @staticmethod
        @override
        def OnPopDirectory(command):
            return "popd > /dev/null"

    # ----------------------------------------------------------------------
    # |  
    # |  Public Properties
    # |  
    # ----------------------------------------------------------------------
    CategoryName                            = DerivedProperty("Linux")
    ScriptExtension                         = DerivedProperty(".sh")
    ExecutableExtension                     = DerivedProperty('')
    CompressionExtensions                   = DerivedProperty([ ".tgz", ".tar", "gz", ])
    AllArgumentsScriptVariable              = DerivedProperty('"$@"')
    HasCaseSensitiveFileSystem              = DerivedProperty(True)
    Architecture                            = DerivedProperty("x64")        # I don't know of a reliable, cross-distro way to detect architecture
    UserDirectory                           = DerivedProperty(os.path.expanduser("~"))
    TempDirectory                           = DerivedProperty("/tmp")

    # ----------------------------------------------------------------------
    # |  
    # |  Public Methods
    # |  
    # ----------------------------------------------------------------------
    @classmethod
    @override
    def IsActive(cls, platform_name):
        # <Class '<name>' has no '<attr>' member> pylint: disable = E1101
        return cls.Name.lower() in platform_name

    # ----------------------------------------------------------------------
    @staticmethod
    @override
    def RemoveDir(path):
        if os.path.isdir(path):
            os.system('rm -Rfd "{}"'.format(path))

    # ----------------------------------------------------------------------
    @staticmethod
    @override
    def DecorateEnvironmentVariable(var_name):
        return "\\${}".format(var_name)

    # ----------------------------------------------------------------------
    @staticmethod
    @override
    def UpdateOwnership(filename_or_directory):
        if ( hasattr(os, "geteuid") and
             os.geteuid() == 0 and 
             not any(var for var in [ "SUDO_UID", "SUDO_GID", ] if var not in os.environ)
           ):
           os.system('chown {recursive} {user}:{group} "{input}"' \
                        .format( recursive="--recursive" if os.path.isdir(filename_or_directory) else '',
                                 user=os.environ["SUDO_UID"],
                                 group=os.environ["SUDO_GID"],
                                 input=filename_or_directory,
                               ))

    # ----------------------------------------------------------------------
    # |  
    # |  Private Methods
    # |  
    # ----------------------------------------------------------------------
    @staticmethod
    @override
    def _GeneratePrefixCommand():
        return "#!/bin/bash"

    # ----------------------------------------------------------------------
    @staticmethod
    @override
    def _GenerateSuffixCommand():
        return
