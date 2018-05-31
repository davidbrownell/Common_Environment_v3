# ----------------------------------------------------------------------
# |  
# |  All.py
# |  
# |  David Brownell <db@DavidBrownell.com>
# |      2018-05-17 16:39:18
# |  
# ----------------------------------------------------------------------
# |  
# |  Copyright David Brownell 2018.
# |  Distributed under the Boost Software License, Version 1.0.
# |  (See accompanying file LICENSE_1_0.txt or copy at http://www.boost.org/LICENSE_1_0.txt)
# |  
# ----------------------------------------------------------------------
"""All items from this module"""

import os
import sys
import textwrap

from CommonEnvironment.CallOnExit import CallOnExit

from CommonEnvironment.SourceControlManagement.GitSourceControlManagement import GitSourceControlManagement
from CommonEnvironment.SourceControlManagement.MercurialSourceControlManagement import MercurialSourceControlManagement

# ----------------------------------------------------------------------
_script_fullpath = os.path.abspath(__file__) if "python" in sys.executable.lower() else sys.executable
_script_dir, _script_name = os.path.split(_script_fullpath)
# ----------------------------------------------------------------------

# ----------------------------------------------------------------------
# |  
# |  Public Types
# |  
# ----------------------------------------------------------------------
ALL_TYPES                                   = [ GitSourceControlManagement,
                                                MercurialSourceControlManagement,
                                              ]

# ----------------------------------------------------------------------
# |  
# |  Public Methods
# |  
# ----------------------------------------------------------------------
def GetSCM(repo_root, raise_on_error=True):
    """Returns the SCM that is active for the provided repo."""

    available = []

    for scm in ALL_TYPES:
        if scm.IsAvailable():
            available.append(scm)
            if scm.IsActive(repo_root):
                return scm

    if not raise_on_error:
        return None

    raise Exception(textwrap.dedent(
        """\
        No SCMs are active for '{repo_root}'.

        Available SCMs are:
        {available}

        Potential SCMs are:
        {potential}
        """).format( repo_root=repo_root,
                     available="    NONE" if not available else '\n'.join([ "    - {}".format(scm.Name) for scm in available ]),
                     potential="    NONE" if not ALL_TYPES else '\n'.join([ "    - {}".format(scm.Name) for scm in ALL_TYPES ]),
                   ))

# ----------------------------------------------------------------------
def GetAnySCM( path, 
               raise_on_error=True,
               by_repository_id=False,      # If True, will use much faster search heuristics
             ):
    """Returns the SCM that is active for the provided dir or any of its ancestors."""

    if by_repository_id:
        # Use repository id filenames to determine when we are at a repo root. This
        # eliminates unnecessary calls to GetSCM.

        sys.path.insert(0, os.getenv("DEVELOPMENT_ENVIRONMENT_FUNDAMENTAL"))
        with CallOnExit(lambda: sys.path.pop(0)):
            from RepositoryBootstrap import Constants as RepositoryBootstrapConstants

        root = path
        while True:
            if os.path.isfile(os.path.join(root, RepositoryBootstrapConstants.REPOSITORY_ID_FILENAME)):
                return GetSCM(root, raise_on_error=raise_on_error)

            potential_root = os.path.dirname(root)
            if potential_root == root:
                break

            root = potential_root

    else:
        root = path
        while True:
            potential_scm = GetSCM(root, raise_on_error=False)
            if potential_scm:
                return potential_scm

            potential_root = os.path.dirname(root)
            if potential_root == root:
                break

            root = potential_root

    raise Exception("No SCMs are active for '{}' or its ancestors.".format(path))

# ----------------------------------------------------------------------
def EnumSCMs(path):
    """
    Enumerates all SCMs that are active in the provided path or its descendants.
    
    Yields (scm, repo_root)
    """

    sys.path.insert(0, os.getenv("DEVELOPMENT_ENVIRONMENT_FUNDAMENTAL"))
    with CallOnExit(lambda: sys.path.pop(0)):
        from RepositoryBootstrap import Constants as RepositoryBootstrapConstants

    for root, directories, _ in os.walk(path):
        for scm in ALL_TYPES:
            if scm.IsRoot(root):
                yield scm, root

                # Don't search in subdirs, as there won't be any
                directories[:] = []
                continue

        if RepositoryBootstrapConstants.GENERATED_DIRECTORY_NAME in directories:
            # Don't search in generated dirs, as the symlinks will cause recursive enumerations
            directories.remove(RepositoryBootstrapConstants.GENERATED_DIRECTORY_NAME)
