# ----------------------------------------------------------------------
# |  
# |  __init__.py
# |  
# |  David Brownell <db@DavidBrownell.com>
# |      2018-04-30 08:52:20
# |  
# ----------------------------------------------------------------------
# |  
# |  Copyright David Brownell 2018.
# |  Distributed under the Boost Software License, Version 1.0.
# |  (See accompanying file LICENSE_1_0.txt or copy at http://www.boost.org/LICENSE_1_0.txt)
# |  
# ----------------------------------------------------------------------
"""Contains shell-related tool and functionality."""

import os
import stat
import sys
import tempfile
import textwrap

from CommonEnvironment.Interface import Interface, \
                                        abstractproperty, \
                                        abstractmethod, \
                                        extensionmethod

# ----------------------------------------------------------------------
_script_fullpath = os.path.abspath(__file__) if "python" in sys.executable.lower() else sys.executable
_script_dir, _script_name = os.path.split(_script_fullpath)
# ----------------------------------------------------------------------

# <Assigning to function call which only returns None> pylint: disable = E1128
# <Using a conditional statement with a constant value> pylint: disable = W0125

# ----------------------------------------------------------------------
class Shell(Interface):
    """
    Contains abstractions for functionality that is common across multiple operating systems.

    While Python can provide a great deal of abstraction, functionality here is generally
    used in bootstrapping python processes.
    """

    # ----------------------------------------------------------------------
    # |  
    # |  Public Properties
    # |  
    # ----------------------------------------------------------------------
    @abstractproperty
    def Name(self):
        """Name of the Shell"""
        raise Exception("Abstract property")

    @abstractproperty
    def CategoryName(self):
        """\
        Name is the specific name of the OS, can CategoryName is its broad category.

        For example:
            Operating System    Name            Category
            ----------------    ----            --------
            Ubuntu              Ubunutu         Linux
            Windows             Windows         Windows
        """
        raise Exception("Abstract property")

    @abstractproperty
    def ScriptExtension(self):
        """File extension used for scripts (e.g. ".cmd" or ".sh")"""
        raise Exception("Abstract property")

    @abstractproperty
    def ExecutableExtension(self):
        """File extension used for executables (if any) (e.g. ".exe")"""
        raise Exception("Abstract property")

    @abstractproperty
    def CompressionExtensions(self):
        """File extension used to indicate compressed files."""
        raise Exception("Abstract property")

    @abstractproperty
    def AllArgumentsScriptVariable(self):
        """Convention used to indicate all variables should be passed to a script. (e.g. "%*" or "$@")"""
        raise Exception("Abstract property")

    @abstractproperty
    def EnvironmentVariableDelimiter(self):
        """Delimiter to separate environment variables (e.g. ";" or ":")"""
        raise Exception("Abstract property")

    @abstractproperty
    def HasCaseSensitiveFileSystem(self):
        """True if the file system is case sensitive."""
        raise Exception("Abstract property")

    @abstractproperty
    def Architecture(self):
        """Architecture value (e.g. "x64" or "x86")"""
        raise Exception("Abstract property")

    @abstractproperty
    def UserDirectory(self):
        """Directory associated with the active user account."""
        raise Exception("Abstract property")

    @abstractproperty
    def TempDirectory(self):
        """Directory used to store temp files."""
        raise Exception("Abstract property")

    @abstractproperty
    def CommandVisitor(self):
        """CommandVisitor used to process commands for the derived object."""
        raise Exception("Abstract property")

    # ----------------------------------------------------------------------
    # |  
    # |  Public Methods
    # |  
    # ----------------------------------------------------------------------
    @classmethod
    def DecorateObjectWithCommands(cls):
        """
        Creates a Commands member that contains all Command types as a convenience.

        This is not defined inline, as it relies on the Commands module, which in turn
        relies on this one.
        """

        from CommonEnvironment.Shell.Commands.All import ALL_COMMANDS
        
        # ----------------------------------------------------------------------
        class ShellCommandsObject(object):
            pass

        # ----------------------------------------------------------------------

        commands = ShellCommandsObject()

        for command in ALL_COMMANDS:
            setattr(commands, command.__name__, command)

        cls.Commands = commands
        return cls

    # ----------------------------------------------------------------------
    @staticmethod
    @abstractmethod
    def IsActive(platform_name):
        """Return True if the environment is active."""
        raise Exception("Abstract method")

    # ----------------------------------------------------------------------
    @staticmethod
    @abstractmethod
    def RemoveDir(path):
        """Removes a directory in the most efficient way possible"""
        raise Exception("Abstract method")

    # ----------------------------------------------------------------------
    @classmethod
    def GenerateCommands( cls, 
                          command_or_commands,
                          suppress_prefix=False,
                          suppress_suffix=False,
                        ):
        """Generates Shell-specific commands from a list of generic commands."""

        if command_or_commands is None:
            return ''

        if not isinstance(command_or_commands, list):
            command_or_commands = [ command_or_commands, ]

        results = []

        if not suppress_prefix:
            prefix = cls._GeneratePrefixCommand()
            if prefix:
                results.append(prefix)

        visitor = cls.CommandVisitor

        for command in command_or_commands:
            result = visitor.Accept(command)            # <Class '<name>' has no '<attr>' member> pylint: disable = E1103
            if result:
                results.append(result)

        if not suppress_suffix:
            suffix = cls._GenerateSuffixCommand()
            if suffix:
                results.append(suffix)

        return '\n'.join(results)

    # ----------------------------------------------------------------------
    @classmethod
    def ExecuteCommands( cls, 
                         command_or_commands,
                         output_stream,
                         environment=None,
                       ):
        """\
        Creates a temporary script file, writes the commands to that file,
        and then executes it. Returns the result and output generated during
        execution.
        """
        
        from CommonEnvironment.CallOnExit import CallOnExit
        from CommonEnvironment import FileSystem
        from CommonEnvironment import Process

        temp_filename = cls.CreateTempFilename(cls.ScriptExtension)
        with open(temp_filename, 'w') as f:
            f.write(cls.GenerateCommands(command_or_commands))
        
        with CallOnExit(lambda: FileSystem.RemoveFile(temp_filename)):
            cls.MakeFileExecutable(temp_filename)
            
            return Process.Execute( temp_filename,
                                    output_stream,
                                    environment=environment,
                                  )

    # ----------------------------------------------------------------------
    @classmethod
    def EnumEnvironmentVariable(cls, name):
        """yields all values within an environment variable as delimited by EnvironmentVariableDelimiter."""
        value = os.getenv(name)
        if not value:
            return

        for item in value.split(cls.EnvironmentVariableDelimiter):
            item = item.strip()
            if item:
                yield item

    # ----------------------------------------------------------------------
    @classmethod
    def CreateScriptName(cls, name):
        ext = cls.ScriptExtension
        if ext:
            name += ext

        return name

    # ----------------------------------------------------------------------
    @classmethod
    def CreateExecutableName(cls, name):
        ext = cls.ExecutableExtension
        if ext:
            name += ext

        return name

    # ----------------------------------------------------------------------
    @staticmethod
    def CreateTempFilename(suffix=''):
        filename_handle, filename = tempfile.mkstemp(suffix=suffix)
        
        os.close(filename_handle)
        os.remove(filename)

        return filename

    # ----------------------------------------------------------------------
    @classmethod
    def CreateTempDirectory(cls, suffix=''):
        folder = cls.CreateTempFilename(suffix)
        os.makedirs(folder)

        return folder

    # ----------------------------------------------------------------------
    @staticmethod
    def MakeFileExecutable(filename):
        assert os.path.isfile(filename), filename
        os.chmod(filename, stat.S_IXUSR | stat.S_IWUSR | stat.S_IRUSR)

    # ----------------------------------------------------------------------
    @classmethod
    def CreateDataFilename( cls,
                            application_name,
                            suffix=".bin",
                          ):
        return os.path.join( cls.UserDirectory,
                             "{}{}".format(application_name.replace(' ', '_'), suffix),
                           )

    # ----------------------------------------------------------------------
    @classmethod
    def CreateSymLink(cls, link_filename, target, is_dir=None):
        """\
        Creating a symbolic link on some systems is cumbersome. This method handles
        the complexity to ensure that it works on all systems, but may be overkill
        for those systems where it is a straighforward process.
        """

        from CommonEnvironment.Shell.Commands import SymbolicLink

        result, output = cls.ExecuteCommands( SymbolicLink(link_filename, target, is_dir),
                                              output_stream=None,
                                            )
        if result != 0:
            raise Exception(textwrap.dedent(
                """\
                An error was encountered when generating a symbolic link:

                Link Filename:              {}
                Target:                     {}
                IsDir:                      {}

                Result:                     {}
                Output:
                {}
                """).format( link_filename,
                             target,
                             is_dir,
                             result,
                             output,
                           ))

    # ----------------------------------------------------------------------
    @staticmethod
    @extensionmethod
    def IsSymLink(filename):
        return os.path.islink(filename)

    # ----------------------------------------------------------------------
    @staticmethod
    @extensionmethod
    def ResolveSymLink(filename):
        return os.path.realpath(filename)

    # ----------------------------------------------------------------------
    @staticmethod
    @extensionmethod
    def DeleteSymLink(filename, command_only=False):
        assert not command_only, "'command_only' is not supported"
        os.remove(filename)
    
    # ----------------------------------------------------------------------
    # ----------------------------------------------------------------------
    # ----------------------------------------------------------------------
    @staticmethod
    @extensionmethod
    def _GeneratePrefixCommand():
        return

    # ----------------------------------------------------------------------
    @staticmethod
    @extensionmethod
    def _GenerateSuffixCommand():
        return
