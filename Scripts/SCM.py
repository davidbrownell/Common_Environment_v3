# ----------------------------------------------------------------------
# |  
# |  SCM.py
# |  
# |  David Brownell <db@DavidBrownell.com>
# |      2018-05-17 19:55:42
# |  
# ----------------------------------------------------------------------
# |  
# |  Copyright David Brownell 2018.
# |  Distributed under the Boost Software License, Version 1.0.
# |  (See accompanying file LICENSE_1_0.txt or copy at http://www.boost.org/LICENSE_1_0.txt)
# |  
# ----------------------------------------------------------------------
"""Tools for use with SourceControlManagement systems"""

import os
import re
import sys
import textwrap

import six

from CommonEnvironment import Describe
from CommonEnvironment import CommandLine
from CommonEnvironment import StringHelpers
from CommonEnvironment.SourceControlManagement import SourceControlManagement, DistributedSourceControlManagement
from CommonEnvironment.SourceControlManagement.All import GetAnySCM, ALL_TYPES as ALL_SCM_TYPES
from CommonEnvironment.SourceControlManagement import UpdateMergeArgs

# ----------------------------------------------------------------------
_script_fullpath = os.path.abspath(__file__) if "python" in sys.executable.lower() else sys.executable
_script_dir, _script_name = os.path.split(_script_fullpath)
# ----------------------------------------------------------------------

_SCM_NAMES                                  = [ _scm.Name for _scm in ALL_SCM_TYPES ]

# <Missing function docstring> pylint: disable = C0111

# ----------------------------------------------------------------------
def _SCMDocstringDecorator(scm_method):
    def Decorator(func):
        func.__doc__ = scm_method.__doc__
        return func

    return Decorator

# ----------------------------------------------------------------------
def CommandLineSuffix():
    return textwrap.dedent(
        """

            The SCM will be auto-detected if not specified. If specified, it can be one of the following values:

        {}

        """).format( '\n'.join([ "    - {}".format(scm.Name) for scm in ALL_SCM_TYPES ]),
                   )

# ----------------------------------------------------------------------
@CommandLine.EntryPoint
@CommandLine.Constraints( directory=CommandLine.DirectoryTypeInfo(arity='?'),
                          output_stream=None,
                        )
def Info( directory=None,
          output_stream=sys.stdout,
        ):
    """Returns information for all known SCMs based on the active directory."""

    directory = directory or os.getcwd()

    col_widths = [ 60, 12, 9, ]
    template = "{name:<%d}  {is_available:<%d}  {is_active:<%d}" % tuple(col_widths)

    # ----------------------------------------------------------------------
    def Display(scm):
        is_available = scm.IsAvailable()

        return template.format( name=scm.Name,
                                is_available="yes" if is_available else "no",
                                is_active="yes" if (is_available and scm.IsActive(directory)) else "no",
                              )

    # ----------------------------------------------------------------------

    output_stream.write(textwrap.dedent(
        """\
        
        {header}
        {sep}
        {values}
        """).format( header=template.format( name="Name",
                                             is_available="Is Available",
                                             is_active="Is Active",
                                           ),
                     sep=template.format(**{ k : v for k, v in zip( [ "name", "is_available", "is_active", ],
                                                                    [ '-' * col_width for col_width in col_widths ],
                                                                  ) }),
                     values='\n'.join([ Display(scm) for scm in ALL_SCM_TYPES ]),
                   ))

# ----------------------------------------------------------------------
@_SCMDocstringDecorator(SourceControlManagement.Create)
@CommandLine.EntryPoint
@CommandLine.Constraints( scm=CommandLine.EnumTypeInfo(_SCM_NAMES),
                          output_dir=CommandLine.DirectoryTypeInfo(ensure_exists=False),
                          output_stream=None,
                        )
def Create( scm,
            output_dir,
            output_stream=sys.stdout,
          ):
    return _Wrap( "Create",
                  lambda directory, scm: scm.Create(output_dir),
                  None,
                  scm,
                  output_stream,
                )

# ----------------------------------------------------------------------
@_SCMDocstringDecorator(SourceControlManagement.Clone)
@CommandLine.EntryPoint
@CommandLine.Constraints( scm=CommandLine.EnumTypeInfo(_SCM_NAMES),
                          uri=CommandLine.StringTypeInfo(),
                          output_dir=CommandLine.DirectoryTypeInfo(ensure_exists=False),
                          branch=CommandLine.StringTypeInfo(arity='?'),
                          output_stream=None,
                        )
def Clone( scm,
           uri,
           output_dir,
           branch=None,
           output_stream=sys.stdout,
         ):
    return _Wrap( "Clone",
                  lambda directory, scm: scm.Clone(uri, output_dir, branch=branch),
                  None,
                  scm,
                  output_stream,
                )

# ----------------------------------------------------------------------
@_SCMDocstringDecorator(SourceControlManagement.GetRoot)
@CommandLine.EntryPoint
@CommandLine.Constraints( directory=CommandLine.DirectoryTypeInfo(arity='?'),
                          scm=CommandLine.EnumTypeInfo(_SCM_NAMES, arity='?'),
                          output_stream=None,
                        )
def GetRoot( directory=None,
             scm=None,
             output_stream=sys.stdout,
           ):
    return _Wrap( "GetRoot", 
                  lambda directory, scm: scm.GetRoot(directory), 
                  directory, 
                  scm, 
                  output_stream,
                )

# ----------------------------------------------------------------------
@_SCMDocstringDecorator(SourceControlManagement.IsRoot)
@CommandLine.EntryPoint
@CommandLine.Constraints( directory=CommandLine.DirectoryTypeInfo(arity='?'),
                          scm=CommandLine.EnumTypeInfo(_SCM_NAMES, arity='?'),
                          output_stream=None,
                        )
def IsRoot( directory=None,
            scm=None,
            output_stream=sys.stdout,
          ):
    return _Wrap( "IsRoot", 
                  lambda directory, scm: scm.IsRoot(directory), 
                  directory, 
                  scm, 
                  output_stream,
                )

# ----------------------------------------------------------------------
@_SCMDocstringDecorator(SourceControlManagement.GetUniqueName)
@CommandLine.EntryPoint
@CommandLine.Constraints( directory=CommandLine.DirectoryTypeInfo(arity='?'),
                          scm=CommandLine.EnumTypeInfo(_SCM_NAMES, arity='?'),
                          output_stream=None,
                        )
def GetUniqueName( directory=None,
                   scm=None,
                   output_stream=sys.stdout,
                 ):
    return _Wrap( "GetUniqueName", 
                  lambda directory, scm: scm.GetUniqueName(directory), 
                  directory, 
                  scm, 
                  output_stream,
                )

# ----------------------------------------------------------------------
@_SCMDocstringDecorator(SourceControlManagement.Who)
@CommandLine.EntryPoint
@CommandLine.Constraints( directory=CommandLine.DirectoryTypeInfo(arity='?'),
                          scm=CommandLine.EnumTypeInfo(_SCM_NAMES, arity='?'),
                          output_stream=None,
                        )
def Who( directory=None,
         scm=None,
         output_stream=sys.stdout,
       ):
    return _Wrap( "Who", 
                  lambda directory, scm: scm.Who(directory), 
                  directory, 
                  scm, 
                  output_stream,
                )

# ----------------------------------------------------------------------
@_SCMDocstringDecorator(SourceControlManagement.HasUntrackedWorkingChanges)
@CommandLine.EntryPoint
@CommandLine.Constraints( directory=CommandLine.DirectoryTypeInfo(arity='?'),
                          scm=CommandLine.EnumTypeInfo(_SCM_NAMES, arity='?'),
                          output_stream=None,
                        )
def HasUntrackedWorkingChanges( directory=None,
                                scm=None,
                                output_stream=sys.stdout,
                              ):
    return _Wrap( "HasUntrackedWorkingChanges", 
                  lambda directory, scm: scm.HasUntrackedWorkingChanges(directory), 
                  directory, 
                  scm, 
                  output_stream,
                )

# ----------------------------------------------------------------------
@_SCMDocstringDecorator(SourceControlManagement.HasWorkingChanges)
@CommandLine.EntryPoint
@CommandLine.Constraints( directory=CommandLine.DirectoryTypeInfo(arity='?'),
                          scm=CommandLine.EnumTypeInfo(_SCM_NAMES, arity='?'),
                          output_stream=None,
                        )
def HasWorkingChanges( directory=None,
                       scm=None,
                       output_stream=sys.stdout,
                     ):
    return _Wrap( "HasWorkingChanges", 
                  lambda directory, scm: scm.HasWorkingChanges(directory), 
                  directory, 
                  scm, 
                  output_stream,
                )

# ----------------------------------------------------------------------
@_SCMDocstringDecorator(SourceControlManagement.GetWorkingChangeStatus)
@CommandLine.EntryPoint
@CommandLine.Constraints( directory=CommandLine.DirectoryTypeInfo(arity='?'),
                          scm=CommandLine.EnumTypeInfo(_SCM_NAMES, arity='?'),
                          output_stream=None,
                        )
def GetWorkingChangeStatus( directory=None,
                            scm=None,
                            output_stream=sys.stdout,
                          ):
    return _Wrap( "GetWorkingChangeStatus", 
                  lambda directory, scm: scm.GetWorkingChangeStatus(directory), 
                  directory, 
                  scm, 
                  output_stream,
                )

# ----------------------------------------------------------------------
@_SCMDocstringDecorator(SourceControlManagement.Clean)
@CommandLine.EntryPoint
@CommandLine.Constraints( directory=CommandLine.DirectoryTypeInfo(arity='?'),
                          scm=CommandLine.EnumTypeInfo(_SCM_NAMES, arity='?'),
                          output_stream=None,
                        )
def Clean( yes=False,
           directory=None,
           scm=None,
           output_stream=sys.stdout,
         ):
    return _Wrap( "Clean", 
                  lambda directory, scm: scm.Clean(directory, no_prompt=yes), 
                  directory, 
                  scm, 
                  output_stream,
                )

# ----------------------------------------------------------------------
@_SCMDocstringDecorator(SourceControlManagement.GetBranches)
@CommandLine.EntryPoint
@CommandLine.Constraints( directory=CommandLine.DirectoryTypeInfo(arity='?'),
                          scm=CommandLine.EnumTypeInfo(_SCM_NAMES, arity='?'),
                          output_stream=None,
                        )
def GetBranches( directory=None,
                 scm=None,
                 output_stream=sys.stdout,
               ):
    return _Wrap( "GetBranches", 
                  lambda directory, scm: list(scm.GetBranches(directory)), 
                  directory, 
                  scm, 
                  output_stream,
                )

# ----------------------------------------------------------------------
@_SCMDocstringDecorator(SourceControlManagement.GetCurrentBranch)
@CommandLine.EntryPoint
@CommandLine.Constraints( directory=CommandLine.DirectoryTypeInfo(arity='?'),
                          scm=CommandLine.EnumTypeInfo(_SCM_NAMES, arity='?'),
                          output_stream=None,
                        )
def GetCurrentBranch( directory=None,
                      scm=None,
                      output_stream=sys.stdout,
                    ):
    return _Wrap( "GetCurrentBranch", 
                  lambda directory, scm: scm.GetCurrentBranch(directory), 
                  directory, 
                  scm, 
                  output_stream,
                )

# ----------------------------------------------------------------------
@_SCMDocstringDecorator(SourceControlManagement.GetCurrentNormalizedBranch)
@CommandLine.EntryPoint
@CommandLine.Constraints( directory=CommandLine.DirectoryTypeInfo(arity='?'),
                          scm=CommandLine.EnumTypeInfo(_SCM_NAMES, arity='?'),
                          output_stream=None,
                        )
def GetCurrentNormalizedBranch( directory=None,
                                scm=None,
                                output_stream=sys.stdout,
                              ):
    return _Wrap( "GetCurrentNormalizedBranch", 
                  lambda directory, scm: scm.GetCurrentNormalizedBranch(directory), 
                  directory, 
                  scm, 
                  output_stream,
                )

# ----------------------------------------------------------------------
@_SCMDocstringDecorator(SourceControlManagement.GetMostRecentBranch)
@CommandLine.EntryPoint
@CommandLine.Constraints( directory=CommandLine.DirectoryTypeInfo(arity='?'),
                          scm=CommandLine.EnumTypeInfo(_SCM_NAMES, arity='?'),
                          output_stream=None,
                        )
def GetMostRecentBranch( directory=None,
                         scm=None,
                         output_stream=sys.stdout,
                       ):
    return _Wrap( "GetMostRecentBranch", 
                  lambda directory, scm: scm.GetMostRecentBranch(directory), 
                  directory, 
                  scm, 
                  output_stream,
                )

# ----------------------------------------------------------------------
@_SCMDocstringDecorator(SourceControlManagement.CreateBranch)
@CommandLine.EntryPoint
@CommandLine.Constraints( branch_name=CommandLine.StringTypeInfo(),
                          directory=CommandLine.DirectoryTypeInfo(arity='?'),
                          scm=CommandLine.EnumTypeInfo(_SCM_NAMES, arity='?'),
                          output_stream=None,
                        )
def CreateBranch( branch_name,
                  directory=None,
                  scm=None,
                  output_stream=sys.stdout,
                ):
    return _Wrap( "CreateBranch", 
                  lambda directory, scm: scm.CreateBranch(directory, branch_name), 
                  directory, 
                  scm, 
                  output_stream,
                )

# ----------------------------------------------------------------------
@_SCMDocstringDecorator(SourceControlManagement.SetBranch)
@CommandLine.EntryPoint
@CommandLine.Constraints( branch_name=CommandLine.StringTypeInfo(),
                          directory=CommandLine.DirectoryTypeInfo(arity='?'),
                          scm=CommandLine.EnumTypeInfo(_SCM_NAMES, arity='?'),
                          output_stream=None,
                        )
def SetBranch( branch_name,
               directory=None,
               scm=None,
               output_stream=sys.stdout,
             ):
    return _Wrap( "SetBranch", 
                  lambda directory, scm: scm.SetBranch(directory, branch_name), 
                  directory, 
                  scm, 
                  output_stream,
                )

# ----------------------------------------------------------------------
@_SCMDocstringDecorator(SourceControlManagement.SetBranchOrDefault)
@CommandLine.EntryPoint
@CommandLine.Constraints( branch_name=CommandLine.StringTypeInfo(),
                          directory=CommandLine.DirectoryTypeInfo(arity='?'),
                          scm=CommandLine.EnumTypeInfo(_SCM_NAMES, arity='?'),
                          output_stream=None,
                        )
def SetBranchOrDefault( branch_name,
                        directory=None,
                        scm=None,
                        output_stream=sys.stdout,
                      ):
    return _Wrap( "SetBranchOrDefault", 
                  lambda directory, scm: scm.SetBranchOrDefault(directory, branch_name), 
                  directory, 
                  scm, 
                  output_stream,
                )

# ----------------------------------------------------------------------
@_SCMDocstringDecorator(SourceControlManagement.GetChangeInfo)
@CommandLine.EntryPoint
@CommandLine.Constraints( change=CommandLine.StringTypeInfo(),
                          directory=CommandLine.DirectoryTypeInfo(arity='?'),
                          scm=CommandLine.EnumTypeInfo(_SCM_NAMES, arity='?'),
                          output_stream=None,
                        )
def GetChangeInfo( change, 
                   directory=None,
                   scm=None,
                   output_stream=sys.stdout,
                 ):
    return _Wrap( "GetChangeInfo", 
                  lambda directory, scm: scm.GetChangeInfo(directory, change), 
                  directory, 
                  scm, 
                  output_stream,
                )

# ----------------------------------------------------------------------
@_SCMDocstringDecorator(SourceControlManagement.AddFiles)
@CommandLine.EntryPoint
@CommandLine.Constraints( file=CommandLine.FilenameTypeInfo(arity='*'),
                          recurse=CommandLine.BoolTypeInfo(arity='?'),
                          include_re=CommandLine.StringTypeInfo(arity='*'),
                          exclude_re=CommandLine.StringTypeInfo(arity='*'),
                          directory=CommandLine.DirectoryTypeInfo(arity='?'),
                          scm=CommandLine.EnumTypeInfo(_SCM_NAMES, arity='?'),
                          output_stream=None,
                        )
def AddFiles( file=None,
              recurse=None,
              include_re=None,
              exclude_re=None,
              directory=None,
              scm=None,
              output_stream=sys.stdout,
            ):
    files = file; del file
    include_res = include_re; del include_re
    exclude_res = exclude_re; del exclude_re

    if recurse is None and (include_res or exclude_res):
        recurse = False

    if files and recurse is not None:
        raise CommandLine.UsageException("'file' or 'recurse' arguments may be provided individually, but not both at the same time.")

    if not files and recurse is None:
        raise CommandLine.UsageException("'file' or 'recurse' must be provided.")

    if recurse is not None and (include_res or exclude_res):
        include_res = [ re.compile(regex) for regex in include_res ]
        exclude_res = [ re.compile(regex) for regex in exclude_res ]

        # ----------------------------------------------------------------------
        def Functor(fullpath):
            return ( (not exclude_res or not any(regex.match(fullpath) for regex in exclude_res)) and
                     (not include_res or any(regex.match(fullpath) for regex in include_res))
                   )

        # ----------------------------------------------------------------------

    else:
        # ----------------------------------------------------------------------
        def Functor(_):
            return True

        # ----------------------------------------------------------------------

    return _Wrap( "AddFiles", 
                  lambda directory, scm: scm.AddFiles( directory,
                                                       file or recurse,
                                                       Functor=Functor,
                                                     ), 
                  directory, 
                  scm, 
                  output_stream,
                )

# ----------------------------------------------------------------------
@_SCMDocstringDecorator(SourceControlManagement.Commit)
@CommandLine.EntryPoint
@CommandLine.Constraints( description=CommandLine.StringTypeInfo(),
                          username=CommandLine.StringTypeInfo(arity='?'),
                          directory=CommandLine.DirectoryTypeInfo(arity='?'),
                          scm=CommandLine.EnumTypeInfo(_SCM_NAMES, arity='?'),
                          output_stream=None,
                        )
def Commit( description,
            username=None,
            directory=None,
            scm=None,
            output_stream=sys.stdout,
          ):
    return _Wrap( "Commit", 
                  lambda directory, scm: scm.Commit(directory, description, username=username), 
                  directory, 
                  scm, 
                  output_stream,
                )

# ----------------------------------------------------------------------
@_SCMDocstringDecorator(SourceControlManagement.Update)
@CommandLine.EntryPoint
@CommandLine.Constraints( change=CommandLine.StringTypeInfo(arity='?'),
                          branch=CommandLine.StringTypeInfo(arity='?'),
                          date=CommandLine.DateTimeTypeInfo(arity='?'),
                          directory=CommandLine.DirectoryTypeInfo(arity='?'),
                          scm=CommandLine.EnumTypeInfo(_SCM_NAMES, arity='?'),
                          output_stream=None,
                        )
def Update( change=None,
            branch=None,
            date=None,
            directory=None,
            scm=None,
            output_stream=sys.stdout,
          ):
    return _Wrap( "Update", 
                  lambda directory, scm: scm.Update(directory, UpdateMergeArgs.FromCommandLine( change=change,
                                                                                                branch=branch,
                                                                                                date=date,
                                                                                              )), 
                  directory, 
                  scm, 
                  output_stream,
                )

# ----------------------------------------------------------------------
@_SCMDocstringDecorator(SourceControlManagement.Merge)
@CommandLine.EntryPoint
@CommandLine.Constraints( change=CommandLine.StringTypeInfo(arity='?'),
                          branch=CommandLine.StringTypeInfo(arity='?'),
                          date=CommandLine.DateTimeTypeInfo(arity='?'),
                          directory=CommandLine.DirectoryTypeInfo(arity='?'),
                          scm=CommandLine.EnumTypeInfo(_SCM_NAMES, arity='?'),
                          output_stream=None,
                        )
def Merge( change=None,
           branch=None,
           date=None,
           directory=None,
           scm=None,
           output_stream=sys.stdout,
         ):
    return _Wrap( "Merge", 
                  lambda directory, scm: scm.Merge(directory, UpdateMergeArgs.FromCommandLine( change=change,
                                                                                               branch=branch,
                                                                                               date=date,
                                                                                             )), 
                  directory, 
                  scm, 
                  output_stream,
                )

# ----------------------------------------------------------------------
@_SCMDocstringDecorator(SourceControlManagement.GetChangesSinceLastMerge)
@CommandLine.EntryPoint
@CommandLine.Constraints( dest_branch=CommandLine.StringTypeInfo(),
                          source_change=CommandLine.StringTypeInfo(arity='?'),
                          source_branch=CommandLine.StringTypeInfo(arity='?'),
                          source_date=CommandLine.DateTimeTypeInfo(arity='?'),
                          source_date_greater_than=CommandLine.BoolTypeInfo(arity='?'),
                          directory=CommandLine.DirectoryTypeInfo(arity='?'),
                          scm=CommandLine.EnumTypeInfo(_SCM_NAMES, arity='?'),
                          output_stream=None,
                        )
def GetChangesSinceLastMerge( dest_branch,
                              source_change=None,
                              source_branch=None,
                              source_date=None,
                              source_date_greater_than=None,
                              directory=None,
                              scm=None,
                              output_stream=sys.stdout,
                            ):
    return _Wrap( "GetChangesSinceLastMerge", 
                  lambda directory, scm: scm.GetChangesSinceLastMerge( directory,
                                                                       dest_branch,
                                                                       UpdateMergeArgs.FromCommandLine( change=source_change,
                                                                                                        branch=source_branch,
                                                                                                        date=source_date,
                                                                                                        date_greater_than=source_date_greater_than,
                                                                                                      ),
                                                                     ), 
                  directory, 
                  scm, 
                  output_stream,
                )

# ----------------------------------------------------------------------
@_SCMDocstringDecorator(SourceControlManagement.GetChangedFiles)
@CommandLine.EntryPoint
@CommandLine.Constraints( change=CommandLine.StringTypeInfo(arity='*'),
                          directory=CommandLine.DirectoryTypeInfo(arity='?'),
                          scm=CommandLine.EnumTypeInfo(_SCM_NAMES, arity='?'),
                          output_stream=None,
                        )
def GetChangedFiles( change=None,
                     directory=None,
                     scm=None,
                     output_stream=sys.stdout,
                   ):
    changes = change; del change
    return _Wrap( "GetChangedFiles", 
                  lambda directory, scm: scm.GetChangedFiles(directory, changes), 
                  directory, 
                  scm, 
                  output_stream,
                )

# ----------------------------------------------------------------------
@_SCMDocstringDecorator(SourceControlManagement.EnumBlameInfo)
@CommandLine.EntryPoint
@CommandLine.Constraints( filename=CommandLine.FilenameTypeInfo(),
                          directory=CommandLine.DirectoryTypeInfo(arity='?'),
                          scm=CommandLine.EnumTypeInfo(_SCM_NAMES, arity='?'),
                          output_stream=None,
                        )
def EnumBlameInfo( filename,
                   directory=None,
                   scm=None,
                   output_stream=sys.stdout,
                 ):
    return _Wrap( "EnumBlameInfo", 
                  lambda directory, scm: list(scm.EnumBlameInfo(directory, filename)), 
                  directory, 
                  scm, 
                  output_stream,
                )

# ----------------------------------------------------------------------
@_SCMDocstringDecorator(SourceControlManagement.EnumTrackedFiles)
@CommandLine.EntryPoint
@CommandLine.Constraints( directory=CommandLine.DirectoryTypeInfo(arity='?'),
                          scm=CommandLine.EnumTypeInfo(_SCM_NAMES, arity='?'),
                          output_stream=None,
                        )
def EnumTrackedFiles( directory=None,
                      scm=None,
                      output_stream=sys.stdout,
                    ):
    return _Wrap( "EnumTrackedFiles", 
                  lambda directory, scm: list(scm.EnumTrackedFiles(directory)), 
                  directory, 
                  scm, 
                  output_stream,
                )

# ----------------------------------------------------------------------
@_SCMDocstringDecorator(SourceControlManagement.CreatePatch)
@CommandLine.EntryPoint
@CommandLine.Constraints( patch_filename=CommandLine.FilenameTypeInfo(ensure_exists=False),
                          start_change=CommandLine.StringTypeInfo(arity='?'),
                          end_change=CommandLine.StringTypeInfo(arity='?'),
                          directory=CommandLine.DirectoryTypeInfo(arity='?'),
                          scm=CommandLine.EnumTypeInfo(_SCM_NAMES, arity='?'),
                          output_stream=None,
                        )
def CreatePatch( patch_filename,
                 start_change=None,
                 end_change=None,
                 directory=None,
                 scm=None,
                 output_stream=sys.stdout,
               ):
    return _Wrap( "CreatePatch", 
                  lambda directory, scm: scm.CreatePatch( directory, 
                                                          patch_filename,
                                                          start_change=start_change,
                                                          end_change=end_change,
                                                        ), 
                  directory, 
                  scm, 
                  output_stream,
                )

# ----------------------------------------------------------------------
@_SCMDocstringDecorator(SourceControlManagement.ApplyPatch)
@CommandLine.EntryPoint
@CommandLine.Constraints( patch_filename=CommandLine.FilenameTypeInfo(),
                          directory=CommandLine.DirectoryTypeInfo(arity='?'),
                          scm=CommandLine.EnumTypeInfo(_SCM_NAMES, arity='?'),
                          output_stream=None,
                        )
def ApplyPatch( patch_filename,
                commit=False,
                directory=None,
                scm=None,
                output_stream=sys.stdout,
              ):
    return _Wrap( "ApplyPatch", 
                  lambda directory, scm: scm.ApplyPatch(directory, patch_filename, commit=commit), 
                  directory, 
                  scm, 
                  output_stream,
                )

# ----------------------------------------------------------------------
@_SCMDocstringDecorator(DistributedSourceControlManagement.Reset)
@CommandLine.EntryPoint
@CommandLine.Constraints( directory=CommandLine.DirectoryTypeInfo(arity='?'),
                          scm=CommandLine.EnumTypeInfo(_SCM_NAMES, arity='?'),
                          output_stream=None,
                        )
def Reset( yes=False,
           skip_backup=False,
           directory=None,
           scm=None,
           output_stream=sys.stdout,
         ):
    return _Wrap( "Reset", 
                  lambda directory, scm: scm.Reset( directory,
                                                    no_prompt=yes,
                                                    no_backup=skip_backup,
                                                  ), 
                  directory, 
                  scm, 
                  output_stream,
                  requires_distributed=True,
                )

# ----------------------------------------------------------------------
@_SCMDocstringDecorator(DistributedSourceControlManagement.HasUpdateChanges)
@CommandLine.EntryPoint
@CommandLine.Constraints( directory=CommandLine.DirectoryTypeInfo(arity='?'),
                          scm=CommandLine.EnumTypeInfo(_SCM_NAMES, arity='?'),
                          output_stream=None,
                        )
def HasUpdateChanges( directory=None,
                      scm=None,
                      output_stream=sys.stdout,
                    ):
    return _Wrap( "HasUpdateChanges", 
                  lambda directory, scm: scm.HasUpdateChanges(directory), 
                  directory, 
                  scm, 
                  output_stream,
                  requires_distributed=True,
                )

# ----------------------------------------------------------------------
@_SCMDocstringDecorator(DistributedSourceControlManagement.HasLocalChanges)
@CommandLine.EntryPoint
@CommandLine.Constraints( directory=CommandLine.DirectoryTypeInfo(arity='?'),
                          scm=CommandLine.EnumTypeInfo(_SCM_NAMES, arity='?'),
                          output_stream=None,
                        )
def HasLocalChanges( directory=None,
                     scm=None,
                     output_stream=sys.stdout,
                   ):
    return _Wrap( "HasLocalChanges", 
                  lambda directory, scm: scm.HasLocalChanges(directory), 
                  directory, 
                  scm, 
                  output_stream,
                  requires_distributed=True,
                )

# ----------------------------------------------------------------------
@_SCMDocstringDecorator(DistributedSourceControlManagement.GetLocalChanges)
@CommandLine.EntryPoint
@CommandLine.Constraints( directory=CommandLine.DirectoryTypeInfo(arity='?'),
                          scm=CommandLine.EnumTypeInfo(_SCM_NAMES, arity='?'),
                          output_stream=None,
                        )
def GetLocalChanges( directory=None,
                     scm=None,
                     output_stream=sys.stdout,
                   ):
    return _Wrap( "GetLocalChanges", 
                  lambda directory, scm: scm.GetLocalChanges(directory), 
                  directory, 
                  scm, 
                  output_stream,
                  requires_distributed=True,
                )

# ----------------------------------------------------------------------
@_SCMDocstringDecorator(DistributedSourceControlManagement.HasRemoteChanges)
@CommandLine.EntryPoint
@CommandLine.Constraints( directory=CommandLine.DirectoryTypeInfo(arity='?'),
                          scm=CommandLine.EnumTypeInfo(_SCM_NAMES, arity='?'),
                          output_stream=None,
                        )
def HasRemoteChanges( directory=None,
                      scm=None,
                      output_stream=sys.stdout,
                    ):
    return _Wrap( "HasRemoteChanges", 
                  lambda directory, scm: scm.HasRemoteChanges(directory), 
                  directory, 
                  scm, 
                  output_stream,
                  requires_distributed=True,
                )

# ----------------------------------------------------------------------
@_SCMDocstringDecorator(DistributedSourceControlManagement.GetRemoteChanges)
@CommandLine.EntryPoint
@CommandLine.Constraints( directory=CommandLine.DirectoryTypeInfo(arity='?'),
                          scm=CommandLine.EnumTypeInfo(_SCM_NAMES, arity='?'),
                          output_stream=None,
                        )
def GetRemoteChanges( directory=None,
                      scm=None,
                      output_stream=sys.stdout,
                    ):
    return _Wrap( "GetRemoteChanges", 
                  lambda directory, scm: scm.GetRemoteChanges(directory), 
                  directory, 
                  scm, 
                  output_stream,
                  requires_distributed=True,
                )

# ----------------------------------------------------------------------
@_SCMDocstringDecorator(DistributedSourceControlManagement.GetChangeStatus)
@CommandLine.EntryPoint
@CommandLine.Constraints( directory=CommandLine.DirectoryTypeInfo(arity='?'),
                          scm=CommandLine.EnumTypeInfo(_SCM_NAMES, arity='?'),
                          output_stream=None,
                        )
def GetChangeStatus( directory=None,
                     scm=None,
                     output_stream=sys.stdout,
                   ):
    return _Wrap( "GetChangeStatus", 
                  lambda directory, scm: scm.GetChangeStatus(directory), 
                  directory, 
                  scm, 
                  output_stream,
                  requires_distributed=True,
                )

# ----------------------------------------------------------------------
@_SCMDocstringDecorator(DistributedSourceControlManagement.Push)
@CommandLine.EntryPoint
@CommandLine.Constraints( directory=CommandLine.DirectoryTypeInfo(arity='?'),
                          scm=CommandLine.EnumTypeInfo(_SCM_NAMES, arity='?'),
                          output_stream=None,
                        )
def Push( create_remote_branch=False,
          directory=None,
          scm=None,
          output_stream=sys.stdout,
        ):
    return _Wrap( "Push", 
                  lambda directory, scm: scm.Push(directory, create_remote_branch=create_remote_branch), 
                  directory, 
                  scm, 
                  output_stream,
                  requires_distributed=True,
                )

# ----------------------------------------------------------------------
@_SCMDocstringDecorator(DistributedSourceControlManagement.Pull)
@CommandLine.EntryPoint
@CommandLine.Constraints( branch=CommandLine.StringTypeInfo(arity='*'),
                          directory=CommandLine.DirectoryTypeInfo(arity='?'),
                          scm=CommandLine.EnumTypeInfo(_SCM_NAMES, arity='?'),
                          output_stream=None,
                        )
def Pull( branch=None,
          directory=None,
          scm=None,
          output_stream=sys.stdout,
        ):
    branches = branch; del branch

    return _Wrap( "Pull", 
                  lambda directory, scm: scm.Pull(directory, branches), 
                  directory, 
                  scm, 
                  output_stream,
                  requires_distributed=True,
                )

# ----------------------------------------------------------------------
# ----------------------------------------------------------------------
# ----------------------------------------------------------------------
# TODO: AllChangeStatus
# TODO: AllWorkingChangeStatus
# TODO: UpdateAll
# TOOD: PushAll
# TODO: PullAll
# TODO: PullAndUpdateAll


# TODO: Reorder these methods so that they make more logical sense.


# ----------------------------------------------------------------------
# ----------------------------------------------------------------------
# ----------------------------------------------------------------------
def _Wrap( method_name, 
           callback, 
           directory, 
           scm, 
           output_stream,
           requires_distributed=False,
         ):
    directory = directory or os.getcwd()

    if scm:
        scm = next(potential_scm for potential_scm in ALL_SCM_TYPES if potential_scm.Name == scm)
        assert scm
    else:
        try:
            scm = GetAnySCM( directory, 
                             by_repository_id=False,
                           )
        except Exception as ex:
            output_stream.write("ERROR: {}\n".format(str(ex)))
            return -1

    if requires_distributed and not scm.IsDistributed:
        output_stream.write("'{}' is not a distributes Source Control Management system, which is a requirement for this functionality.\n".format(scm.Name))
        return -1

    result = callback(directory, scm)

    if isinstance(result, tuple) and len(result) == 2 and isinstance(result[0], int) and isinstance(result[1], six.string_types):
        result, output = result
    else:
        output = result
        result = 0
    
    sink = six.moves.StringIO()
    Describe(output, sink)
    sink = sink.getvalue()

    output_stream.write(textwrap.dedent(
        """\

        Method Name:            {method}
        Working Directory:      {working}
        Return Code:            {result}
        Output:                 {output}
        """).format( method=method_name,
                     working=directory,
                     result=result,
                     output=StringHelpers.LeftJustify(sink.strip(), 24),
                   ))

    return 0

# ----------------------------------------------------------------------
# ----------------------------------------------------------------------
# ----------------------------------------------------------------------
if __name__ == "__main__":
    try: sys.exit(CommandLine.Main())
    except KeyboardInterrupt: pass
