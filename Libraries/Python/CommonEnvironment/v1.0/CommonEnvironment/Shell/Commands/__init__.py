# ----------------------------------------------------------------------
# |
# |  __init__.py
# |
# |  David Brownell <db@DavidBrownell.com>
# |      2018-04-30 19:31:25
# |
# ----------------------------------------------------------------------
# |
# |  Copyright David Brownell 2018-20.
# |  Distributed under the Boost Software License, Version 1.0.
# |  (See accompanying file LICENSE_1_0.txt or copy at http://www.boost.org/LICENSE_1_0.txt)
# |
# ----------------------------------------------------------------------
"""Contains generic commands applicable to different shells."""

import itertools
import os

import CommonEnvironment

# ----------------------------------------------------------------------
_script_fullpath                            = CommonEnvironment.ThisFullpath()
_script_dir, _script_name                   = os.path.split(_script_fullpath)
# ----------------------------------------------------------------------

# <Too few public methods> pylint: disable = R0903

# ----------------------------------------------------------------------
class Comment(object):
    """A comment within a generated script"""

    def __init__(self, value):
        self.Value                          = value

    # ----------------------------------------------------------------------
    def __repr__(self):
        return CommonEnvironment.ObjectReprImpl(self)


# ----------------------------------------------------------------------
class Message(object):
    """A (potentially) multiline message displayed within a generated script"""

    def __init__(self, value):
        self.Value                          = value

    # ----------------------------------------------------------------------
    def __repr__(self):
        return CommonEnvironment.ObjectReprImpl(self)


# ----------------------------------------------------------------------
class Call(object):
    """A command invoked within a generated script"""

    def __init__(
        self,
        command_line,
        exit_on_error=True,
    ):
        self.CommandLine                    = command_line
        self.ExitOnError                    = exit_on_error

    # ----------------------------------------------------------------------
    def __repr__(self):
        return CommonEnvironment.ObjectReprImpl(self)


# ----------------------------------------------------------------------
class Execute(object):
    """A command invoked within a generated script"""

    def __init__(
        self,
        command_line,
        exit_on_error=True,
    ):
        self.CommandLine                    = command_line
        self.ExitOnError                    = exit_on_error

    # ----------------------------------------------------------------------
    def __repr__(self):
        return CommonEnvironment.ObjectReprImpl(self)


# ----------------------------------------------------------------------
class SymbolicLink(object):
    """A symbolic link created within a generated script"""

    def __init__(
        self,
        link_filename,
        target,
        is_dir=None,
        remove_existing=True,
        relative_path=True,
    ):
        self.LinkFilename                   = link_filename
        self.Target                         = target
        self.IsDir                          = is_dir if is_dir is not None else os.path.isdir(target)
        self.RemoveExisting                 = remove_existing
        self.RelativePath                   = relative_path

    # ----------------------------------------------------------------------
    def __repr__(self):
        return CommonEnvironment.ObjectReprImpl(self)


# ----------------------------------------------------------------------
class Set(object):
    """Sets an environment variable within a generated script"""

    def __init__(self, name, value_or_values):
        self.Name                           = name
        self.Values                         = value_or_values if isinstance(value_or_values, list) else [value_or_values] if value_or_values is not None else None

    # ----------------------------------------------------------------------
    def __repr__(self):
        return CommonEnvironment.ObjectReprImpl(self)


# ----------------------------------------------------------------------
class Augment(object):
    """Adds items to an environment variable within a generated script if they don't already exist"""

    def __init__(
        self,
        name,
        value_or_values,
        is_space_delimited_string=False,
        append_values=False,
    ):
        if not isinstance(value_or_values, list):
            value_or_values = [value_or_values]

        self.Name                           = name
        self.Values                         = value_or_values
        self.IsSpaceDelimitedString         = is_space_delimited_string
        self.AppendValues                   = append_values

    # ----------------------------------------------------------------------
    def __repr__(self):
        return CommonEnvironment.ObjectReprImpl(self)


# ----------------------------------------------------------------------
class Path(Set):
    """Adds items to the system path within a generated script"""

    def __init__(self, value_or_values):
        super(Path, self).__init__("PATH", value_or_values)

    # ----------------------------------------------------------------------
    def __repr__(self):
        return CommonEnvironment.ObjectReprImpl(self)


# ----------------------------------------------------------------------
class AugmentPath(Augment):
    """Adds items to the system path within a generated script if they don't already exist"""

    def __init__(self, value_or_values):
        super(AugmentPath, self).__init__("PATH", value_or_values)

    # ----------------------------------------------------------------------
    def __repr__(self):
        return CommonEnvironment.ObjectReprImpl(self)


# ----------------------------------------------------------------------
class Exit(object):
    """Exits from a generated script"""

    def __init__(
        self,
        pause_on_success=False,
        pause_on_error=False,
        return_code=None,
    ):
        self.PauseOnSuccess                 = pause_on_success
        self.PauseOnError                   = pause_on_error
        self.ReturnCode                     = return_code

    # ----------------------------------------------------------------------
    def __repr__(self):
        return CommonEnvironment.ObjectReprImpl(self)


# ----------------------------------------------------------------------
class ExitOnError(object):
    """Exists from a generated script if an error was encountered"""

    def __init__(
        self,
        return_code=None,
        variable_name=None,
    ):
        self.ReturnCode                     = return_code
        self.VariableName                   = variable_name

    # ----------------------------------------------------------------------
    def __repr__(self):
        return CommonEnvironment.ObjectReprImpl(self)


# ----------------------------------------------------------------------
class Raw(object):
    """Writes a raw string to the generated script"""

    def __init__(self, value):
        self.Value                          = value

    # ----------------------------------------------------------------------
    def __repr__(self):
        return CommonEnvironment.ObjectReprImpl(self)


# ----------------------------------------------------------------------
class EchoOff(object):
    """Disabled command echoing in a generated script"""

    def __init__(self):
        pass

    # ----------------------------------------------------------------------
    def __repr__(self):
        return CommonEnvironment.ObjectReprImpl(self)


# ----------------------------------------------------------------------
class CommandPrompt(object):
    """Set the command prompt to a valid within a generated script"""

    def __init__(self, prompt):
        self.Prompt                         = prompt

    # ----------------------------------------------------------------------
    def __repr__(self):
        return CommonEnvironment.ObjectReprImpl(self)


# ----------------------------------------------------------------------
class Delete(object):
    """Deletes a file or directory within a generated script"""

    def __init__(
        self,
        filename_or_directory,
        is_dir=None,
    ):
        self.FilenameOrDirectory            = filename_or_directory
        self.IsDir                          = is_dir

    # ----------------------------------------------------------------------
    def __repr__(self):
        return CommonEnvironment.ObjectReprImpl(self)


# ----------------------------------------------------------------------
class Copy(object):
    """Copies a file or directory within a generated script"""

    def __init__(
        self,
        source,
        dest,
        is_dir=None,
    ):
        self.Source                         = source
        self.Dest                           = dest
        self.IsDir                          = is_dir

    # ----------------------------------------------------------------------
    def __repr__(self):
        return CommonEnvironment.ObjectReprImpl(self)


# ----------------------------------------------------------------------
class Move(object):
    """Moves a file or directory within a generated script"""

    def __init__(
        self,
        source,
        dest,
        is_dir=None,
    ):
        self.Source                         = source
        self.Dest                           = dest
        self.IsDir                          = is_dir

    # ----------------------------------------------------------------------
    def __repr__(self):
        return CommonEnvironment.ObjectReprImpl(self)


# ----------------------------------------------------------------------
class PersistError(object):
    """Persist any errors generated by the previous command"""

    def __init__(self, var_name):
        self.VariableName                   = var_name

    # ----------------------------------------------------------------------
    def __repr__(self):
        return CommonEnvironment.ObjectReprImpl(self)


# ----------------------------------------------------------------------
class PushDirectory(object):
    """Pushes a directory onto the directory stack"""

    def __init__(self, directory_or_none):
        self.Directory                      = directory_or_none

    # ----------------------------------------------------------------------
    def __repr__(self):
        return CommonEnvironment.ObjectReprImpl(self)


# ----------------------------------------------------------------------
class PopDirectory(object):
    """Pops a directory from the directory stack"""

    def __init__(self):
        pass

    # ----------------------------------------------------------------------
    def __repr__(self):
        return CommonEnvironment.ObjectReprImpl(self)
