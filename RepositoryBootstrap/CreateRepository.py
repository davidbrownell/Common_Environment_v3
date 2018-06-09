# ----------------------------------------------------------------------
# |  
# |  CreateRepository.py
# |  
# |  David Brownell <db@DavidBrownell.com>
# |      2018-05-18 17:01:49
# |  
# ----------------------------------------------------------------------
# |  
# |  Copyright David Brownell 2018.
# |  Distributed under the Boost Software License, Version 1.0.
# |  (See accompanying file LICENSE_1_0.txt or copy at http://www.boost.org/LICENSE_1_0.txt)
# |  
# ----------------------------------------------------------------------
"""Initializes a repository with bootstrapping files"""

import os
import shutil
import sys
import textwrap
import uuid

import inflect as inflect_mod
import six

from CommonEnvironment.CallOnExit import CallOnExit
from CommonEnvironment import CommandLine
from CommonEnvironment.StreamDecorator import StreamDecorator

# ----------------------------------------------------------------------
_script_fullpath = os.path.abspath(__file__) if "python" in sys.executable.lower() else sys.executable
_script_dir, _script_name = os.path.split(_script_fullpath)
# ----------------------------------------------------------------------

inflect                                     = inflect_mod.engine()

# ----------------------------------------------------------------------
@CommandLine.EntryPoint
@CommandLine.Constraints( repo_dir=CommandLine.DirectoryTypeInfo(),
                          repo_name=CommandLine.StringTypeInfo(),
                          output_stream=None,
                        )
def EntryPoint( repo_dir,
                repo_name,
                output_stream=sys.stdout,
              ):
    with StreamDecorator(output_stream).DoneManager( line_prefix='',
                                                     prefix="\nResults: ",
                                                     suffix='\n',
                                                   ) as dm:
        # Prompt for the files to copy
        support_git = _Prompt("Support Git? ", "yes").lower() in [ "yes", "y", ]
        support_hg = _Prompt("Support Hg? ", "yes").lower() in [ "yes", "y", ]
        support_windows = _Prompt("Support Windows? ", "yes").lower() in [ "yes", "y", ]

        if support_windows:
            support_powershell = _Prompt("Support PowerShell on Windows? ", "yes").lower() in [ "yes", "y", ]
        else:
            support_powershell = False

        support_linux = _Prompt("Support Linux? ", "yes").lower() in [ "yes", "y", ]

        include_boost_license = _Prompt("Include the boost software license (https://www.boost.org/users/license.html)? ", "no").lower() in [ "yes", "y", ]

        if not (support_git or support_hg):
            raise Exception("At least one of Git or Hg must be supported")
        if not (support_windows or support_powershell or support_linux):
            raise Exception("At least one of Windows, PowerShell, or Linux must be supported")

        # Get a list of the files based on feedback
        filenames = [ "Activate_custom.py",
                      "ScmHook_custom.py",
                      "Setup_custom.py",
                      "Readme.rst",
                    ] 

        if support_git:                     
            filenames += [ ".gitignore", ]

        if support_hg:                      
            filenames += [ ".hgignore", ]

        if support_windows:
            filenames.append("Setup.cmd")
        if support_powershell:
            filenames.append("Setup.ps1")
        if support_linux:
            filenames.append("Setup.sh")

        if include_boost_license:
            filenames.append("LICENSE_1_0.txt")

        dm.stream.write("\n\nPopulating {}...".format(inflect.no("file", len(filenames) + 1)))
        with dm.stream.DoneManager() as this_dm:
            for filename in filenames:
                dest_filename = os.path.join(repo_dir, filename)

                if os.path.exists(dest_filename):
                    continue

                source_filename = os.path.join(_script_dir, "Templates", filename)
                assert os.path.isfile(source_filename), source_filename

                shutil.copy2(source_filename, dest_filename)

            # Create the repo id
            sys.path.insert(0, os.getenv("DEVELOPMENT_ENVIRONMENT_FUNDAMENTAL"))
            with CallOnExit(lambda: sys.path.pop(0)):
                from RepositoryBootstrap import Constants as RepositoryBootstrapConstants

            dest_filename = os.path.join(repo_dir, RepositoryBootstrapConstants.REPOSITORY_ID_FILENAME)
            if not os.path.exists(dest_filename):
                with open(dest_filename, 'w') as f:
                    f.write(RepositoryBootstrapConstants.REPOSITORY_ID_CONTENT_TEMPLATE.format( name=repo_name,
                                                                                                id=str(uuid.uuid4()).replace('-', '').upper(),
                                                                                              ))

        dm.stream.write(textwrap.dedent(
            """\

            Repository information has been created at: {repo_dir}

            To begin using this repository...

                1) {setup}
                   
                   Edit this file and add dependencies and any custom setup actions (if necessary). The template copied is
                   preconfigured to raise exceptions when these methods are first invoked; you can remove these exceptions once 
                   you have configured all setup activites.

                2) {activate}

                   Edit this file and add any custom activation actions (if necessary). The template copied is preconfigured
                   to raise an exception when this method is first invoked; you can remove this exception once you have 
                   configured all activation activities.

                3) [OPTIONAL] {scm_hook}

                   Edit this file and add any custom Committing, Pushing, or Pulled validation events. Repositories will
                   rarely modify this file; the template is not preconfigured to raise exceptions when these methods are
                   invoked.

            See <Common_Environment>/Readme.rst[.md] for more information.

            """).format( repo_dir=repo_dir,
                         setup=os.path.join(repo_dir, RepositoryBootstrapConstants.SETUP_ENVIRONMENT_CUSTOMIZATION_FILENAME),
                         activate=os.path.join(repo_dir, RepositoryBootstrapConstants.ACTIVATE_ENVIRONMENT_CUSTOMIZATION_FILENAME),
                         scm_hook=os.path.join(repo_dir, RepositoryBootstrapConstants.HOOK_ENVIRONMENT_CUSTOMIZATION_FILENAME),
                       ))

        return dm.result

# ----------------------------------------------------------------------
def _Prompt( prompt,
             default_value=None,
           ):
    while True:
        if default_value is not None:
            prompt += "[{}] ".format(default_value)

        result = six.moves.input(prompt).strip()
        if not result and default_value is not None:
            result = default_value

        if result:
            return result

# ----------------------------------------------------------------------
# ----------------------------------------------------------------------
# ----------------------------------------------------------------------
if __name__ == "__main__":
    try: sys.exit(CommandLine.Main())
    except KeyboardInterrupt: pass