# ----------------------------------------------------------------------
# |  
# |  Visitor.py
# |  
# |  David Brownell <db@DavidBrownell.com>
# |      2018-04-30 10:53:20
# |  
# ----------------------------------------------------------------------
# |  
# |  Copyright David Brownell 2018.
# |  Distributed under the Boost Software License, Version 1.0.
# |  (See accompanying file LICENSE_1_0.txt or copy at http://www.boost.org/LICENSE_1_0.txt)
# |  
# ----------------------------------------------------------------------
"""Contains the CommandVisitor object"""

import os
import sys

from CommonEnvironment.Interface import Interface, \
                                        abstractmethod, \
                                        staticderived, \
                                        override

# <Unused import> pylint: disable = W0614

from CommonEnvironment.Shell.Commands.All import *      # <Wildcard import> pylint: disable = W0401

# ----------------------------------------------------------------------
_script_fullpath = os.path.abspath(__file__) if "python" in sys.executable.lower() else sys.executable
_script_dir, _script_name = os.path.split(_script_fullpath)
# ----------------------------------------------------------------------

# <Missing docstring> pylint: disable = C0111

# ----------------------------------------------------------------------
class Visitor(Interface):
    """Visitor pattern that accepts Commands."""

    # ----------------------------------------------------------------------
    @staticmethod
    @abstractmethod
    def OnComment(command, *args, **kwargs):
        raise Exception("Abstract method")

    # ----------------------------------------------------------------------
    @staticmethod
    @abstractmethod
    def OnMessage(command, *args, **kwargs):
        raise Exception("Abstract method")

    # ----------------------------------------------------------------------
    @staticmethod
    @abstractmethod
    def OnCall(command, *args, **kwargs):
        raise Exception("Abstract method")

    # ----------------------------------------------------------------------
    @staticmethod
    @abstractmethod
    def OnExecute(command, *args, **kwargs):
        raise Exception("Abstract method")

    # ----------------------------------------------------------------------
    @staticmethod
    @abstractmethod
    def OnSymbolicLink(command, *args, **kwargs):
        raise Exception("Abstract method")

    # ----------------------------------------------------------------------
    @staticmethod
    @abstractmethod
    def OnPath(command, *args, **kwargs):
        raise Exception("Abstract method")

    # ----------------------------------------------------------------------
    @staticmethod
    @abstractmethod
    def OnAugmentPath(command, *args, **kwargs):
        raise Exception("Abstract method")

    # ----------------------------------------------------------------------
    @staticmethod
    @abstractmethod
    def OnSet(command, *args, **kwargs):
        raise Exception("Abstract method")

    # ----------------------------------------------------------------------
    @staticmethod
    @abstractmethod
    def OnAugment(command, *args, **kwargs):
        raise Exception("Abstract method")

    # ----------------------------------------------------------------------
    @staticmethod
    @abstractmethod
    def OnExit(command, *args, **kwargs):
        raise Exception("Abstract method")

    # ----------------------------------------------------------------------
    @staticmethod
    @abstractmethod
    def OnExitOnError(command, *args, **kwargs):
        raise Exception("Abstract method")

    # ----------------------------------------------------------------------
    @staticmethod
    @abstractmethod
    def OnRaw(command, *args, **kwargs):
        raise Exception("Abstract method")

    # ----------------------------------------------------------------------
    @staticmethod
    @abstractmethod
    def OnEchoOff(command, *args, **kwargs):
        raise Exception("Abstract method")

    # ----------------------------------------------------------------------
    @staticmethod
    @abstractmethod
    def OnCommandPrompt(command, *args, **kwargs):
        raise Exception("Abstract method")

    # ----------------------------------------------------------------------
    @staticmethod
    @abstractmethod
    def OnDelete(command, *args, **kwargs):
        raise Exception("Abstract method")

    # ----------------------------------------------------------------------
    @staticmethod
    @abstractmethod
    def OnCopy(command, *args, **kwargs):
        raise Exception("Abstract method")

    # ----------------------------------------------------------------------
    @staticmethod
    @abstractmethod
    def OnMove(command, *args, **kwargs):
        raise Exception("Abstract method")

    # ----------------------------------------------------------------------
    @staticmethod
    @abstractmethod
    def OnPersistError(command, *args, **kwargs):
        raise Exception("Abstract method")

    # ----------------------------------------------------------------------
    @staticmethod
    @abstractmethod
    def OnPushDirectory(command, *args, **kwargs):
        raise Exception("Abstract method")

    # ----------------------------------------------------------------------
    @staticmethod
    @abstractmethod
    def OnPopDirectory(command, *args, **kwargs):
        raise Exception("Abstract method")

    # ----------------------------------------------------------------------
    @classmethod
    def Accept(cls, command, *args, **kwargs):
        lookup = { Comment                  : cls.OnComment,
                   Message                  : cls.OnMessage,
                   Call                     : cls.OnCall,
                   Execute                  : cls.OnExecute,
                   SymbolicLink             : cls.OnSymbolicLink,
                   Path                     : cls.OnPath,
                   AugmentPath              : cls.OnAugmentPath,
                   Set                      : cls.OnSet,
                   Augment                  : cls.OnAugment,
                   Exit                     : cls.OnExit,
                   ExitOnError              : cls.OnExitOnError,
                   Raw                      : cls.OnRaw,
                   EchoOff                  : cls.OnEchoOff,
                   CommandPrompt            : cls.OnCommandPrompt,
                   Delete                   : cls.OnDelete,
                   Copy                     : cls.OnCopy,
                   Move                     : cls.OnMove,
                   PersistError             : cls.OnPersistError,
                   PushDirectory            : cls.OnPushDirectory,
                   PopDirectory             : cls.OnPopDirectory,
                 }

        typ = type(command)

        if typ not in lookup:
            raise Exception("'{}' was not expected".format(typ))

        value = lookup[typ]

        if isinstance(value, tuple):
            command = value[0](command)
            value = value[1]

        return value(command, *args, **kwargs)

# ----------------------------------------------------------------------
# |  
# |  Public Methods
# |  
# ----------------------------------------------------------------------
# <Too many arguments> pylint: disable = R0913
# <Too many local variables> pylint: disable = R0914

def CreateSimpleVisitor( on_comment_func=None,          # def Func(command, *args, **kwargs)
                         on_message_func=None,          # def Func(command, *args, **kwargs)
                         on_call_func=None,             # def Func(command, *args, **kwargs)
                         on_execute_func=None,          # def Func(command, *args, **kwargs)
                         on_symbolic_link_func=None,    # def Func(command, *args, **kwargs)
                         on_path_func=None,             # def Func(command, *args, **kwargs)
                         on_augment_path_func=None,     # def Func(command, *args, **kwargs)
                         on_set_func=None,              # def Func(command, *args, **kwargs)
                         on_augment_func=None,          # def Func(command, *args, **kwargs)
                         on_exit_func=None,             # def Func(command, *args, **kwargs)
                         on_exit_on_error_func=None,    # def Func(command, *args, **kwargs)
                         on_raw_func=None,              # def Func(command, *args, **kwargs)
                         on_echo_off_func=None,         # def Func(command, *args, **kwargs)
                         on_command_prompt_func=None,   # def Func(command, *args, **kwargs)
                         on_delete_func=None,           # def Func(command, *args, **kwargs)
                         on_copy_func=None,             # def Func(command, *args, **kwargs)
                         on_move_func=None,             # def Func(command, *args, **kwargs)
                         on_persist_error_func=None,    # def Func(command, *args, **kwargs)
                         on_push_directory_func=None,   # def Func(command, *args, **kwargs)
                         on_pop_directory_func=None,    # def Func(command, *args, **kwargs)
                         on_default_func=None,          # def Func(command, *args, **kwargs)
                       ):
    """Creates a CommandVisitor instance implemented in terms of the non-None function arguments."""

    on_default_func = on_default_func or (lambda command, *args, **kwargs: None)

    on_comment_func = on_comment_func or on_default_func
    on_message_func = on_message_func or on_default_func
    on_call_func = on_call_func or on_default_func
    on_execute_func = on_execute_func or on_default_func
    on_symbolic_link_func = on_symbolic_link_func or on_default_func
    on_path_func = on_path_func or on_default_func
    on_augment_path_func = on_augment_path_func or on_default_func
    on_set_func = on_set_func or on_default_func
    on_augment_func = on_augment_func or on_default_func
    on_exit_func = on_exit_func or on_default_func
    on_exit_on_error_func = on_exit_on_error_func or on_default_func
    on_raw_func = on_raw_func or on_default_func
    on_echo_off_func = on_echo_off_func or on_default_func
    on_command_prompt_func = on_command_prompt_func or on_default_func
    on_delete_func = on_delete_func or on_default_func
    on_copy_func = on_copy_func or on_default_func
    on_move_func = on_move_func or on_default_func
    on_persist_error_func = on_persist_error_func or on_default_func
    on_push_directory_func = on_push_directory_func or on_default_func
    on_pop_directory_func = on_pop_directory_func or on_default_func
    
    # ----------------------------------------------------------------------
    @staticderived
    class SimpleVisitor(Visitor):
        # ----------------------------------------------------------------------
        @staticmethod
        @override
        def OnComment(command, *args, **kwargs):
            return on_comment_func(command, *args, **kwargs)
    
        # ----------------------------------------------------------------------
        @staticmethod
        @override
        def OnMessage(command, *args, **kwargs):
            return on_message_func(command, *args, **kwargs)
    
        # ----------------------------------------------------------------------
        @staticmethod
        @override
        def OnCall(command, *args, **kwargs):
            return on_call_func(command, *args, **kwargs)
    
        # ----------------------------------------------------------------------
        @staticmethod
        @override
        def OnExecute(command, *args, **kwargs):
            return on_execute_func(command, *args, **kwargs)
    
        # ----------------------------------------------------------------------
        @staticmethod
        @override
        def OnSymbolicLink(command, *args, **kwargs):
            return on_symbolic_link_func(command, *args, **kwargs)
    
        # ----------------------------------------------------------------------
        @staticmethod
        @override
        def OnPath(command, *args, **kwargs):
            return on_path_func(command, *args, **kwargs)
    
        # ----------------------------------------------------------------------
        @staticmethod
        @override
        def OnAugmentPath(command, *args, **kwargs):
            return on_augment_path_func(command, *args, **kwargs)
    
        # ----------------------------------------------------------------------
        @staticmethod
        @override
        def OnSet(command, *args, **kwargs):
            return on_set_func(command, *args, **kwargs)
    
        # ----------------------------------------------------------------------
        @staticmethod
        @override
        def OnAugment(command, *args, **kwargs):
            return on_augment_func(command, *args, **kwargs)
    
        # ----------------------------------------------------------------------
        @staticmethod
        @override
        def OnExit(command, *args, **kwargs):
            return on_exit_func(command, *args, **kwargs)
    
        # ----------------------------------------------------------------------
        @staticmethod
        @override
        def OnExitOnError(command, *args, **kwargs):
            return on_exit_on_error_func(command, *args, **kwargs)
    
        # ----------------------------------------------------------------------
        @staticmethod
        @override
        def OnRaw(command, *args, **kwargs):
            return on_raw_func(command, *args, **kwargs)
    
        # ----------------------------------------------------------------------
        @staticmethod
        @override
        def OnEchoOff(command, *args, **kwargs):
            return on_echo_off_func(command, *args, **kwargs)
    
        # ----------------------------------------------------------------------
        @staticmethod
        @override
        def OnCommandPrompt(command, *args, **kwargs):
            return on_command_prompt_func(command, *args, **kwargs)
    
        # ----------------------------------------------------------------------
        @staticmethod
        @override
        def OnDelete(command, *args, **kwargs):
            return on_delete_func(command, *args, **kwargs)
    
        # ----------------------------------------------------------------------
        @staticmethod
        @override
        def OnCopy(command, *args, **kwargs):
            return on_copy_func(command, *args, **kwargs)
    
        # ----------------------------------------------------------------------
        @staticmethod
        @override
        def OnMove(command, *args, **kwargs):
            return on_move_func(command, *args, **kwargs)

        # ----------------------------------------------------------------------
        @staticmethod
        @override
        def OnPersistError(command, *args, **kwargs):
            return on_persist_error_func(command, *args, **kwargs)

        # ----------------------------------------------------------------------
        @staticmethod
        @override
        def OnPushDirectory(command, *args, **kwargs):
            return on_push_directory_func(command, *args, **kwargs)

        # ----------------------------------------------------------------------
        @staticmethod
        @override
        def OnPopDirectory(command, *args, **kwargs):
            return on_pop_directory_func(command, *args, **kwargs)

    # ----------------------------------------------------------------------

    return SimpleVisitor
    