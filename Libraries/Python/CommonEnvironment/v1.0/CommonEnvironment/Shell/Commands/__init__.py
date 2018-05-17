# ----------------------------------------------------------------------
# |  
# |  __init__.py
# |  
# |  David Brownell <db@DavidBrownell.com>
# |      2018-04-30 19:31:25
# |  
# ----------------------------------------------------------------------
# |  
# |  Copyright David Brownell 2018.
# |  Distributed under the Boost Software License, Version 1.0.
# |  (See accompanying file LICENSE_1_0.txt or copy at http://www.boost.org/LICENSE_1_0.txt)
# |  
# ----------------------------------------------------------------------
"""Contains generic commands applicable to different shells."""

import itertools
import os
import sys

import CommonEnvironment

# ----------------------------------------------------------------------
_script_fullpath = os.path.abspath(__file__) if "python" in sys.executable.lower() else sys.executable
_script_dir, _script_name = os.path.split(_script_fullpath)
# ----------------------------------------------------------------------

# ----------------------------------------------------------------------
class Comment(object):
    """A comment within a generated script"""
    def __init__(self, value):
        self.Value                          = value

    # ----------------------------------------------------------------------
    def __str__(self):
        return CommonEnvironment.ObjectStrImpl(self)

# ----------------------------------------------------------------------
class Message(object):
    """A (potentially) multiline message displayed within a generated script"""
    def __init__(self, value):
        self.Value                          = value

    # ----------------------------------------------------------------------
    def __str__(self):
        return CommonEnvironment.ObjectStrImpl(self)

# ----------------------------------------------------------------------
class Call(object):
    """A command invoked within a generated script"""
    def __init__(self, command_line):
        self.CommandLine                    = command_line

    # ----------------------------------------------------------------------
    def __str__(self):
        return CommonEnvironment.ObjectStrImpl(self)

# ----------------------------------------------------------------------
class Execute(object):
    """A command invoked within a generated script"""
    def __init__(self, command_line):
        self.CommandLine                    = command_line

    # ----------------------------------------------------------------------
    def __str__(self):
        return CommonEnvironment.ObjectStrImpl(self)

# ----------------------------------------------------------------------
class SymbolicLink(object):
    """A symbolic link created within a generated script"""
    def __init__( self, 
                  link_filename, 
                  target, 
                  is_dir=None,
                  remove_existing=True,
                ):
        self.LinkFilename                   = link_filename
        self.Target                         = target
        self.IsDir                          = is_dir if is_dir is not None else os.path.isdir(target)
        self.RemoveExisting                 = remove_existing

    # ----------------------------------------------------------------------
    def __str__(self):
        return CommonEnvironment.ObjectStrImpl(self)

# ----------------------------------------------------------------------
class Set(object):
    """Sets an environment variable within a generated script"""
    def __init__(self, name, value_or_values, update_memory=False):
        self.Name                           = name
        self.Values                         = value_or_values if isinstance(value_or_values, list) else [ value_or_values, ] if value_or_values is not None else None

        if update_memory:
            if self.Values is None:
                os.environ.pop(self.Name, None)
            else:
                from CommonEnvironment.Shell.Commands.All import CurrentShell

                os.environ[self.Name] = CurrentShell.EnvironmentVariableDelimiter.join(self.Values)

    # ----------------------------------------------------------------------
    def __str__(self):
        return CommonEnvironment.ObjectStrImpl(self)

# ----------------------------------------------------------------------
class Augment(object):
    """Adds items to an environment variable within a generated script if they don't already exist"""
    def __init__(self, name, value_or_values, update_memory=False):
        if not value_or_values:
            raise Exception("'value_or_values' must not be None")

        self.Name                           = name
        self.Values                         = value_or_values if isinstance(value_or_values, list) else [ value_or_values, ]

        if update_memory:
            from CommonEnvironment.Shell.Commands.All import CurrentShell

            existing_values = list(CurrentShell.EnumEnvironmentVariable(self.Name))
        
            for value in self.Values:
                new_values = []
        
                if value not in existing_values:
                    new_values.append(value)
        
            os.environ[self.Name] = CurrentShell.EnvironmentVariableDelimiter.join(itertools.chain(new_values, existing_values))

    # ----------------------------------------------------------------------
    def __str__(self):
        return CommonEnvironment.ObjectStrImpl(self)

# ----------------------------------------------------------------------
class Path(Set):
    """Adds items to the system path within a generated script"""
    def __init__(self, value_or_values, update_memory=False):
        super(Path, self).__init__("PATH", value_or_values, update_memory=update_memory)

    # ----------------------------------------------------------------------
    def __str__(self):
        return CommonEnvironment.ObjectStrImpl(self)

# ----------------------------------------------------------------------
class AugmentPath(Augment):
    """Adds items to the system path within a generated script if they don't already exist"""
    def __init__(self, value_or_values, update_memory=False):
        super(AugmentPath, self).__init__("PATH", value_or_values, update_memory=update_memory)

    # ----------------------------------------------------------------------
    def __str__(self):
        return CommonEnvironment.ObjectStrImpl(self)

# ----------------------------------------------------------------------
class Exit(object):
    """Exits from a generated script"""
    def __init__(self, pause_on_success=False, pause_on_error=False, return_code=None):
        self.PauseOnSuccess                 = pause_on_success
        self.PauseOnError                   = pause_on_error
        self.ReturnCode                     = return_code

    # ----------------------------------------------------------------------
    def __str__(self):
        return CommonEnvironment.ObjectStrImpl(self)

# ----------------------------------------------------------------------
class ExitOnError(object):
    """Exists from a generated script if an error was encountered"""
    def __init__(self, return_code=None):
        self.ReturnCode                     = return_code

    # ----------------------------------------------------------------------
    def __str__(self):
        return CommonEnvironment.ObjectStrImpl(self)

# ----------------------------------------------------------------------
class Raw(object):
    """Writes a raw string to the generated script"""
    def __init__(self, value):
        self.Value                          = value

    # ----------------------------------------------------------------------
    def __str__(self):
        return CommonEnvironment.ObjectStrImpl(self)

# ----------------------------------------------------------------------
class EchoOff(object):
    """Disabled command echoing in a generated script"""
    def __init__(self):
        pass

    # ----------------------------------------------------------------------
    def __str__(self):
        return CommonEnvironment.ObjectStrImpl(self)

# ----------------------------------------------------------------------
class CommandPrompt(object):
    """Set the command prompt to a valid within a generated script"""
    def __init__(self, prompt):
        self.Prompt                         = prompt

    # ----------------------------------------------------------------------
    def __str__(self):
        return CommonEnvironment.ObjectStrImpl(self)

# ----------------------------------------------------------------------
class Delete(object):
    """Deletes a file or directory within a generated script"""
    def __init__(self, filename_or_directory, is_dir=None):
        self.FilenameOrDirectory            = filename_or_directory
        self.IsDir                          = is_dir

    # ----------------------------------------------------------------------
    def __str__(self):
        return CommonEnvironment.ObjectStrImpl(self)

# ----------------------------------------------------------------------
class Copy(object):
    """Copies a file or directory within a generated script"""
    def __init__(self, source, dest, is_dir=None):
        self.Source                         = source
        self.Dest                           = dest
        self.IsDir                          = is_dir

    # ----------------------------------------------------------------------
    def __str__(self):
        return CommonEnvironment.ObjectStrImpl(self)

# ----------------------------------------------------------------------
class Move(object):
    """Moves a file or directory within a generated script"""
    def __init__(self, source, dest, is_dir=None):
        self.Source                         = source
        self.Dest                           = dest
        self.IsDir                          = is_dir

    # ----------------------------------------------------------------------
    def __str__(self):
        return CommonEnvironment.ObjectStrImpl(self)
