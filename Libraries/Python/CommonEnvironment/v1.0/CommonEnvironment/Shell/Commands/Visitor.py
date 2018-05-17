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

from CommonEnvironment.Interface import *
from CommonEnvironment.Shell.Commands import *

# ----------------------------------------------------------------------
_script_fullpath = os.path.abspath(__file__) if "python" in sys.executable.lower() else sys.executable
_script_dir, _script_name = os.path.split(_script_fullpath)
# ----------------------------------------------------------------------

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
def CreateSimpleVisitor( onCommentFunc=None,            # def Func(command, *args, **kwargs)
                         onMessageFunc=None,            # def Func(command, *args, **kwargs)
                         onCallFunc=None,               # def Func(command, *args, **kwargs)
                         onExecuteFunc=None,            # def Func(command, *args, **kwargs)
                         onSymbolicLinkFunc=None,       # def Func(command, *args, **kwargs)
                         onPathFunc=None,               # def Func(command, *args, **kwargs)
                         onAugmentPathFunc=None,        # def Func(command, *args, **kwargs)
                         onSetFunc=None,                # def Func(command, *args, **kwargs)
                         onAugmentFunc=None,            # def Func(command, *args, **kwargs)
                         onExitFunc=None,               # def Func(command, *args, **kwargs)
                         onExitOnErrorFunc=None,        # def Func(command, *args, **kwargs)
                         onRawFunc=None,                # def Func(command, *args, **kwargs)
                         onEchoOffFunc=None,            # def Func(command, *args, **kwargs)
                         onCommandPromptFunc=None,      # def Func(command, *args, **kwargs)
                         onDeleteFunc=None,             # def Func(command, *args, **kwargs)
                         onCopyFunc=None,               # def Func(command, *args, **kwargs)
                         onMoveFunc=None,               # def Func(command, *args, **kwargs)
                         onDefaultFunc=None,            # def Func(command, *args, **kwargs)
                       ):
    """Creates a CommandVisitor instance implemented in terms of the non-None function arguments."""

    onDefaultFunc = onDefaultFunc or (lambda command, *args, **kwargs: None)

    onCommentFunc = onCommentFunc or onDefaultFunc
    onMessageFunc = onMessageFunc or onDefaultFunc
    onCallFunc = onCallFunc or onDefaultFunc
    onExecuteFunc = onExecuteFunc or onDefaultFunc
    onSymbolicLinkFunc = onSymbolicLinkFunc or onDefaultFunc
    onPathFunc = onPathFunc or onDefaultFunc
    onAugmentPathFunc = onAugmentPathFunc or onDefaultFunc
    onSetFunc = onSetFunc or onDefaultFunc
    onAugmentFunc = onAugmentFunc or onDefaultFunc
    onExitFunc = onExitFunc or onDefaultFunc
    onExitOnErrorFunc = onExitOnErrorFunc or onDefaultFunc
    onRawFunc = onRawFunc or onDefaultFunc
    onEchoOffFunc = onEchoOffFunc or onDefaultFunc
    onCommandPromptFunc = onCommandPromptFunc or onDefaultFunc
    onDeleteFunc = onDeleteFunc or onDefaultFunc
    onCopyFunc = onCopyFunc or onDefaultFunc
    onMoveFunc = onMoveFunc or onDefaultFunc
    
    # ----------------------------------------------------------------------
    @staticderived
    class SimpleVisitor(Visitor):
        # ----------------------------------------------------------------------
        @staticmethod
        def OnComment(command, *args, **kwargs):
            return onCommentFunc(command, *args, **kwargs)
    
        # ----------------------------------------------------------------------
        @staticmethod
        def OnMessage(command, *args, **kwargs):
            return onMessageFunc(command, *args, **kwargs)
    
        # ----------------------------------------------------------------------
        @staticmethod
        def OnCall(command, *args, **kwargs):
            return onCallFunc(command, *args, **kwargs)
    
        # ----------------------------------------------------------------------
        @staticmethod
        def OnExecute(command, *args, **kwargs):
            return onExecuteFunc(command, *args, **kwargs)
    
        # ----------------------------------------------------------------------
        @staticmethod
        def OnSymbolicLink(command, *args, **kwargs):
            return onSymbolicLinkFunc(command, *args, **kwargs)
    
        # ----------------------------------------------------------------------
        @staticmethod
        def OnPath(command, *args, **kwargs):
            return onPathFunc(command, *args, **kwargs)
    
        # ----------------------------------------------------------------------
        @staticmethod
        def OnAugmentPath(command, *args, **kwargs):
            return onAugmentPathFunc(command, *args, **kwargs)
    
        # ----------------------------------------------------------------------
        @staticmethod
        def OnSet(command, *args, **kwargs):
            return onSetFunc(command, *args, **kwargs)
    
        # ----------------------------------------------------------------------
        @staticmethod
        def OnAugment(command, *args, **kwargs):
            return onAugmentFunc(command, *args, **kwargs)
    
        # ----------------------------------------------------------------------
        @staticmethod
        def OnExit(command, *args, **kwargs):
            return onExitFunc(command, *args, **kwargs)
    
        # ----------------------------------------------------------------------
        @staticmethod
        def OnExitOnError(command, *args, **kwargs):
            return onExitOnErrorFunc(command, *args, **kwargs)
    
        # ----------------------------------------------------------------------
        @staticmethod
        def OnRaw(command, *args, **kwargs):
            return onRawFunc(command, *args, **kwargs)
    
        # ----------------------------------------------------------------------
        @staticmethod
        def OnEchoOff(command, *args, **kwargs):
            return onEchoOffFunc(command, *args, **kwargs)
    
        # ----------------------------------------------------------------------
        @staticmethod
        def OnCommandPrompt(command, *args, **kwargs):
            return onCommandPromptFunc(command, *args, **kwargs)
    
        # ----------------------------------------------------------------------
        @staticmethod
        def OnDelete(command, *args, **kwargs):
            return onDeleteFunc(command, *args, **kwargs)
    
        # ----------------------------------------------------------------------
        @staticmethod
        def OnCopy(command, *args, **kwargs):
            return onCopyFunc(command, *args, **kwargs)
    
        # ----------------------------------------------------------------------
        @staticmethod
        def OnMove(command, *args, **kwargs):
            return onMoveFunc(command, *args, **kwargs)

    # ----------------------------------------------------------------------

    return SimpleVisitor

