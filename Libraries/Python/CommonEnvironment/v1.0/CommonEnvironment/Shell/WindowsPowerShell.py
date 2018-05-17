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

    # TODO: Update this for power shell
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
            return textwrap.dedent(
                """\
                if exist "{link}" ({remove} "{link}")
                mklink{dir_flag} "{link}" "{target}" > NUL
                """).format( link=command.LinkFilename,
                             target=command.Target,
                             dir_flag=" /D /J" if command.IsDir else '',
                             remove="rmdir" if command.IsDir else "del /Q",
                           )

        # ----------------------------------------------------------------------
        @classmethod
        def OnPath(cls, command):
            return cls.OnSet(Set("PATH", command.Values, command.PreserveOriginal))

        # ----------------------------------------------------------------------
        @classmethod
        def OnAugmentPath(cls, command):
            return cls.OnAugment(Augment("PATH", command.Values))

        # ----------------------------------------------------------------------
        @staticmethod
        def OnSet(command):
            if len(command.Values) == 1 and command.Values[0] is None:
                assert command.PreserveOriginal == False
                return "SET {}=".format(command.Name)

            return "SET {}={}{}".format( command.Name,
                                         WindowsShell.EnvironmentVariableDelimiter.join(command.Values),
                                         ";%{}%".format(command.Name) if command.PreserveOriginal else '',
                                       )

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

            return cls.OnSet(Set(command.Name, new_values, bool(current_values)))
            
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
            if not command.IsDir:
                return 'del "{}"'.format(command.FilenameOrDirectory)
            
            return 'rmdir /S /Q "{}"'.format(command.FilenameOrDirectory)

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
    # Same as base: CategoryName                            = "Windows"
    # Same as base: ScriptExtension                         = ".cmd"
    ScriptExtension                         = ".ps1"
    # Same as base: ExecutableExtension                     = ".exe"
    # Same as base: AllArgumentsScriptVariable              = "%*"
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
    @classmethod
    def IsActive(cls, platform_name):
        return ("windows" in platform_name or platform_name == "nt") and os.getenv(cls.ENVIRONMENT_NAME, None) == "1"

    # Same as base: # ----------------------------------------------------------------------
    # Same as base: @classmethod
    # Same as base: def __clsinit__(cls):
    # Same as base:     # User directory
    # Same as base:     # Directory
    # Same as base:     from win32com.shell import shellcon, shell      # <Unable to import> pylint: disable = F0401, E0611
    # Same as base:     import unicodedata
    # Same as base:     
    # Same as base:     homedir = shell.SHGetFolderPath(0, shellcon.CSIDL_APPDATA, 0, 0)
    # Same as base:     homedir = unicodedata.normalize("NFKD", homedir)
    # Same as base:     
    # Same as base:     if sys.version_info[0] == 2:
    # Same as base:         homedir = homedir.encode("ascii", "ignore")
    # Same as base: 
    # Same as base:     cls.UserDirectory                   = homedir
    # Same as base: 
    # Same as base: # ----------------------------------------------------------------------
    # Same as base: @staticmethod
    # Same as base: def RemoveDir(path):
    # Same as base:     if os.path.isdir(path):
    # Same as base:         os.system('rmdir /S /Q "{}"'.format(path))
    # Same as base: 
    # Same as base: # ----------------------------------------------------------------------
    # Same as base: if sys.version_info[0] == 2:
    # Same as base:     # Python 2.+ doesn't support symlinks on Windows, so we have to provide 
    # Same as base:     # much of its functionality manually.
    # Same as base: 
    # Same as base:     # ----------------------------------------------------------------------
    # Same as base:     @staticmethod
    # Same as base:     def IsSymLink(filename):
    # Same as base:         import win32file
    # Same as base: 
    # Same as base:         file_attribute_reparse_point = 1024
    # Same as base:     
    # Same as base:         return os.path.exists(filename) and win32file.GetFileAttributes(filename) & file_attribute_reparse_point == file_attribute_reparse_point
    # Same as base: 
    # Same as base:     # ----------------------------------------------------------------------
    # Same as base:     @staticmethod
    # Same as base:     def ResolveSymLink(filename):
    # Same as base:         # Python 2.+ doesn't support symlinks on Windows and there doesn't seem to be
    # Same as base:         # a way to resolve a symlink without parsing the file, and libraries mentioned
    # Same as base:         # http://stackoverflow.com/questions/1447575/symlinks-on-windows/7924557#7924557
    # Same as base:         # and https://github.com/sid0/ntfs seem to have problems. The only way I have found
    # Same as base:         # to reliabaly get this info is to parse the output of 'dir' and extact the info.
    # Same as base:         # This is horribly painful code.
    # Same as base:         
    # Same as base:         import re
    # Same as base: 
    # Same as base:         import six
    # Same as base:         from six import StringIO
    # Same as base:         import six.moves.cPickle as pickle
    # Same as base: 
    # Same as base:         from CommonEnvironment import Process
    # Same as base: 
    # Same as base:         filename = filename.replace('/', os.path.sep)
    # Same as base: 
    # Same as base:         assert cls.IsSymLink(filename)
    # Same as base: 
    # Same as base:         if not hasattr(cls, "_symlink_lookup"):
    # Same as base:             cls._symlink_lookup = {}                # <Attribute defined outside __init__> pylint: disable = W0201
    # Same as base:             cls._symlink_redirection_maps = {}      # <Attribute defined outside __init__> pylint: disable = W0201
    # Same as base: 
    # Same as base:         if filename in cls._symlink_lookup:
    # Same as base:             return cls._symlink_lookup[filename]
    # Same as base: 
    # Same as base:         # Are there any redirection maps that reside in the filename's path?
    # Same as base:         path = os.path.split(filename)[0]
    # Same as base:         while True:
    # Same as base:             potential_map_filename = os.path.join(path, "symlink.redirection_map")
    # Same as base:             if os.path.isfile(potential_map_filename):
    # Same as base:                 if potential_map_filename not in cls._symlink_redirection_maps:
    # Same as base:                     cls._symlink_redirection_maps[potential_map_filename] = pickle.loads(open(potential_map_filename).read())
    # Same as base: 
    # Same as base:                 if filename in cls._symlink_redirection_maps[potential_map_filename]:
    # Same as base:                     return cls._symlink_redirection_maps[potential_map_filename][filename]
    # Same as base: 
    # Same as base:             new_path = os.path.split(path)[0]
    # Same as base:             if new_path == path:
    # Same as base:                 break
    # Same as base: 
    # Same as base:             path = new_path
    # Same as base: 
    # Same as base:         # If here, there isn't a map filename so we have to do things the hard way.
    # Same as base:         if os.path.isfile(filename):
    # Same as base:             command_line = 'dir /AL "%s"' % filename
    # Same as base:             is_match = lambda name: True
    # Same as base:         else:
    # Same as base:             command_line = 'dir /AL "%s"' % os.path.dirname(filename)
    # Same as base:             is_match = lambda name: name == os.path.basename(filename)
    # Same as base: 
    # Same as base:         rval, sink = Process.Execute(command_line)
    # Same as base:         
    # Same as base:         regexp = re.compile(r".+<(?P<type>.+?)>\s+(?P<link>.+?)\s+\[(?P<filename>.+?)\]\s*")
    # Same as base: 
    # Same as base:         for line in sink.split('\n'):
    # Same as base:             match = regexp.match(line)
    # Same as base:             if match:
    # Same as base:                 link = match.group("link")
    # Same as base:                 if not is_match(link):
    # Same as base:                     continue
    # Same as base: 
    # Same as base:                 target_filename = match.group("filename")
    # Same as base:                 assert os.path.exists(target_filename), target_filename
    # Same as base: 
    # Same as base:                 cls._symlink_lookup[filename] = target_filename
    # Same as base:                 return target_filename
    # Same as base: 
    # Same as base:         assert False, sink
    # Same as base: 
    # Same as base:     # ----------------------------------------------------------------------
    # Same as base:     @staticmethod
    # Same as base:     def DeleteSymLink(filename):
    # Same as base:         assert self.IsSymLink(filename), filename
    # Same as base:     
    # Same as base:         if os.path.isdir(filename):
    # Same as base:             command_line = 'rmdir "{}"'.format(filename)
    # Same as base:         elif os.path.isfile(filename):
    # Same as base:             command_line = 'del /Q "{}"'.format(filename)
    # Same as base:         else:
    # Same as base:             assert False, filename
    # Same as base: 
    # Same as base:         if command_only:
    # Same as base:             return command_line
    # Same as base:             
    # Same as base:         os.system(command_line)
