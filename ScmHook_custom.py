# ----------------------------------------------------------------------
# |  
# |  ScmHook_custom.py
# |  
# |  David Brownell <db@DavidBrownell.com>
# |      2018-05-07 13:21:00
# |  
# ----------------------------------------------------------------------
# |  
# |  Copyright David Brownell 2018.
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

# ----------------------------------------------------------------------
_script_fullpath = os.path.abspath(__file__) if "python" in sys.executable.lower() else sys.executable
_script_dir, _script_name = os.path.split(_script_fullpath)
# ----------------------------------------------------------------------

sys.path.insert(0, os.getenv("DEVELOPMENT_ENVIRONMENT_FUNDAMENTAL"))
from RepositoryBootstrap.Impl import CommonEnvironmentImports
del sys.path[0]

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
                             size=CommonEnvironmentImports.FileSystem.GetSizeDisplay(max_size),
                             errors='\n'.join([ "    - {} ({})".format(k, CommonEnvironmentImports.FileSystem.GetSizeDisplay(v)) for k, v in six.iteritems(errors) ]),
                           ))

            dm.result = -1
            return dm.result

    # Check for changes in .hgignore/.gitignore
    output_stream.write("Validating change groups...")
    with output_stream.DoneManager() as dm:
        allow_sentinel = "allow invalid change groups"

        if allow_sentinel not in data.description.lower():
            all_groups = [ [ ".hgignore", ".gitignore", ],
                           [ "readme.rst", "readme.md", ],
                         ]

            changes = {}

            for groups in all_groups:
                for item in groups:
                    changes[item] = False

            for filename in itertools.chain(data.modified, data.added):
                base_name = os.path.basename(filename)

                if base_name in changes:
                    changes[base_name] = True

            errors = []

            for group in all_groups:
                count = 0

                for item in group:
                    if changes[item]:
                        count += 1

                if count and count != len(group):
                    errors.append(group)

            if errors:
                dm.stream.write(textwrap.dedent(
                    """\
                    ERROR: {this} {change} must be grouped with changes to other item(s). To disable this check, include the text '{sentinel}' in the change description.

                    {errors}
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
