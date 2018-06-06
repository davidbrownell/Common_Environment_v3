# ----------------------------------------------------------------------
# |  
# |  Git.py
# |  
# |  David Brownell <db@DavidBrownell.com>
# |      2018-06-03 13:19:13
# |  
# ----------------------------------------------------------------------
# |  
# |  Copyright David Brownell 2018.
# |  Distributed under the Boost Software License, Version 1.0.
# |  (See accompanying file LICENSE_1_0.txt or copy at http://www.boost.org/LICENSE_1_0.txt)
# |  
# ----------------------------------------------------------------------
"""Hook functionality for Git"""

import datetime
import os
import re
import sys

from collections import namedtuple

# ----------------------------------------------------------------------
_script_fullpath = os.path.abspath(__file__) if "python" in sys.executable.lower() else sys.executable
_script_dir, _script_name = os.path.split(_script_fullpath)
# ----------------------------------------------------------------------

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", ".."))
from RepositoryBootstrap import GetFundamentalRepository as _GetFundamentalRepository
sys.path.pop(0)

_fundamental_root                           = _GetFundamentalRepository()

sys.path.insert(0, _fundamental_root)
from RepositoryBootstrap.Impl import CommonEnvironmentImports
Process                                     = CommonEnvironmentImports.Process
del sys.path[0]

del _fundamental_root

sys.path.insert(0, os.path.dirname(__file__))
import HookImpl
sys.path.pop(0)

# ----------------------------------------------------------------------
@CommonEnvironmentImports.CommandLine.EntryPoint
@CommonEnvironmentImports.CommandLine.Constraints( description_filename=CommonEnvironmentImports.CommandLine.FilenameTypeInfo(),
                                                   output_stream=None,
                                                 )
def commit_msg( description_filename,
                debug=False,
                output_stream=sys.stdout,
              ):
    repo_root = _GetRepoRoot()

    # Get the date
    dtti = CommonEnvironmentImports.CommandLine.DateTimeTypeInfo()
    
    date = CommonEnvironmentImports.FundamentalTypesStringSerialization.DeserializeItem(dtti, os.getenv("GIT_AUTHOR_DATE"))
    date = CommonEnvironmentImports.FundamentalTypesStringSerialization.SerializeItem(dtti, date)
    
    # Get files added/modified/removed
    result, output = Process.Execute('git status --porcelain --branch --untracked-files=no')
    assert result == 0, output

    pfr = _ProcessFileResult(repo_root, output)
    
    return HookImpl.Invoke( repo_root,
                            output_stream,
                            "Commit",
                            { "id" : "HEAD",
                              "author" : "{} <{}>".format(os.getenv("GIT_AUTHOR_NAME"), os.getenv("GIT_AUTHOR_EMAIL")),
                              "date" : date,
                              "description" : open(description_filename).read(),
                              "branch" : pfr.Branch,
                              "added" : pfr.Added,
                              "modified" : pfr.Modified,
                              "removed" : pfr.Removed,
                            },
                            is_debug=debug,
                          )

# ----------------------------------------------------------------------
@CommonEnvironmentImports.CommandLine.EntryPoint
@CommonEnvironmentImports.CommandLine.Constraints( remote=CommonEnvironmentImports.CommandLine.StringTypeInfo(),
                                                   output_stream=None,
                                                 )
def pre_push( remote,
              debug=False,
              output_stream=sys.stdout,
            ):
    return HookImpl.Invoke( _GetRepoRoot(),
                            output_stream,
                            "Push",
                            { "url" : remote,
                            },
                            is_debug=debug,
                          )

# ----------------------------------------------------------------------
@CommonEnvironmentImports.CommandLine.EntryPoint
@CommonEnvironmentImports.CommandLine.Constraints( args=CommonEnvironmentImports.CommandLine.StringTypeInfo(min_length=0, arity='*'),
                                                   output_stream=None,
                                                 )
def pre_receive( args=None,
                 output_stream=sys.stdout,
               ):
    # Normally, we would add a debug flag to signal debug output (as we did above).
    # However, git passes an empty string as the first argument. Rather than taking 
    # an explicit debug flag, look for "/debug" in args.
    debug = False

    for arg in (args or []):
        if arg == "/debug":
            debug = True

    dtti = CommonEnvironmentImports.CommandLine.DateTimeTypeInfo()
    repo_root = _GetRepoRoot()

    changes = []

    # Get the rev from stdin
    rev_list_regex = re.compile(r"(?P<oldrev>\S+)\s+(?P<newrev>\S+)\s+(?P<refname>\S+)")

    for line in sys.stdin.read().strip().split('\n'):
        match = rev_list_regex.match(line)
        assert match, line

        # Get all changes
        result, output = Process.Execute('git rev-list {}..{}'.format( match.group("oldrev"),
                                                                       match.group("newrev"),
                                                                     ))
        assert result == 0, output
        
        revs = [ line.strip() for line in output.split('\n') if line.strip() ]
        revs.reverse()
        
        # Get info about the changes
        for rev in revs:
            # Basic info
            result, output = Process.Execute('git show -s --format=" %aN <%ae> %n %at %n %s" {}'.format(rev))
            assert result == 0, output
        
            lines = output.split('\n')

            date = CommonEnvironmentImports.FundamentalTypesStringSerialization.DeserializeItem(dtti, lines[1].strip())
            date = CommonEnvironmentImports.FundamentalTypesStringSerialization.SerializeItem(dtti, date)

            change = { "id" : rev,
                       "author" : lines[0].strip(),
                       "date" : date,
                       "description" : lines[2].strip(),
                       "branch" : match.group("refname"),
                     }

            # Get the files
            result, output = Process.Execute('git diff-tree --no-commit-id --name-status {}'.format(rev))
            assert result == 0, output

            pfr = _ProcessFileList(repo_root, output)

            change["added"] = pfr.Added
            change["modified"] = pfr.Modified
            change["removed"] = pfr.Removed

            changes.append(change)
        
    return HookImpl.Invoke( repo_root,
                            output_stream,
                            "Pull",
                            { "changes" : changes },
                            is_debug=debug,
                          )
    
# ----------------------------------------------------------------------
# ----------------------------------------------------------------------
# ----------------------------------------------------------------------
def _GetRepoRoot():
    original_repo_root = os.getcwd()

    repo_root = original_repo_root
    while True:
        if os.path.isdir(os.path.join(repo_root, ".git")):
            return repo_root

        potential_repo_root = os.path.dirname(repo_root)
        if potential_repo_root == repo_root:
            raise Exception("No repository found in '{}' or its ancestors".format(original_repo_root))

        repo_root = potential_repo_root

# ----------------------------------------------------------------------
_ProcessFile_regex                          = re.compile(r"(?P<prefix>\S+)\s+(?P<filename>.+)")

_ProcessFileResult                          = namedtuple( "_ProcessFileResult",
                                                          [ "Branch",
                                                            "Added",
                                                            "Modified",
                                                            "Removed",
                                                          ],
                                                        )
def _ProcessFileList(repo_root, output):
    # ----------------------------------------------------------------------
    def TransformFilename(filename):
        return os.path.join(repo_root, filename).replace('/', os.path.sep)

    # ----------------------------------------------------------------------

    branch = None
    added = []
    modified = []
    removed = []

    for line in output.split('\n'):
        line = line.strip()
        if not line:
            continue

        match = _ProcessFile_regex.match(line)
        assert match

        prefix = match.group("prefix").strip()
        filename = match.group("filename")

        if prefix == "##":
            assert branch is None, branch
            branch = filename
        elif prefix == 'M':
            modified.append(TransformFilename(filename))
        elif prefix == 'A':
            added.append(TransformFilename(filename))
        elif prefix == 'D':
            removed.append(TransformFilename(filename))
        elif prefix == 'R':
            assert " -> " in filename, filename
            source, dest = filename.split(" -> ")

            removed.append(TransformFilename(source))
            added.append(TransformFilename(dest))
        elif prefix in [ 'C', 'U', ]:
            # [C]opied
            # [U]pdated but unmerged
            pass
        else:
            assert False, (prefix, filename)

    return _ProcessFileResult( branch,
                               added,
                               modified,
                               removed,
                             )

# ----------------------------------------------------------------------
# ----------------------------------------------------------------------
# ----------------------------------------------------------------------
if __name__ == "__main__":
    try: sys.exit(CommonEnvironmentImports.CommandLine.Main())
    except KeyboardInterrupt: pass
