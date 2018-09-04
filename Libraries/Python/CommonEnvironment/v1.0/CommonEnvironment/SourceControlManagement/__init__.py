# ----------------------------------------------------------------------
# |  
# |  __init__.py
# |  
# |  David Brownell <db@DavidBrownell.com>
# |      2018-05-12 23:22:08
# |  
# ----------------------------------------------------------------------
# |  
# |  Copyright David Brownell 2018.
# |  Distributed under the Boost Software License, Version 1.0.
# |  (See accompanying file LICENSE_1_0.txt or copy at http://www.boost.org/LICENSE_1_0.txt)
# |  
# ----------------------------------------------------------------------
"""Contains the SourceControlManagement and DistributedSourceControlManagement objects"""

import os
import sys
import textwrap

from collections import namedtuple

import six

from CommonEnvironment.Interface import *
from CommonEnvironment import FileSystem

# ----------------------------------------------------------------------
_script_fullpath = os.path.abspath(__file__) if "python" in sys.executable.lower() else sys.executable
_script_dir, _script_name = os.path.split(_script_fullpath)
# ----------------------------------------------------------------------

# ----------------------------------------------------------------------
class SourceControlManagement(Interface):
    """
    Base class for a standard source control management system.

    By convention, all actions return (return_code, output) for all actions.
    A method is considered an action if it doesn't begin with 'Is', 'Has', or
    'Get'.
    """

    # ----------------------------------------------------------------------
    # |  
    # |  Public Properties
    # |  
    # ----------------------------------------------------------------------
    @abstractproperty
    def Name(self):
        raise Exception("Abstract property")

    @abstractproperty
    def DefaultBranch(self):
        """
        Name of the default branch for the system. This name will often be used
        when no other branch name has been specified.
        """
        raise Exception("Abstract property")

    @abstractproperty
    def Tip(self):
        """Name of the most recent checkin."""
        raise Exception("Abstract property")

    @abstractproperty
    def WorkingDirectories(self):
        """
        Names of the directory(ies) used by the system to track changes and local state.
        This can be an empty list if the system don't use local directories to track state.
        """
        raise Exception("Abstract property")

    @abstractproperty
    def IgnoreFilename(self):
        """
        Name of a local file used to track files that should be ignored by the system. This
        can be None if the system doesn't not make use of such a file.
        """
        raise Exception("Abstract property")

    def IsDistributed(self):
        """Returns True if the system is a distributes source control system."""
        return False
    
    # Set the True to enable additional diagnostics
    Diagnostics                             = False

    # ----------------------------------------------------------------------
    # |  
    # |  Public Methods
    # |  
    # ----------------------------------------------------------------------
    @staticmethod
    @abstractmethod
    def IsAvailable():
        """Returns True if the source control management system is available on this computer."""
        raise Exception("Abstract method")

    # ----------------------------------------------------------------------
    @staticmethod
    @abstractmethod
    def IsActive(repo_root):
        """Returns True if the source control management system is activate for the provided root directory."""
        raise Exception("Abstract method")

    # ----------------------------------------------------------------------
    @staticmethod
    @abstractmethod
    def Create(output_dir):
        """Creates a repository in the provided output directory."""
        raise Exception("Abstract method")

    # ----------------------------------------------------------------------
    @staticmethod
    @abstractmethod
    def Clone(uri, output_dir, branch=None):
        """Clones a repository in the provided output directory; DefaultBranch will be used if no branch is provided."""
        raise Exception("Abstract method")

    # ----------------------------------------------------------------------
    @staticmethod
    @abstractmethod
    def GetUniqueName(repo_root):
        """Returns a unique name for the repository active at the provided root."""
        raise Exception("Abstract method")

    # ----------------------------------------------------------------------
    @staticmethod
    @abstractmethod
    def Who(repo_root):
        """Returns the username associated with the specified repo."""
        raise Exception("Abstract method")

    # ----------------------------------------------------------------------
    @staticmethod 
    @abstractmethod
    def GetRoot(repo_dir):
        """
        Returns the root directory of the repository associated with the provided directory
        using conventions specific to the SCM.
        """
        raise Exception("Abstract method")
    
    # ----------------------------------------------------------------------
    @classmethod
    @extensionmethod
    def IsRoot(cls, repo_dir):
        """Returns True if the given dir is the root dir for the repository"""
        return cls.IsAvailable() and cls.IsActive(repo_dir) and cls.GetRoot(repo_dir) == repo_dir

    # ----------------------------------------------------------------------
    @staticmethod
    @abstractmethod
    def Clean(repo_root, no_prompt=False):
        """Reverts any changes in the local working directory."""
        raise Exception("Abstract method")

    # ----------------------------------------------------------------------
    @staticmethod
    @abstractmethod
    def GetBranches(repo_root):
        """Gets all local branches"""
        raise Exception("Abstract method")

    # ----------------------------------------------------------------------
    @staticmethod
    @abstractmethod
    def GetCurrentBranch(repo_root):
        """Gets the current branch"""
        raise Exception("Abstract method")

    # ----------------------------------------------------------------------
    @classmethod
    @extensionmethod
    def GetCurrentNormalizedBranch(cls, repo_root):
        """
        Some SCMs (such as Git) need to do wonky things to ensure that branches
        stay consistent (e.g. to avoid a detached head state), such as decorating
        branch names. These wonky things may present problems for other programs,
        so this method will expose standard names that undecorare the actual
        branch name.
        """
        return cls.GetCurrentBranch(repo_root)

    # ----------------------------------------------------------------------
    @staticmethod
    @abstractmethod
    def GetMostRecentBranch(repo_root):
        """Gets the name of the branch associated with the most recent change"""
        raise Exception("Abstract method")

    # ----------------------------------------------------------------------
    @staticmethod
    @abstractmethod
    def CreateBranch(repo_root, branch_name):
        """Creates a local branch"""
        raise Exception("Abstract method")

    # ----------------------------------------------------------------------
    @staticmethod
    @abstractmethod
    def SetBranch(repo_root, branch_name):
        """Sets the local repository to the specified branch."""
        raise Exception("Abstract method")

    # ----------------------------------------------------------------------
    @classmethod
    def SetBranchOrDefault(cls, repo_root, branch_name):
        """Sets the local repository to the specified branch if it exists or the default branch if it doesn't."""
        return cls.SetBranch( repo_root,
                              branch_name if branch_name in cls.GetBranches(repo_root) else cls.DefaultBranch,
                            )

    # ----------------------------------------------------------------------
    @staticmethod
    @abstractmethod
    def HasUntrackedWorkingChanges(repo_root):
        """Returns True if there are changes to files that are not tracked in the local working directory."""
        raise Exception("Abstract method")

    # ----------------------------------------------------------------------
    @staticmethod
    @abstractmethod
    def HasWorkingChanges(repo_root):
        """Returns True if there are changes to files in the local working directory."""
        raise Exception("Abstract method")

    # ----------------------------------------------------------------------
    @staticmethod
    @abstractmethod
    def GetWorkingChanges(repo_root):
        """Returns a list of all files that have changed (but are not yet committed) in the local working directory."""
        raise Exception("Abstract method")

    # ----------------------------------------------------------------------
    GetWorkingChangeStatusResult            = namedtuple( "GetWorkingChangeStatusResult",
                                                          [ "untracked",
                                                            "working",
                                                            
                                                          ],
                                                        )

    @classmethod
    @extensionmethod
    def GetWorkingChangeStatus(cls, repo_root):
        """
        Returns information about local change status. Derived implementations should
        override this method if it is possible to implement it in a more efficient
        manner.
        """
        return cls.GetWorkingChangeStatusResult( cls.HasUntrackedWorkingChanges(repo_root),
                                                 cls.HasWorkingChanges(repo_root),
                                               )

    # ----------------------------------------------------------------------
    @staticmethod
    @abstractmethod
    def GetChangeInfo(repo_root, change):
        """
        Returns a dictionary that contains information about a specific change. At the 
        very least, the object will contain the attributes:
            - user
            - date
            - summary
        """
        raise Exception("Abstract method")

    # ----------------------------------------------------------------------
    @classmethod
    def AddFiles( cls,
                  repo_root,
                  files,                    # Can be: [ filenames, ... ]
                                            #         filename
                                            #         <recurse from root if True else search in the current dir>
                  filter_functor=None,      # def Func(filename) -> bool (True to add, False to skip)
                ):
        """
        Adds the file or files specified or will search for new files in the current dir
        (if files is False) or from the repo root (if false is True).
        """

        if isinstance(files, bool):

            if files:
                # ----------------------------------------------------------------------
                def GetFiles():
                    return FileSystem.WalkFiles( repo_root,
                                                 traverse_exclude_dir_names=cls.WorkingDirectories,
                                               )

                # ----------------------------------------------------------------------

            else:
                # ----------------------------------------------------------------------
                def GetFiles():
                    return FileSystem.WalkFiles( os.getcwd(),
                                                 recurse=False,
                                               )

                # ----------------------------------------------------------------------

            filter_functor = filter_functor or (lambda filename: True)

            files = [ filename for filename in GetFiles() if filter_functor(filename) ]

        elif isinstance(files, six.string_types):
            files = [ files, ]

        for filename in files:
            if not os.path.isfile(filename):
                raise Exception("'{}' is not a valid file".format(filename))

        return cls._AddFilesImpl(repo_root, files)

    # ----------------------------------------------------------------------
    @staticmethod
    @abstractmethod
    def Commit(repo_root, description, username=None):
        """Commits the local changes"""
        raise Exception("Abstract method")

    # ----------------------------------------------------------------------
    @staticmethod
    @abstractmethod
    def Update(repo_root, update_arg=None):
        """Updates the working directory. Will update to local tip if update_arg is None"""
        raise Exception("Abstract method")

    # ----------------------------------------------------------------------
    @staticmethod
    @abstractmethod
    def Merge(repo_root, merge_arg):
        """Merges the branch/change specified by the provided merge arg into the working directory."""
        raise Exception("Abstract method")

    # ----------------------------------------------------------------------
    @staticmethod
    @abstractmethod
    def GetChangesSinceLastMerge( repo_root, 
                                  dest_branch, 
                                  source_merge_arg=None,
                                ):
        """
        Returns all changes since the last merge from the current branch to dest_branch.
        source_merge_arg and dest_merge_arg can be used to refine the changes returned.
        """
        raise Exception("Abstract method")

    # ----------------------------------------------------------------------
    @staticmethod
    @abstractmethod
    def GetChangedFiles(repo_root, change_or_changes_or_none):
        """Get the files changed as a part of the provided change or changes"""
        raise Exception("Abstract method")

    # ----------------------------------------------------------------------
    @staticmethod
    @abstractmethod
    def EnumBlameInfo(repo_root, filename):
        """Returns blame information for lines in the provided filename."""
        raise Exception("Abstract method")

    # ----------------------------------------------------------------------
    @staticmethod
    @abstractmethod
    def EnumTrackedFiles(repo_root):
        """Enumerates the filenames of all files tracked in working directory"""
        raise Exception("Abstract method")

    # ----------------------------------------------------------------------
    @staticmethod
    @abstractmethod
    def CreatePatch( repo_root, 
                     output_filename,
                     start_change=None,
                     end_change=None,
                   ):
        """
        Creates a patch based on the source and dest merge args. Will use local
        changes if both are None.
        """
        raise Exception("Abstract method")

    # ----------------------------------------------------------------------
    @staticmethod
    @abstractmethod
    def ApplyPatch( repo_root,
                    patch_filename,
                    commit=False,
                  ):
        """Applies the provided patch to the current working directory."""
        raise Exception("Abstract method")

    # ----------------------------------------------------------------------
    # |  
    # |  Protected Methods
    # |  
    # ----------------------------------------------------------------------
    @staticmethod
    def AreYouSurePrompt(prompt):
        result = six.moves.input("{}\nEnter 'y' to continue or anything else to exit: ".format(prompt)).strip() == 'y'
        sys.stdout.write("\n")

        return result

    # ----------------------------------------------------------------------
    # |  
    # |  Private Methods
    # |  
    # ----------------------------------------------------------------------
    @staticmethod
    @abstractmethod
    def _AddFilesImpl(repo_root, filenames):
        raise Exception("Abstract method")

# ----------------------------------------------------------------------
class DistributedSourceControlManagement(SourceControlManagement):
    """
    Base class for a distributed source control management system.

    By convention, all actions return (return_code, output) for all actions.
    A method is considered an action if it doesn't begin with 'Is', 'Has', or
    'Get'.
    """

    IsDistributed                           = True

    # ----------------------------------------------------------------------
    @staticmethod
    @abstractmethod
    def Reset( repo_root, 
               no_prompt=False, 
               no_backup=False,
             ):
        """Resets the repo to the remote state, erasing any unpushed (but committed) changes."""
        raise Exception("Abstract method")

    # ----------------------------------------------------------------------
    @staticmethod
    @abstractmethod
    def HasUpdateChanges(repo_root):
        """Returns True if there are changes on the local branch that have yet to be applied to the working directory."""
        raise Exception("Abstract method")

    # ----------------------------------------------------------------------
    @staticmethod
    @abstractmethod
    def HasLocalChanges(repo_root):
        """Returns True if there are changes commited in the local branch that have yet to be pushed to the remote repository."""
        raise Exception("Abstract method")

    # ----------------------------------------------------------------------
    @staticmethod
    @abstractmethod
    def GetLocalChanges(repo_root):
        """Returns all changes that have yet to be pushed to the remote repository."""
        raise Exception("Abstract method")

    # ----------------------------------------------------------------------
    @staticmethod
    @abstractmethod
    def HasRemoteChanges(repo_root):
        """Returns True if there are changes in the remote repo that have yet to be pulled to the local repo."""
        raise Exception("Abstract method")

    # ----------------------------------------------------------------------
    @staticmethod
    @abstractmethod
    def GetRemoteChanges(repo_root):
        """Returns all changes that have yet to be pulled from the remote repo."""
        raise Exception("Abstract method")

    # ----------------------------------------------------------------------
    GetChangeStatusResult                   = namedtuple( "GetChangeStatusResult",
                                                           [ "untracked",
                                                             "working",
                                                             "local",
                                                             "remote",
                                                             "update",
                                                             "branch",
                                                           ],
                                                        )
    @classmethod
    @extensionmethod
    def GetChangeStatus(cls, repo_root):
        """
        Returns information about change status. Derived implementations should
        override this method if it is possible to implement it in a more efficient
        manner.
        """
        
        return cls.GetChangeStatusResult( cls.HasUntrackedWorkingChanges(repo_root),
                                          cls.HasWorkingChanges(repo_root),
                                          cls.HasLocalChanges(repo_root),
                                          cls.HasRemoteChanges(repo_root),
                                          cls.HasUpdateChanges(repo_root),
                                          cls.GetMostRecentBranch(repo_root),
                                        )

    # ----------------------------------------------------------------------
    @staticmethod
    @abstractmethod
    def Push(repo_root, create_remote_branch=False):
        """Pushes committed changes to the remote repo."""
        raise Exception("Abstract method")

    # ----------------------------------------------------------------------
    @staticmethod
    @abstractmethod
    def Pull(repo_root, branch_or_branches=None):
        """Pulls changes from the remote repo."""
        raise Exception("Abstract method")
