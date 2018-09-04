# ----------------------------------------------------------------------
# |  
# |  MercurialSourceControlManagement.py
# |  
# |  David Brownell <db@DavidBrownell.com>
# |      2018-05-17 16:57:17
# |  
# ----------------------------------------------------------------------
# |  
# |  Copyright David Brownell 2018.
# |  Distributed under the Boost Software License, Version 1.0.
# |  (See accompanying file LICENSE_1_0.txt or copy at http://www.boost.org/LICENSE_1_0.txt)
# |  
# ----------------------------------------------------------------------
"""Contains the MercurialSourceControlManagement object"""

# Note that the functionality in this file requires the following Mercurial extensions:
#
#       Mercurial Extension Name            Functionality
#       ----------------------------------  --------------------------------
#       purge                               Clean, Reset
#       strip                               Reset
#
# These commands will return errors if the extensions are not installed.

import os
import re
import sys
import textwrap

from collections import OrderedDict

import six

from CommonEnvironment.CallOnExit import CallOnExit
from CommonEnvironment import FileSystem
from CommonEnvironment.Interface import staticderived, override, DerivedProperty
from CommonEnvironment import Process
from CommonEnvironment.Shell.All import CurrentShell

from CommonEnvironment.SourceControlManagement import DistributedSourceControlManagement
from CommonEnvironment.SourceControlManagement.UpdateMergeArgs import *

from CommonEnvironment.TypeInfo.FundamentalTypes.DateTimeTypeInfo import DateTimeTypeInfo
from CommonEnvironment.TypeInfo.FundamentalTypes.Serialization.StringSerialization import StringSerialization

# ----------------------------------------------------------------------
_script_fullpath = os.path.abspath(__file__) if "python" in sys.executable.lower() else sys.executable
_script_dir, _script_name = os.path.split(_script_fullpath)
# ----------------------------------------------------------------------

@staticderived
class MercurialSourceControlManagement(DistributedSourceControlManagement):
    """Specializations for Mercurial (aka Hg) [https://www.mercurial-scm.org/]"""

    # ----------------------------------------------------------------------
    # |  
    # |  Public Properties
    # |  
    # ----------------------------------------------------------------------
    Name                                    = DerivedProperty("Mercurial")
    DefaultBranch                           = DerivedProperty("default")
    Tip                                     = DerivedProperty("tip")
    WorkingDirectories                      = DerivedProperty([ ".hg", ])
    IgnoreFilename                          = DerivedProperty(".hgignore")

    # Diagnostics                             = True

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
        command = command.replace("hg ", 'hg --cwd "{}" '.format(repo_root))

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
            result, output = cls.Execute(os.getcwd(), "hg version")
            is_available = result == 0 and "Mercurial Distributed SCM" in output

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
        return cls.Execute(os.getcwd(), 'hg init "{}"'.format(output_dir))

    # ----------------------------------------------------------------------
    @classmethod
    @override
    def Clone(cls, uri, output_dir, branch=None):
        if os.path.isdir(output_dir):
            raise Exception("The directory '{}' already exists and will not be overwritten.".format(output_dir))

        clone_path, clone_name = os.path.split(output_dir)
        FileSystem.MakeDirs(clone_path)

        return cls.Execute(clone_path, 'hg clone{branch} "{uri}" "{name}"'.format( branch=' -b "{}"'.format(branch) if branch else '',
                                                                                   uri=uri,
                                                                                   name=clone_name,
                                                                                 ))

    # ----------------------------------------------------------------------
    @classmethod
    @override
    def GetUniqueName(cls, repo_root):
        result, output = cls.Execute(repo_root, "hg paths", newline=True)
        assert result == 0, (result, output)

        regex = re.compile(r"{}\s*=\s*(?P<value>.+)".format(cls.DefaultBranch))

        for line in output.split('\n'):
            match = regex.match(line)
            if match:
                return match.group("value")

        # If here, we didn't find anything. Most of the time, this
        # is an indication that the repo is local (no remote); return
        # the path.
        return os.path.realpath(repo_root)

    # ----------------------------------------------------------------------
    @classmethod
    @override
    def Who(cls, repo_root):
        result, output = cls.Execute(repo_root, "hg showconfig ui.username")
        assert result == 0, (result, output)

        return output.strip()

    # ----------------------------------------------------------------------
    _cached_roots                           = set()

    @classmethod
    @override
    def GetRoot(cls, repo_dir):
        for k in cls._cached_roots:
            if repo_dir.startswith(k):
                return k

        result, output = cls.Execute( repo_dir,
                                      "hg root",
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
            """\
            This operation will revert any working changes.

            THIS INCLUDES THE FOLLOWING:
                - Any working edits
                - Any files that have been added
            """)):
            return 0, "<<Skipped>>"

        commands = [ "hg update --clean",
                     "hg purge",
                   ]

        return cls.Execute(repo_root, " && ".join(commands))

    # ----------------------------------------------------------------------
    @classmethod
    @override
    def GetBranches(cls, repo_root):
        result, output = cls.Execute(repo_root, "hg branches")
        assert result == 0, (result, output)

        regex = re.compile(r"(?P<name>\S+)\s*(?P<id>.+)")

        for match in regex.finditer(output):
            yield match.group("name")

    # ----------------------------------------------------------------------
    @classmethod
    @override
    def GetCurrentBranch(cls, repo_root):
        result, output = cls.Execute(repo_root, "hg branch")
        assert result == 0, (result, output)

        return output.strip()

    # ----------------------------------------------------------------------
    @classmethod
    @override
    def GetMostRecentBranch(cls, repo_root):
        return cls._GetBranchAssociatedWithChange(repo_root)

    # ----------------------------------------------------------------------
    @classmethod
    @override
    def CreateBranch(cls, repo_root, branch_name):
        return cls.Execute(repo_root, 'hg branch "{}"'.format(branch_name))

    # ----------------------------------------------------------------------
    @classmethod
    @override
    def SetBranch(cls, repo_root, branch_name):
        return cls.Execute(repo_root, 'hg update "{}"'.format(branch_name))

    # ----------------------------------------------------------------------
    @classmethod
    @override
    def HasUntrackedWorkingChanges(cls, repo_root):
        result, output = cls.Execute(repo_root, "hg status")

        for line in output.split('\n'):
            if line.strip().startswith('?'):
                return True

        return False

    # ----------------------------------------------------------------------
    @classmethod
    @override
    def HasWorkingChanges(cls, repo_root):
        result, output = cls.Execute(repo_root, "hg status")

        for line in output.split('\n'):
            line = line.strip()

            if line and not line.startswith('?'):
                return True

        return False

    # ----------------------------------------------------------------------
    @classmethod
    @override
    def GetWorkingChanges(cls, repo_root):
        result, output = cls.Execute(repo_root, 'hg status')
        assert result == 0, (result, output)

        regex = re.compile(r"^(?P<type>\S+)\s+(?P<filename>.+)$")
        
        results = []
        for line in output.split('\n'):
            match = regex.match(line)
            if match:
                results.append(os.path.join(repo_root, match.group("filename")))

        return results

    # ----------------------------------------------------------------------
    @classmethod
    @override
    def GetChangeInfo(cls, repo_root, change):
        result, output = cls.Execute(repo_root, 'hg log --rev "{}"'.format(change))
        assert result == 0, (result, output)

        d = { "user" : None,
              "date" : None,
              "summary" : None,
            }

        for line in output.strip().split('\n'):
            for key in six.iterkeys(d):
                if line.startswith(key):
                    assert d[key] is None
                    d[key] = line[len(key) + 1:].strip()
                    break

        for k, v in six.iteritems(d):
            assert k, v

        d["files"] = cls.GetChangedFiles(repo_root, change)

        return d

    # ----------------------------------------------------------------------
    @classmethod
    @override
    def Commit(cls, repo_root, description, username=None):
        return cls.Execute( repo_root,
                            'hg commit --message "{desc}"{user}'.format( desc=description.replace('"', '\\"'),
                                                                         user=' --user "{}"'.format(username) if username else '',
                                                                       ),
                          )

    # ----------------------------------------------------------------------
    @classmethod
    @override
    def Update(cls, repo_root, update_arg=None):
        return cls.Execute(repo_root, "hg update{}".format(cls._UpdateMergeArgToCommandLine(repo_root, update_arg)))

    # ----------------------------------------------------------------------
    @classmethod
    @override
    def Merge(cls, repo_root, merge_arg):
        return cls.Execute(repo_root, "hg merge{}".format(cls._UpdateMergeArgToCommandLine(repo_root, merge_arg)))

    # ----------------------------------------------------------------------
    @classmethod
    @override
    def GetChangesSinceLastMerge(cls, repo_root, dest_branch, source_merge_arg=None):
        source_branch = None
        additional_filters = []

        # ----------------------------------------------------------------------
        def GetDateOperator(arg):
            if arg is None or arg:
                return '>'

            return '<'

        # ----------------------------------------------------------------------

        if isinstance(source_merge_arg, EmptyUpdateMergeArg):
            source_branch = cls.GetCurrentBranch(repo_root)

        elif isinstance(source_merge_arg, ChangeUpdateMergeArg):
            source_branch = cls._GetBranchAssociatedWithChange(repo_root, source_merge_arg.Change)
            additional_filters.append("{}::".format(source_merge_arg.Change))

        elif isinstance(source_merge_arg, DateUpdateMergeArg):
            source_branch = cls.GetCurrentBranch(repo_root)
            additional_filters.append("date('{}{}')".format( GetDateOperator(source_merge_arg.GreaterThan),
                                                             StringSerialization.SerializeItem(DateTimeTypeInfo(), source_merge_arg.Date, microseconds=False),
                                                           ))

        elif isinstance(source_merge_arg, BranchAndDateUpdateMergeArg):
            source_branch = source_merge_arg.Branch
            additional_filters.append("date('{}{}')".format( GetDateOperator(source_merge_arg.GreaterThan),
                                                             StringSerialization.SerializeItem(DateTimeTypeInfo(), source_merge_arg.Date, microseconds=False),
                                                           ))

        elif isinstance(source_merge_arg, BranchUpdateMergeArg):
            source_branch = source_merge_arg.Branch

        else:
            assert False, type(source_merge_arg)

        filter = "::{} and not ::{}".format(source_branch, dest_branch)
        if additional_filters:
            filter += " and {}".format(" and ".join(additional_filters))

        command_line = r'hg log --branch "{source_branch}" --rev "{filter}" --template "{{rev}}\n"' \
                            .format( source_branch=source_branch,
                                     filter=filter,
                                   )

        result, output = cls.Execute(repo_root, command_line)
        assert result == 0, (result, output)

        return [ line.strip() for line in output.split('\n') if line.strip() ]

    # ----------------------------------------------------------------------
    @classmethod
    @override
    def GetChangedFiles(cls, repo_root, change_or_changes_or_none):
        command_line_template = "hg status"

        if change_or_changes_or_none:
            changes = change_or_changes_or_none if isinstance(change_or_changes_or_none, list) else [ change_or_changes_or_none, ]
            command_line_template += ' --change "{change}"'
        else:
            changes = [ None, ]

        filenames = set()

        for change in changes:
            command_line = command_line_template.format(change=change)

            result, output = cls.Execute(repo_root, command_line)
            assert result == 0, (result, output)

            for line in [ line.strip() for line in output.split('\n') if line.strip() ]:
                assert len(line) > 2 and line[1] == ' ' and line[2] != ' ', line

                filename = os.path.join(repo_root, line[2:])
                if filename not in filenames:
                    filenames.add(filename)

        return sorted(filenames)

    # ----------------------------------------------------------------------
    @classmethod
    @override
    def EnumBlameInfo(cls, repo_root, filename):
        result, output = cls.Execute(repo_root, 'hg blame "{}"'.format(filename))

        if result != 0:
            # Don't produce an error if we are looking at a file that has been renamed/removed.
            if "no such file in" in output:
                return

            assert False, (result, output)

        regex = re.compile('^\s*(?P<change>\d+):\s?(?P<line>.*)$')

        for line in output.split('\n'):
            if not line:
                continue

            match = regex.match(line)
            if not match:
                # Don't produce an error on a failure to enumerate binary files
                if line.endswith("binary file"):
                    return

                assert False, line

            yield match.group("change"), match.group("line")

    # ----------------------------------------------------------------------
    @classmethod
    @override
    def EnumTrackedFiles(cls, repo_root):
        temp_filename = CurrentShell.CreateTempFilename()

        result, output = cls.Execute(repo_root, 'hg status --no-status --clean --added --modified > "{}"'.format(temp_filename))
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
            command_line = 'hg diff --git > "{}"'.format(output_filename)
        else:
            command_line = 'hg export --git --rev "{start}:{end}" > "{filename}"'.format( start=start_change,
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
        return cls.Execute(repo_root, 'hg import{commit} "{filename}"'.format( commit=" --no-commit" if not commit else '',
                                                                               filename=patch_filename,
                                                                             ))
    
    # ----------------------------------------------------------------------
    @classmethod
    @override
    def Reset( cls,
               repo_root, 
               no_prompt=False, 
               no_backup=False,
             ):
        if not no_prompt and not cls.AreYouSurePrompt(textwrap.dedent(
            """\
            This operation will revert your local repository to match the state of the remote repository.

            THIS INCLUDES THE FOLLOWING:
                - Any working edits
                - Any files that have been added
                - Any committed changes that have not been pushed to the remote repository
            """)):
                return 0, ''

        commands = [ 'hg update --clean',
                     'hg purge',
                     'hg strip{no_backup} "roots(outgoing())"'.format(no_backup=" --no-backup" if no_backup else ''),
                   ]

        empty_revision_set_notice = "abort: empty revision set"

        result, output = cls.Execute(repo_root, " && ".join(commands))
        if result != 0 and empty_revision_set_notice in output:
            result = 0
            output = output.replace(empty_revision_set_notice, '')

        return result, "{}\n".format(output.strip())

    # ----------------------------------------------------------------------
    @classmethod
    @override
    def HasUpdateChanges(cls, repo_root):
        result, output = cls.Execute(repo_root, "hg summary")
        return result == 0 and output.find("update: (current)") == -1

    # ----------------------------------------------------------------------
    @classmethod
    @override
    def HasLocalChanges(cls, repo_root):
        result, output = cls.Execute(repo_root, "hg outgoing")
        assert result == 0 or (result == 1 and "no changes found" in output), (result, output)

        return result == 0

    # ----------------------------------------------------------------------
    @classmethod
    @override
    def GetLocalChanges(cls, repo_root):
        output_prefix = "rev:"

        result, output = cls.Execute(repo_root, r'hg outgoing --template "{}{{rev}}\n"'.format(output_prefix))
        assert result == 0 or (result == 1 and "no changes found" in output), (result, output)

        return [ line[len(output_prefix):].strip() for line in output.split('\n') if line.startswith(output_prefix) ]

    # ----------------------------------------------------------------------
    @classmethod
    @override
    def HasRemoteChanges(cls, repo_root):
        result, output = cls.Execute(repo_root, "hg incoming")
        assert result == 0 or (result == 1 and "no changes found" in output), (result, output)

        return result == 0

    # ----------------------------------------------------------------------
    @classmethod
    @override
    def GetRemoteChanges(cls, repo_root):
        output_prefix = "rev:"

        result, output = cls.Execute(repo_root, r'hg incoming --template "{}{{rev}}\n"'.format(output_prefix))
        assert result == 0, (result, output)

        changes = []

        return [ line[len(output_prefix):].strip() for line in output.split('\n') if line.startswith(output_prefix) ]

    # ----------------------------------------------------------------------
    @classmethod
    @override
    def Push(cls, repo_root, create_remote_branch=False):
        return cls.Execute(repo_root, "hg push{}".format(" --new-branch" if create_remote_branch else ''))

    # ----------------------------------------------------------------------
    @classmethod
    @override
    def Pull(cls, repo_root, branch_or_branches=None):
        # In Mercurial, a pull gets all branches; no need to consider branch_or_branches
        result, output = cls.Execute(repo_root, "hg pull")
        if result != 0 and "no changes found" in output:
            result = 0

        return result, output

    # ----------------------------------------------------------------------
    # |  
    # |  Private Methods
    # |  
    # ----------------------------------------------------------------------
    @classmethod
    @override
    def _AddFilesImpl(cls, repo_root, filenames):
        return cls.Execute(repo_root, 'hg add {}'.format(' '.join([ '"{}"'.format(filename) for filename in filenames ])))

    # ----------------------------------------------------------------------
    @classmethod
    def _GetBranchAssociatedWithChange(cls, repo_root, change=None):
        command_line = 'hg log {change} --template "{{branch}}"'.format( change="--rev {}".format(change) if change else "-l 1",
                                                                       )

        result, output = cls.Execute(repo_root, command_line)
        assert result == 0, (result, output)

        return output.strip()

    # ----------------------------------------------------------------------
    @classmethod
    def _UpdateMergeArgToCommandLine(cls, repo_root, arg):
        change = cls._UpdateMergeArgToString(repo_root, arg)
        if not change:
            return ''

        if isinstance(change, six.string_types):
            return ' --rev "{}"'.format(change)

        return ' "{}"'.format(change)

    # ----------------------------------------------------------------------
    @classmethod
    def _UpdateMergeArgToString(cls, repo_root, arg):

        # ----------------------------------------------------------------------
        def NormalizeChange(change):
            try:
                value = int(change)
                if value >= 0:
                    return change

            except ValueError:
                pass

            result, output = cls.Execute(repo_root, 'hg log --rev "{rev_name}" --template "{{rev}}"'.format( rev_name=change,
                                                                                                           ))
            assert result == 0, (result, output)

            return output.strip()

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

            if not operator:
                operator = '<'
            else:
                operator = '>'

            errors = OrderedDict()

            for branch in BranchGenerator():
                command_line = '''hg log --branch "{branch}" --rev "sort(date('{operator}{date}'), -date)" --limit 1 --template "{{rev}}"''' \
                                    .format( branch=branch,
                                             operator=operator,
                                             date=StringSerialization.SerializeItem(DateTimeTypeInfo(), date, microseconds=False),
                                           )

                result, output = cls.Execute(repo_root, command_line, strip=True)

                if result == 0 and output:
                    return output

                errors[command_line] = output

            raise Exception("Change not found ({branch}, {date})\n{errors}".format( branch=branch,
                                                                                    date=date,
                                                                                    errors='\n\n'.join([ "{}\n{}".format(k, v) for k, v in six.iteritems(errors) ]),
                                                                                  ))

        # ----------------------------------------------------------------------

        if arg is None:
            arg = EmptyUpdateMergeArg()

        dispatch_map = { EmptyUpdateMergeArg :                              lambda: "",
                         ChangeUpdateMergeArg :                             lambda: NormalizeChange(arg.Change),
                         DateUpdateMergeArg :                               lambda: DateAndBranch(arg.Date.replace(microsecond=0), None, arg.GreaterThan),
                         BranchUpdateMergeArg :                             lambda: DateAndBranch(DateTimeTypeInfo.Create(microseconds=False), arg.Branch, None),
                         BranchAndDateUpdateMergeArg :                      lambda: DateAndBranch(arg.Date.replace(microsecond=0), arg.Branch, arg.GreaterThan),
                       }

        assert type(arg) in dispatch_map, type(arg)
        return dispatch_map[type(arg)]()
