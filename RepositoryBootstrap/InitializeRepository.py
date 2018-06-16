# ----------------------------------------------------------------------
# |  
# |  InitializeRepository.py
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

sys.path.insert(0, os.getenv("DEVELOPMENT_ENVIRONMENT_FUNDAMENTAL"))
with CallOnExit(lambda: sys.path.pop(0)):
    from RepositoryBootstrap import Constants as RepositoryBootstrapConstants
            
# ----------------------------------------------------------------------
inflect                                     = inflect_mod.engine()

# ----------------------------------------------------------------------
@CommandLine.EntryPoint
@CommandLine.Constraints( output_stream=None,
                        )
def EntryPoint( output_stream=sys.stdout,
              ):
    with StreamDecorator(output_stream).DoneManager( line_prefix='',
                                                     prefix="\nResults: ",
                                                     suffix='\n',
                                                   ) as dm:
        dm.stream.write('\n')

        repo_dir = _Prompt( textwrap.dedent(
                                """\
                                Enter the destination repository directory (this directory should exist 
                                and be initialized with your preferred source control management system)
                                """), 
                            os.getcwd(),
                          )
        
        repo_dir = os.path.realpath(repo_dir)
        if not os.path.isdir(repo_dir):
            dm.stream.write("ERROR: '{}' does not exist.\n".format(repo_dir))
            dm.result = -1

            return dm.result

        dm.stream.write('\n')

        repo_name = _Prompt("Enter the friendly name of this repository: ")
        
        # Prompt for the files to copy
        dm.stream.write(textwrap.dedent(
            """\

            **********************************************************************
            The following information will be used to copy files to
            '{}'.

            The contents of the files themselves will not be modified.
            **********************************************************************

            """).format(repo_dir))

        support_git = _Prompt("Include .gitignore for Git support? ", "yes").lower() in [ "yes", "y", ]
        support_hg = _Prompt("Include .hgignore for Hg support? ", "yes").lower() in [ "yes", "y", ]
        support_windows = _Prompt("Support development on Windows? ", "yes").lower() in [ "yes", "y", ]

        if support_windows:
            support_powershell = _Prompt("Support development on Windows using PowerShell? ", "yes").lower() in [ "yes", "y", ]
        else:
            support_powershell = False

        support_linux = _Prompt("Support development on Linux? ", "yes").lower() in [ "yes", "y", ]

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

        dm.stream.write("\nPopulating {}...".format(inflect.no("file", len(filenames) + 1)))
        with dm.stream.DoneManager() as this_dm:
            for filename in filenames:
                dest_filename = os.path.join(repo_dir, filename)
            
                if os.path.exists(dest_filename):
                    continue
            
                source_filename = os.path.join(_script_dir, "Templates", filename)
                assert os.path.isfile(source_filename), source_filename
            
                shutil.copy2(source_filename, dest_filename)
            
            # Create the repo id
            dest_filename = os.path.join(repo_dir, RepositoryBootstrapConstants.REPOSITORY_ID_FILENAME)
            if not os.path.exists(dest_filename):
                with open(dest_filename, 'w') as f:
                    f.write(RepositoryBootstrapConstants.REPOSITORY_ID_CONTENT_TEMPLATE.format( name=repo_name,
                                                                                                id=str(uuid.uuid4()).replace('-', '').upper(),
                                                                                              ))

        dm.stream.write(textwrap.dedent(
            """\

            **********************************************************************
            Repository information has been created at: "{repo_dir}"

            To begin using this repository...

                1) "{setup}"
                   
                   Edit this file and add dependencies and any custom setup actions (if necessary). The template copied is
                   preconfigured to raise exceptions when these methods are first invoked; you can remove these exceptions once 
                   you have configured all setup activities.

                2) "{activate}"

                   Edit this file and add any custom activation actions (if necessary). The template copied is preconfigured
                   to raise an exception when this method is first invoked; you can remove this exception once you have 
                   configured all activation activities.

                3) [OPTIONAL] "{scm_hook}"

                   Edit this file and add any custom Committing, Pushing, or Pulled validation events. Repositories will
                   rarely modify this file; the template is not preconfigured to raise exceptions when these methods are
                   invoked.
                
                4) "{readme}"

                   Edit this file to include specific information about your new repository.

            See <Common_Environment>/Readme.rst[.md] for more information.
            **********************************************************************

            """).format( repo_dir=repo_dir,
                         setup=os.path.join(repo_dir, RepositoryBootstrapConstants.SETUP_ENVIRONMENT_CUSTOMIZATION_FILENAME),
                         activate=os.path.join(repo_dir, RepositoryBootstrapConstants.ACTIVATE_ENVIRONMENT_CUSTOMIZATION_FILENAME),
                         scm_hook=os.path.join(repo_dir, RepositoryBootstrapConstants.HOOK_ENVIRONMENT_CUSTOMIZATION_FILENAME),
                         readme=os.path.join(repo_dir, "Readme.rst"),
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