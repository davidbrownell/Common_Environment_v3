# ----------------------------------------------------------------------
# |  
# |  GitSourceControlManagement.py
# |  
# |  David Brownell <db@DavidBrownell.com>
# |      2018-05-30 21:48:36
# |  
# ----------------------------------------------------------------------
# |  
# |  Copyright David Brownell 2018.
# |  Distributed under the Boost Software License, Version 1.0.
# |  (See accompanying file LICENSE_1_0.txt or copy at http://www.boost.org/LICENSE_1_0.txt)
# |  
# ----------------------------------------------------------------------
"""Contains the GitSourceControlManagement object"""

import os
import re
import sys
import textwrap

import six

from CommonEnvironment.CallOnExit import CallOnExit
from CommonEnvironment import FileSystem
from CommonEnvironment.Interface import staticderived, override, DerivedProperty
from CommonEnvironment import Process
from CommonEnvironment import RegularExpression
from CommonEnvironment.Shell.All import CurrentShell

from CommonEnvironment.SourceControlManagement import DistributedSourceControlManagement
from CommonEnvironment.SourceControlManagement.UpdateMergeArgs import *

from CommonEnvironment.TypeInfo.FundamentalTypes.DateTimeTypeInfo import DateTimeTypeInfo
from CommonEnvironment.TypeInfo.FundamentalTypes.Serialization.StringSerialization import StringSerialization

# ----------------------------------------------------------------------
_script_fullpath = os.path.abspath(__file__) if "python" in sys.executable.lower() else sys.executable
_script_dir, _script_name = os.path.split(_script_fullpath)
# ----------------------------------------------------------------------

# ----------------------------------------------------------------------
@staticderived
class GitSourceControlManagement(DistributedSourceControlManagement):
    """Specializations for Git [https://www.git-scm.com/]"""

    # ----------------------------------------------------------------------
    # |  
    # |  Public Properties
    # |  
    # ----------------------------------------------------------------------
    Name                                    = DerivedProperty("Git")
    DefaultBranch                           = DerivedProperty("master")
    Tip                                     = DerivedProperty("head")
    WorkingDirectories                      = DerivedProperty([ ".git", ])
    IgnoreFilename                          = DerivedProperty(".gitignore")

    DetachedHeadPseudoBranchName            = "__DetachedHeadPseudoBranchName_{Index}_{BranchName}__"
    _DetachedHeadPseudoBranchName_regex     = RegularExpression.TemplateStringToRegex(DetachedHeadPseudoBranchName)

    # ----------------------------------------------------------------------
    # |  
    # |  Public Methods
    # |  
    # ----------------------------------------------------------------------
    @classmethod
    def Execute( cls,
                 repo_root,
                 command,
                 strip=False,
                 newline=False,
               ):
        command = command.replace("git ", 'git -C "{}" '.format(repo_root))

        if cls.Diagnostics:
            sys.stdout.write("VERBOSE: {}\n".format(command))

        result, content = Process.Execute( command,
                                           environment=os.environ,
                                         )

        if strip:
            content = content.strip()
        if newline and not content.endswith('\n'):
            content += '\n'

        return result, content
    
    # ----------------------------------------------------------------------
    @classmethod
    @override
    def IsAvailable(cls):
        is_available = getattr(cls, "_cached_is_available", None)
        if is_available is None:
            _, output = cls.Execute(os.getcwd(), "git")
            is_available = "usage: git" in output

            setattr(cls, "_cached_is_available", is_available)

        return is_available

    # ----------------------------------------------------------------------
    _cached_is_active                       = set()

    @classmethod
    @override
    def IsActive(cls, repo_root):
        for k in cls._cached_is_active:
            if repo_root.startswith(k):
                return k

        try:
            result = os.path.isdir(cls.GetRoot(repo_root))

            # Note that we are only caching positive results. This is to ensure
            # that we walk into repositories associated with subdirs when provided
            # with a parent dir that isn't a repository itself (caching a failure 
            # on a parent dir would prevent traversal into its children).
            if result:
                cls._cached_is_active.add(repo_root)

        except:
            result = False

        return result

    # ----------------------------------------------------------------------
    @classmethod
    @override
    def Create(cls, output_dir):
        if os.path.isdir(output_dir):
            raise Exception("The directory '{}' already exists and will not be overwritten".format(output_dir))
    
        FileSystem.MakeDirs(output_dir)
        return cls.Execute(os.getcwd(), 'git init "{}"'.format(output_dir))
    
    # ----------------------------------------------------------------------
    @classmethod
    @override
    def Clone(cls, uri, output_dir, branch=None):
        if os.path.isdir(output_dir):
            raise Exception("The directory '{}' already exists and will not be overwritten.".format(output_dir))
    
        clone_path, clone_name = os.path.split(output_dir)
        FileSystem.MakeDirs(clone_path)
    
        return cls.Execute(clone_path, 'git clone{branch} "{uri}" "{name}"'.format( branch=' --branch "{}"'.format(branch) if branch else '',
                                                                                    uri=uri,
                                                                                    name=clone_name,
                                                                                  ))
    
    # ----------------------------------------------------------------------
    @classmethod
    @override
    def GetUniqueName(cls, repo_root):
        result, output = cls.Execute(repo_root, "git remote -v")
        assert result == 0, (result, output)
    
        regex = re.compile(r"origin\s+(?P<url>.+?)\s+\(fetch\)")
    
        for line in output.split('\n'):
            match = regex.match(line)
            if match:
                return match.group("url")
    
        # If here, we didn't find anything. Most of the time, this
        # is an indication that the repo is local (no remote); return
        # the path.
        return os.path.realpath(repo_root)
    
    # ----------------------------------------------------------------------
    @classmethod
    @override
    def Who(cls, repo_root):
        # ----------------------------------------------------------------------
        def GetValue(name):
            result, output = cls.Execute(repo_root, "git config {}".format(name))
            assert result == 0, (result, output)

            return output.strip()

        # ----------------------------------------------------------------------

        return "{} <{}>".format( GetValue("user.name"),
                                 GetValue("user.email"),
                               )

    # ----------------------------------------------------------------------
    _cached_roots                           = set()

    @classmethod
    @override
    def GetRoot(cls, repo_dir):
        for k in cls._cached_roots:
            if repo_dir.startswith(k):
                return k

        result, output = cls.Execute( repo_dir,
                                      "git rev-parse --show-toplevel",
                                      strip=True,
                                    )
        assert result == 0, (result, output)

        cls._cached_roots.add(output)

        return output
    
    # ----------------------------------------------------------------------
    @classmethod
    @override
    def IsRoot(cls, repo_dir):
        return os.path.isdir(os.path.join(repo_dir, cls.WorkingDirectories[0]))

    # ----------------------------------------------------------------------
    @classmethod
    @override
    def Clean(cls, repo_root, no_prompt=False):
        if not no_prompt and not cls.AreYouSurePrompt(textwrap.dedent(
            # <Wrong hanging indentation> pylint: disable = C0330
            """\
            This operation will revert any working changes.

            THIS INCLUDES THE FOLLOWING:
                - Any working edits
                - Any files that have been added
            """)):
            return 0, "<<Skipped>>"

        commands = [ "git reset --hard",
                     "git clean -df",
                   ]

        return cls.Execute(repo_root, " && ".join(commands))

    # ----------------------------------------------------------------------
    _GetBranches_regex                      = re.compile(r"^\*?\s*\[(origin/)?(?P<name>\S+?)\]\s+.+?")

    @classmethod
    @override
    def GetBranches(cls, repo_root):
        result, output = cls.Execute(repo_root, "git show-branch --list --all")
        assert result == 0, (result, output)

        branches = set()

        for line in output.split('\n'):
            match = cls._GetBranches_regex.match(line)
            if not match:
                continue

            branch = match.group("name")
            if branch not in branches:
                branches.add(branch)
                yield branch

    # ----------------------------------------------------------------------
    _GetCurrentBranch_regex                 = re.compile(r"\s*\*\s+(?P<name>.+)")

    @classmethod
    @override
    def GetCurrentBranch(cls, repo_root):
        result, output = cls.Execute(repo_root, "git branch --no-color")
        assert result == 0, (result, output)
    
        if output:
            for line in output.split('\n'):
                match = cls._GetCurrentBranch_regex.match(line)
                if match:
                    return match.group("name")

        return cls.DefaultBranch
    
    # ----------------------------------------------------------------------
    @classmethod
    @override
    def GetMostRecentBranch(cls, repo_root):
        result, output = cls.Execute( repo_root,
                                      'git for-each-ref --sort=-committerdate --format="%(refname)"',
                                    )
        assert result == 0, (result, output)

        for line in output.split('\n'):
            parts = line.split('/')

            if parts[1] == "remotes" and parts[2] == "origin":
                return parts[3]

        assert False, output
        return None
    
    # ----------------------------------------------------------------------
    @classmethod
    @override
    def CreateBranch(cls, repo_root, branch_name):
        return cls.Execute(repo_root, 'git branch "{name}" && git checkout "{name}"'.format(name=branch_name))
    
    # ----------------------------------------------------------------------
    @classmethod
    @override
    def SetBranch(cls, repo_root, branch_name):
        return cls.Execute(repo_root, 'git checkout "{}"'.format(branch_name))

    # ----------------------------------------------------------------------
    @classmethod
    @override
    def HasUntrackedWorkingChanges(cls, repo_root):
        result, output = cls.Execute(repo_root, "git ls-files --others --exclude-standard")
        assert result == 0, (result, output)

        return bool(output)

    # ----------------------------------------------------------------------
    @classmethod
    @override
    def HasWorkingChanges(cls, repo_root):
        result, output = cls.Execute(repo_root, "git --no-pager diff -name-only")
        assert result == 0, (result, output)

        return bool(output)

    # ----------------------------------------------------------------------
    @classmethod
    @override
    def GetWorkingChanges(cls, repo_root):
        result, output = cls.Execute(repo_root, 'git status --short')
        assert result == 0, (result, output)

        regex = re.compile("^(?P<type>..)\s+(?P<filename>.+)$")
        
        results = []
        for line in output.split('\n'):
            match = regex.match(line)
            if match:
                results.append(os.path.join(repo_root, match.group("filename").replace('/', os.path.sep)))
                
        return results
        
    # ----------------------------------------------------------------------
    @classmethod
    @override
    def GetChangeInfo(cls, repo_root, change):
        # Not the spaces to work around issues with git
        template = " %aN <%ae> %n %cd %n %s"

        result, output = cls.Execute(repo_root, 'git --no-pager show -s --format="{}" "{}"'.format(template, change))
        assert result == 0, (result, output)

        lines = output.split('\n')
        assert len(lines) >= 3, (len(lines), output)

        d = { "user" : lines[0].lstrip(),
              "date" : lines[1].lstrip(),
              "summary" : lines[2].lstrip(),
            }

        d["files"] = cls.GetChangedFiles(repo_root, change)

        return d

    # ----------------------------------------------------------------------
    _Commit_regex                           = re.compile(r"(?P<username>.+?)\s+\<(?P<email>.+?)\>")

    @classmethod
    @override
    def Commit(cls, repo_root, description, username=None):
        # Git is particular about username format; massage it into the right
        # format if necessary.
        if username:
            match = cls._Commit_regex.match(username)
            if not match:
                username = "{} <noreply@Generator.com>".format(username)

        return cls.Execute( repo_root,
                            'git commit -a --allow-empty -m "{desc}"{user}'.format( desc=description.replace('"', '\\"'),
                                                                                    user=' --author="{}"'.format(username) if username else '',
                                                                                  ),
                          )
    # ----------------------------------------------------------------------
    @classmethod
    @override
    def Update(cls, repo_root, update_arg=None):
        branch = cls.GetCurrentBranch(repo_root)

        commands = [ 'git merge --ff-only "origin/{}"'.format(branch),
                   ]

        if update_arg is None:
            pass
        elif isinstance(update_arg, EmptyUpdateMergeArg):
            pass 
        elif isinstance(update_arg, BranchUpdateMergeArg):
            commands.insert(0, 'git checkout "{}"'.format(update_arg.Branch))
        elif isinstance(update_arg, ( ChangeUpdateMergeArg,
                                      DateUpdateMergeArg,
                                      BranchAndDateUpdateMergeArg,
                                    )):
            revision = cls._UpdateMergeArgToString(repo_root, update_arg)

            # Updating to a specific revision within Git is interesting, as one will find
            # themselves in a "DETACHED HEAD" state. While this makes a lot of sense from
            # a commit perspective, it doesn't make as much sense from a reading perspective
            # (especially in scenarios where it is necessary to derive the branch name from the
            # current state, as will be the case during Reset). To work around this, Update to
            # a new branch that is cleverly named in a way that can be parsed by commands that
            # need this sort of information.
            existing_branch_names = set(cls.GetBranches(repo_root))

            index = 0
            while True:
                potential_branch_name = cls.DetachedHeadPseudoBranchName.format( Index=index,
                                                                                 BranchName=branch,
                                                                               )

                if potential_branch_name not in existing_branch_names:
                    break

                index += 1

            commands.append('git checkout {} -b "{}"'.format(revision, potential_branch_name))

        else:
            assert False, type(update_arg)

        return cls.Execute(repo_root, " && ".join(commands))

    # ----------------------------------------------------------------------
    @classmethod
    @override
    def Merge(cls, repo_root, merge_arg):
        return cls.Execute(repo_root, 'git merge --no-commit --no-ff {}'.format(cls._UpdateMergeArgToString(repo_root, merge_arg)))

    # ----------------------------------------------------------------------
    @classmethod
    @override
    def GetChangesSinceLastMerge(cls, repo_root, dest_branch, source_merge_arg=None):
        # Git is really screwed up. After a 30 minute search, I couldn't find a way to
        # specify a branch and beginning revision in a single command. Therefore, I am
        # doing it manually.

        source_branch = None
        additional_filters = []
        post_decorator_func = None

        # ----------------------------------------------------------------------
        def GetDateOperator(arg):
            if arg is None or arg:
                return "since"

            return "until"

        # ----------------------------------------------------------------------

        if source_merge_arg is None or isinstance(source_merge_arg, EmptyUpdateMergeArg):
            source_branch = cls.GetCurrentBranch(repo_root)

        elif isinstance(source_merge_arg, ChangeUpdateMergeArg):
            source_branch = cls._GetBranchAssociatedWithChange(source_merge_arg.Change)

            # ----------------------------------------------------------------------
            def AfterChangeDecorator(changes):
                starting_index = None

                for index, change in enumerate(changes):
                    if change == source_merge_arg.Change:
                        starting_index = index 
                        break

                if starting_index is None:
                    return []

                return changes[starting_index:]

            # ----------------------------------------------------------------------

            post_decorator_func = AfterChangeDecorator

        elif isinstance(source_merge_arg, DateUpdateMergeArg):
            source_branch = cls.GetCurrentBranch(repo_root)
            additional_filters.append('--{}="{}"'.format( GetDateOperator(source_merge_arg.GreaterThan),
                                                          StringSerialization.SerializeItem(DateTimeTypeInfo(), source_merge_arg.Date),
                                                        ))

        elif isinstance(source_merge_arg, BranchUpdateMergeArg):
            source_branch = source_merge_arg.Branch

        elif isinstance(source_merge_arg, BranchAndDateUpdateMergeArg):
            source_branch = source_merge_arg.Branch
            additional_filters.append('--{}="{}"'.format( GetDateOperator(source_merge_arg.GreaterThan),
                                                          StringSerialization.SerializeItem(DateTimeTypeInfo(), source_merge_arg.Date),
                                                        ))

        else:
            assert False, type(source_merge_arg)

        command_line = 'git --no-pager log "{source_branch}" --not "{dest_branch}" --format="%H" --no-merges{additional_filters}' \
                            .format( source_branch=source_branch,
                                     dest_branch=dest_branch,
                                     additional_filters='' if not additional_filters else " {}".format(' '.join(additional_filters)),
                                   )

        result, output = cls.Execute(repo_root, command_line)
        assert result == 0, (result, output)

        changes = [ line.strip() for line in output.split('\n') if line.strip() ]

        if post_decorator_func:
            changes = post_decorator_func(changes)

        return changes

    # ----------------------------------------------------------------------
    _GetChangedFiles_regex                  = re.compile(r'^(?:\S|\?\?)\s+"?(?P<filename>.+)"?$')

    @classmethod
    @override
    def GetChangedFiles(cls, repo_root, change_or_changes_or_none):
        if not change_or_changes_or_none:
            result, output = cls.Execute(repo_root, 'git status --short')
            assert result == 0, (result, output)

            filenames = []

            for line in [ line.strip() for line in output.split('\n') if line.strip() ]:
                match = cls._GetChangedFiles_regex(line)
                assert match, line

                filenames.append(os.path.join(repo_root, match.group("filename")))

            return filenames

        changes = change_or_changes_or_none if isinstance(change_or_changes_or_none, list) else [ change_or_changes_or_none, ]
        command_line_template = 'git diff-tree --no-commit-id --name-only -r {}'

        filenames = set()

        for change in changes:
            change = cls._UpdateMergeArgToString(repo_root, ChangeUpdateMergeArg(change))
            command_line = command_line_template.format(change)
            
            result, output = cls.Execute(repo_root, command_line)
            assert result == 0, (result, output)

            for line in [ line.strip() for line in output.split('\n') if line.strip() ]:
                filename = os.path.join(repo_root, line)

                if filename not in filenames:
                    filenames.add(filename)

        return sorted(filenames)
    
    # ----------------------------------------------------------------------
    @classmethod
    @override
    def EnumBlameInfo(cls, repo_root, filename):
        result, output = cls.Execute(repo_root, 'git blame -s "{}"'.format(filename))

        if result != 0:
            # Don't produce an error if we are looking at a file that has been renamed/removed.
            if "No such file or directory" in output:
                return

            assert False, (result, output)

        regex = re.compile(r"^(?P<revision>\S+)\s+(?P<line_number>\d+)\)(?: (?P<line>.*))?$")

        for line in output.split('\n'):
            if not line:
                continue

            match = regex.match(line)
            if not match:
                # Don't produce an error on a failure to enumerate binary files
                if line.endswith("binary file"):
                    return

                assert False, line

            yield match.group("revision"), match.group("line_number")

    # ----------------------------------------------------------------------
    @classmethod
    @override
    def EnumTrackedFiles(cls, repo_root):
        temp_filename = CurrentShell.CreateTempFilename()

        result, output = cls.Execute(repo_root, 'git ls-files > "{}"'.format(temp_filename))
        assert result == 0, (result, output)

        assert os.path.isfile(temp_filename), temp_filename
        with CallOnExit(lambda: os.remove(temp_filename)):
            with open(temp_filename) as f:
                for line in f.readlines():
                    line = line.strip()
                    if line:
                        yield os.path.join(repo_root, line)

    # ----------------------------------------------------------------------
    @classmethod
    @override
    def CreatePatch( cls,
                     repo_root, 
                     output_filename,
                     start_change=None,
                     end_change=None,
                   ):
        if not start_change or not end_change:
            command_line = 'git diff -g > "{}"'.format(output_filename)
        else:
            command_line = 'git diff -g {start} {end} > "{filename}"'.format( start=start_change,
                                                                              end=end_change,
                                                                              filename=output_filename,
                                                                            )
        return cls.Execute(repo_root, command_line)

    # ----------------------------------------------------------------------
    @classmethod
    @override
    def ApplyPatch( cls, 
                    repo_root,
                    patch_filename,
                    commit=False,
                  ):
        if commit:
            raise Exception("Git does not support applying a patch without committing")

        return cls.Execute(repo_root, 'git apply "{}"'.format(patch_filename))
    
    # ----------------------------------------------------------------------
    @classmethod
    @override
    def Reset( cls,
               repo_root, 
               no_prompt=False, 
               no_backup=False,
             ):
        if not no_prompt and not cls.AreYouSurePrompt(textwrap.dedent(
            # <Wrong hanging indentation> pylint: disable = C0330
            """\
            This operation will revert your local repository to match the state of the remote repository.

            THIS INCLUDES THE FOLLOWING:
                - Any working edits
                - Any files that have been added
                - Any committed changes that have not been pushed to the remote repository
            """)):
            return 0, ''

        commands = []

        # See if we are looking at a detached head pseudo branch. If so, extract the actual
        # branch name and switch to that before running the other commands.
        branch = cls.GetCurrentBranch(repo_root)

        match = cls._DetachedHeadPseudoBranchName_regex.match(branch)
        if match:
            branch = match.group("BranchName")
            commands.append('git checkout "{}"'.format(branch))

        # Remove any of the pseudo branches that have been created
        for potential_delete_branch in cls.GetBranches(repo_root):
            if cls._DetachedHeadPseudoBranchName_regex.match(potential_delete_branch):
                commands.append('git branch -D "{}"'.format(potential_delete_branch))

        commands += [ 'git reset --hard "origin/{}"'.format(branch),
                      'git clean -df',
                    ]

        return cls.Execute(repo_root, ' && '.join(commands))

    # ----------------------------------------------------------------------
    @classmethod
    @override
    def HasUpdateChanges(cls, repo_root):
        result, output = cls.Execute(repo_root, "git status -uno")
        assert result == 0, (result, output)

        return "Your branch is behind" in output or "have diverged" in output

    # ----------------------------------------------------------------------
    @classmethod
    @override
    def HasLocalChanges(cls, repo_root):
        result, output = cls.Execute(repo_root, 'git --no-pager log --branches --not --remotes')
        assert result == 0 or (result == 1 and "no changes found" in output), (result, output)

        return bool(output)

    # ----------------------------------------------------------------------
    @classmethod
    @override
    def GetLocalChanges(cls, repo_root):
        result, output = cls.Execute(repo_root, 'git remote update')
        assert result == 0, (result, output)

        result, output = cls.Execute(repo_root, 'git --no-pager log "origin/{}..HEAD" --format="%H"'.format(cls.GetCurrentBranch(repo_root)))
        assert result == 0, (result, output)

        return [ line.strip() for line in output.split('\n') if line.strip() ]

    # ----------------------------------------------------------------------
    @classmethod
    @override
    def HasRemoteChanges(cls, repo_root):
        result, output = cls.Execute(repo_root, 'git remote update')
        assert result == 0, (result, output)
        
        return cls.HasUpdateChanges(repo_root)

    # ----------------------------------------------------------------------
    @classmethod
    @override
    def GetRemoteChanges(cls, repo_root):
        result, output = cls.Execute(repo_root, 'git remote update')
        assert result == 0, (result, output)

        result, output = cls.Execute(repo_root, 'git --no-pager log "HEAD..origin/{}" --format="%H"'.format(cls.GetCurrentBranch(repo_root)))
        assert result == 0, (result, output)

        return [ line.strip() for line in output.split('\n') if line.strip() ]

    # ----------------------------------------------------------------------
    @classmethod
    @override
    def Push(cls, repo_root, create_remote_branch=False):
        commands = [ 'git push',
                     'git push --tags',
                   ]

        if create_remote_branch:
            commands[0] += ' --set-upstream origin "{}"'.format(cls.GetCurrentBranch(repo_root))

        return cls.Execute(repo_root, " && ".join(commands))

    # ----------------------------------------------------------------------
    @classmethod
    @override
    def Pull(cls, repo_root, branch_or_branches=None):
        commands = []

        if isinstance(branch_or_branches, six.string_types):
            branch_or_branches = [ branch_or_branches, ]

        existing_branches = set(cls.GetBranches(repo_root))

        for branch_name in (branch_or_branches or []):
            if branch_name not in existing_branches:
                commands.append('git checkout -b "{name}" "origin/{name}"'.format(name=branch_name))

        commands += [ 'git fetch --all',
                      'git fetch --all --tags',
                    ]

        return cls.Execute(repo_root, " && ".join(commands))
    
    # ----------------------------------------------------------------------
    # |  
    # |  Private Methods
    # |  
    # ----------------------------------------------------------------------
    @classmethod
    @override
    def _AddFilesImpl(cls, repo_root, filenames):
        return cls.Execute(repo_root, 'git add {}'.format(' '.join([ '"{}"'.format(filename) for filename in filenames ])))

    # ----------------------------------------------------------------------
    @classmethod
    def _UpdateMergeArgToString(cls, repo_root, update_arg):

        # ----------------------------------------------------------------------
        def NormalizeChange(change):
            result, output = cls.Execute(repo_root, 'git --no-pager log {} -n 1 --format="%H"'.format(change))
            assert result == 0, (result, output)

            output = output.strip()
            if output.startswith("* "):
                output = output[len("* "):]

            return output

        # ----------------------------------------------------------------------
        def DateAndBranch(date, branch, operator):
            assert date

            if branch:
                # ----------------------------------------------------------------------
                def BranchGenerator():
                    yield branch

                # ----------------------------------------------------------------------
            else:
                # ----------------------------------------------------------------------
                def BranchGenerator():
                    for branch in [ cls.GetCurrentBranch(repo_root),
                                    cls.DefaultBranch,
                                  ]:
                        yield branch

                # ----------------------------------------------------------------------

            assert BranchGenerator

            if operator:
                operator = "since"
            else:
                operator = "until"

            for branch in BranchGenerator():
                result, output = cls.Execute(repo_root, 'git --no-pager long "--branches=*{}" "--{}={}" -n 1 --format="%H"'.format(branch, operator, date))
                
                if result == 0 and output:
                    return output

            raise Exception("Revision not found")

        # ----------------------------------------------------------------------

        dispatch_map = { EmptyUpdateMergeArg :          lambda: "",
                         ChangeUpdateMergeArg :         lambda: NormalizeChange(update_arg.Change),
                         DateUpdateMergeArg :           lambda: DateAndBranch(update_arg.Date, None, update_arg.GreaterThan),
                         BranchUpdateMergeArg :         lambda: update_arg.Branch,
                         BranchAndDateUpdateMergeArg :  lambda: DateAndBranch(update_arg.Date, update_arg.Branch, update_arg.GreaterThan),
                       }

        assert type(update_arg) in dispatch_map, type(update_arg)
        return dispatch_map[type(update_arg)]()

    # ----------------------------------------------------------------------
    @classmethod
    def _GetBranchAssociatedWithChange(cls, repo_root, change):
        result, output = cls.Execute(repo_root, 'git branch --contains {}'.format(change))
        assert result == 0, (result, output)

        output = output.strip()
        if output.startswith("* "):
            output = output[len("* "):]

        return output
