# ----------------------------------------------------------------------
# |  
# |  CleanRepoData.py
# |  
# |  David Brownell <db@DavidBrownell.com>
# |      2018-05-29 11:18:04
# |  
# ----------------------------------------------------------------------
# |  
# |  Copyright David Brownell 2018.
# |  Distributed under the Boost Software License, Version 1.0.
# |  (See accompanying file LICENSE_1_0.txt or copy at http://www.boost.org/LICENSE_1_0.txt)
# |  
# ----------------------------------------------------------------------
"""
Activating a repository creates temporary state information that is required with the associated
environment is active. This script removes that information that is no longer useful.
"""

import datetime
import os
import stat
import sys
import textwrap
import time

from collections import namedtuple

import inflect as inflect_mod
import six

import CommonEnvironment
from CommonEnvironment.CallOnExit import CallOnExit
from CommonEnvironment import CommandLine
from CommonEnvironment import FileSystem
from CommonEnvironment.Shell.All import CurrentShell
from CommonEnvironment.StreamDecorator import StreamDecorator
from CommonEnvironment.TypeInfo.FundamentalTypes.DurationTypeInfo import DurationTypeInfo

# ----------------------------------------------------------------------
_script_fullpath = CommonEnvironment.ThisFullpath()
_script_dir, _script_name = os.path.split(_script_fullpath)
# ----------------------------------------------------------------------

inflect                                     = inflect_mod.engine()

assert os.getenv("DEVELOPMENT_ENVIRONMENT_FUNDAMENTAL")
sys.path.insert(0, os.getenv("DEVELOPMENT_ENVIRONMENT_FUNDAMENTAL"))
with CallOnExit(lambda: sys.path.pop(0)):
    from RepositoryBootstrap import Constants as RepositoryBootstrapConstants

# ----------------------------------------------------------------------
@CommandLine.EntryPoint( delete_before=CommandLine.EntryPoint.Parameter("Delete files that are older than this value"),
                       )
@CommandLine.Constraints( delete_before=DurationTypeInfo(arity='?'),
                          output_stream=None,
                        )
def EntryPoint( delete_before=datetime.timedelta(days=7),
                yes=False,
                output_stream=sys.stdout,
                verbose=False,
              ):
    with StreamDecorator(output_stream).DoneManager( line_prefix='',
                                                     prefix="\nResults: ",
                                                     suffix='\n',
                                                   ) as dm:
        verbose_stream = StreamDecorator(dm.stream if verbose else None, line_prefix="INFO: ")

        # Find the files

        # ----------------------------------------------------------------------
        FileInfo                            = namedtuple( "FileInfo",
                                                          [ "Name",
                                                            "Type",
                                                            "Fullpath",
                                                            "Age",
                                                            "Size",
                                                          ],
                                                        )

        # ----------------------------------------------------------------------

        t = time.time()

        dm.stream.write("Searching for files...")
        with dm.stream.DoneManager( suffix='\n',
                                  ):
            file_infos = []

            for filename in FileSystem.WalkFiles( CurrentShell.TempDirectory,
                                                  include_file_extensions=[ RepositoryBootstrapConstants.TEMPORARY_FILE_EXTENSION, ],
                                                ):
                name = os.path.splitext(os.path.basename(filename))[0].split('.')

                if len(name) == 1:
                    type_ = ''
                    name = name[0]
                else:
                    type_ = name[-1]
                    name = '.'.join(name[:-1])

                file_infos.append(FileInfo( name,
                                            type_,
                                            filename,
                                            datetime.timedelta(seconds=t - os.stat(filename)[stat.ST_MTIME]),
                                            os.stat(filename)[stat.ST_SIZE],
                                          ))

        if not file_infos:
            dm.stream.write("No files were found.\n")
            return dm.result

        dm.stream.write("{} {} found.\n".format( inflect.no("file", len(file_infos)),
                                                 inflect.plural("was", len(file_infos)),
                                               ))

        verbose_stream.write("\nFiles found:\n{}\n\n".format( '\n'.join([ fi.Fullpath for fi in file_infos ])))

        # Trim the list based on age
        file_infos = [ fi for fi in file_infos if fi.Age >= delete_before ]

        if not file_infos:
            dm.stream.write("No files were found older than {}.\n".format(delete_before))
            return dm.result

        if not yes:
            total_size = 0
            for fi in file_infos:
                total_size += fi.Size

            dm.stream.write(textwrap.dedent(
                """\

                Would you like to delete these files:

                    Name                        Type                Size               Age (days)                      Fullpath
                    --------------------------  ------------------  -----------------  ------------------------------  -----------------------------------------------
                {files}

                ? ({total_size}) [y/N] """).format( files='\n'.join([ "    {name:<26}  {type:18}  {size:<17}  {age:<30}  {fullpath}".format( name=fi.Name,
                                                                                                                                             type=fi.Type,
                                                                                                                                             size=FileSystem.GetSizeDisplay(fi.Size),
                                                                                                                                             age=str(fi.Age),
                                                                                                                                             fullpath=fi.Fullpath,
                                                                                                                                           )
                                                                      for fi in file_infos
                                                                    ]),
                                                    total_size=FileSystem.GetSizeDisplay(total_size),
                                                  ))

            value = six.moves.input().strip()
            if not value:
                value = 'N'

            value = value.lower()

            if value in [ "0", "n", "no", ]:
                return dm.result

        dm.stream.write("\nRemoving files...")
        with dm.stream.DoneManager() as this_dm:
            for index, fi in enumerate(file_infos):
                this_dm.stream.write("Removing '{}' ({} of {})...".format( fi.Fullpath,
                                                                           index + 1,
                                                                           len(file_infos),
                                                                         ))
                with this_dm.stream.DoneManager():
                    FileSystem.RemoveFile(fi.Fullpath)

        return dm.result

# ----------------------------------------------------------------------
# ----------------------------------------------------------------------
# ----------------------------------------------------------------------
if __name__ == "__main__":
    try: sys.exit(CommandLine.Main())
    except KeyboardInterrupt: pass
