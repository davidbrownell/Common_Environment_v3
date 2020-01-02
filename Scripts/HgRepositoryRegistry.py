# ----------------------------------------------------------------------
# |  
# |  HgRepositoryRegistry.py
# |  
# |  David Brownell <db@DavidBrownell.com>
# |      2018-05-30 21:24:52
# |  
# ----------------------------------------------------------------------
# |  
# |  Copyright David Brownell 2018-20.
# |  Distributed under the Boost Software License, Version 1.0.
# |  (See accompanying file LICENSE_1_0.txt or copy at http://www.boost.org/LICENSE_1_0.txt)
# |  
# ----------------------------------------------------------------------
"""Updates the hg repository registry on the local machine"""

import os
import sys
import textwrap

from collections import OrderedDict

import inflect as inflect_mod
import six

import CommonEnvironment
from CommonEnvironment import CommandLine
from CommonEnvironment import FileSystem
from CommonEnvironment.SourceControlManagement.All import EnumSCMs
from CommonEnvironment.StreamDecorator import StreamDecorator
from CommonEnvironment import StringHelpers

# ----------------------------------------------------------------------
_script_fullpath = CommonEnvironment.ThisFullpath()
_script_dir, _script_name = os.path.split(_script_fullpath)
# ----------------------------------------------------------------------

inflect                                     = inflect_mod.engine()

# ----------------------------------------------------------------------
@CommandLine.EntryPoint
@CommandLine.Constraints( root_dir=CommandLine.DirectoryTypeInfo(),
                          output_stream=None,
                        )
def EntryPoint( root_dir,
                output_stream=sys.stdout,
              ):
    with StreamDecorator(output_stream).DoneManager( line_prefix='',
                                                     prefix="\nResults: ",
                                                     suffix='\n',
                                                   ) as dm:
        repositories = []

        dm.stream.write("\nSearching for repositories in '{}'...".format(root_dir))
        with dm.stream.DoneManager( done_suffix=lambda: inflect.no("repository", len(repositories)),
                                  ):
            for scm, directory in EnumSCMs(root_dir):
                if scm.Name != "Mercurial":
                    continue

                repositories.append(directory)

        # Organize the repos
        dm.stream.write("Organizing...")
        with dm.stream.DoneManager():
            repo_dict = OrderedDict()

            common_prefix = FileSystem.GetCommonPath(*repositories)
            common_prefix_len = len(common_prefix)

            for repository in repositories:
                suffix = repository[common_prefix_len:]

                parts = suffix.split(os.path.sep)

                repo_name = parts[-1]
                prefixes = parts[:-1]

                rd = repo_dict
                for prefix in prefixes:
                    rd.setdefault(prefix, OrderedDict())
                    rd = rd[prefix]

                rd[repo_name] = repository

        # Write the content
        dm.stream.write("Writing TortoiseHg content...")
        with dm.stream.DoneManager():
            filename = os.path.join(os.getenv("APPDATA"), "TortoiseHg", "thg-reporegistry.xml")
            assert os.path.isfile(filename), filename

            with open(filename, 'w') as f:
                # ----------------------------------------------------------------------
                def GenerateContent(root, is_root):
                    items = []

                    for k, v in six.iteritems(root):
                        if isinstance(v, six.string_types):
                            items.append('<repo root="{}" shortname="{}" />\n'.format( v,
                                                                                       os.path.basename(k),
                                                                                     ))
                        else:
                            tag_name = "allgroup" if is_root else "group"

                            items.append(textwrap.dedent(
                                """\
                                <{tag_name} name="{name}">
                                  {content}
                                </{tag_name}>
                                """).format( tag_name=tag_name,
                                             name=k,
                                             content=StringHelpers.LeftJustify(GenerateContent(v, False), 2).rstrip(),
                                           ))

                    return ''.join(items)

                # ----------------------------------------------------------------------

                f.write(textwrap.dedent(
                    """\
                    <?xml version="1.0" encoding="UTF-8"?>
                    <reporegistry>
                      <treeitem>
                    {}
                      </treeitem>
                    </reporegistry>
                    """).format(StringHelpers.LeftJustify( GenerateContent(repo_dict, True).rstrip(),
                                                           4,
                                                           skip_first_line=False,
                                                         )))
        return dm.result

# ----------------------------------------------------------------------
# ----------------------------------------------------------------------
# ----------------------------------------------------------------------
if __name__ == "__main__":
    try: sys.exit(CommandLine.Main())
    except KeyboardInterrupt: pass