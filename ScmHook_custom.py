# ----------------------------------------------------------------------
# |  
# |  ScmHook_custom.py
# |  
# |  David Brownell <db@DavidBrownell.com>
# |      2018-05-07 13:21:00
# |  
# ----------------------------------------------------------------------
# |  
# |  Copyright David Brownell 2018-20.
# |  Distributed under the Boost Software License, Version 1.0.
# |  (See accompanying file LICENSE_1_0.txt or copy at http://www.boost.org/LICENSE_1_0.txt)
# |  
# ----------------------------------------------------------------------
"""Contains SCM hooks"""

import itertools
import os
import sys
import textwrap

from collections import OrderedDict

import inflect as inflect_mod
import six

sys.path.insert(0, os.getenv("DEVELOPMENT_ENVIRONMENT_FUNDAMENTAL"))
from RepositoryBootstrap.Impl import CommonEnvironmentImports
del sys.path[0]

# ----------------------------------------------------------------------
_script_fullpath = CommonEnvironmentImports.CommonEnvironment.ThisFullpath()
_script_dir, _script_name = os.path.split(_script_fullpath)
# ----------------------------------------------------------------------

FileSystem                                  = CommonEnvironmentImports.FileSystem

# ----------------------------------------------------------------------

inflect                                     = inflect_mod.engine()

# ----------------------------------------------------------------------
def OnCommitting(data, output_stream):
    """
    Called when the repository is in the process of committing (but not 
    yet committed); return -1 or raise an exception to prevent the change 
    from being committed to the local repository.

    If the method includes the 'configuration' argument, it will be called
    once for each configuration defined by the repository. If the method
    doesn't include the value, it will only be called once.
    """

    output_stream.write("Validating file sizes...")
    with output_stream.DoneManager() as dm:
        errors = OrderedDict()
        max_size = 95 * 1024 * 1024 # 95 MB
        
        for filename in itertools.chain(data.modified, data.added):
            this_size = os.path.getsize(filename)

            if this_size > max_size:
                errors[filename] = this_size

        if errors:
            dm.stream.write(textwrap.dedent(
                """\
                ERROR: {this} {file} {is_} greater than {size}:
                
                {errors}

                """).format( this=inflect.plural_adj("this", len(errors)).capitalize(),
                             file=inflect.plural("file", len(errors)),
                             is_=inflect.plural("is", len(errors)),
                             size=FileSystem.GetSizeDisplay(max_size),
                             errors='\n'.join([ "    - {} ({})".format(k, FileSystem.GetSizeDisplay(v)) for k, v in six.iteritems(errors) ]),
                           ))

            dm.result = -1
            return dm.result

    # Check for changes in .hgignore/.gitignore
    output_stream.write("Validating change groups...")
    with output_stream.DoneManager() as dm:
        allow_sentinel = "allow invalid change groups"

        if allow_sentinel not in data.description.lower():
            current_dir = os.getcwd()       # This file is run from the repository's root

            # ----------------------------------------------------------------------
            class ItemInfo(object):
                def __init__(self, item_name):
                    self.Exists             = os.path.isfile(os.path.join(current_dir, item_name.replace('/', os.path.sep)))
                    self.Changed            = False

            # ----------------------------------------------------------------------

            all_groups = [ [ ".hgignore", ".gitignore", ],
                           [ "readme.rst", "readme.md", ],
                         ]

            changes = {}

            for groups in all_groups:
                for item in groups:
                    changes[item] = ItemInfo(item)

            for filename in itertools.chain(data.modified, data.added):
                filename = FileSystem.TrimPath(filename, current_dir)
                
                if filename in changes:
                    changes[filename].Changed = True

            errors = []

            for group in all_groups:
                has_changes = None

                for item in group:
                    if changes[item].Exists:
                        if changes[item].Changed != has_changes and has_changes is not None:
                            errors.append(group)
                            break

                        has_changes = changes[item].Changed

            if errors:
                dm.stream.write(textwrap.dedent(
                    """\
                    ERROR: {this} {change} must be grouped with changes to other item(s). To disable this check, include the text '{sentinel}' in the change description.

                    {errors}

                           The tool 'pandoc' (in the Tools directory) can be used to automatically convert from one file format to another.

                           Examples:
                               pandoc readme.rst -o readme.md
                               pandoc readme.md -o readme.rst

                    """).format( this=inflect.plural("this", len(errors)).capitalize(),
                                 change=inflect.plural("change", len(errors)),
                                 sentinel=allow_sentinel,
                                 errors='\n'.join([ "    - {}".format(', '.join(error)) for error in errors ]),
                               ))

                dm.result = -1
                return dm.result

    # Check for 'bugbug'
    output_stream.write("Checking for banned text...")
    with output_stream.DoneManager() as dm:
        allow_sentinel = "allow banned text"

        if allow_sentinel not in data.description.lower():
            errors = []

            for filename in itertools.chain(data.modified, data.added):
                try:
                    content = open(filename).read()

                    if "bugbug" in content.lower():
                        errors.append(filename)
                except UnicodeDecodeError:
                    # If here, we are likely looking at a binary file.
                    pass

            if errors:
                dm.stream.write(textwrap.dedent(
                    """\
                    ERROR: {this} {change} contained the banned text 'BugBug'. To disable this check, include the text '{sentinel}' in the change description.

                    {errors}

                    """).format( this=inflect.plural("this", len(errors)).capitalize(),
                                 change=inflect.plural("change", len(errors)),
                                 sentinel=allow_sentinel,
                                 errors='\n'.join([ "    - {}".format(error) for error in errors ]),
                               ))

                dm.result = -1
                return dm.result

# ----------------------------------------------------------------------
def OnPulled(data, output_stream): # , configuration):
    """
    Called when the repository is in the process of pulling (but has not 
    yet committed the pulled changes); return -1 or raise an exception to 
    prevent the remote change from being persisted.

    If the method includes the 'configuration' argument, it will be called
    once for each configuration defined by the repository. If the method
    doesn't include the value, it will only be called once.
    """

    # TODO: Implement similar functionality as commit
    return
