# ----------------------------------------------------------------------
# |  
# |  Constants.py
# |  
# |  David Brownell <db@DavidBrownell.com>
# |      2018-05-02 13:31:31
# |  
# ----------------------------------------------------------------------
# |  
# |  Copyright David Brownell 2018.
# |  Distributed under the Boost Software License, Version 1.0.
# |  (See accompanying file LICENSE_1_0.txt or copy at http://www.boost.org/LICENSE_1_0.txt)
# |  
# ----------------------------------------------------------------------
"""Constants used in the bootstrap process"""

import os
import sys
import textwrap

# ----------------------------------------------------------------------
_script_fullpath = os.path.abspath(__file__) if "python" in sys.executable.lower() else sys.executable
_script_dir, _script_name = os.path.split(_script_fullpath)
# ----------------------------------------------------------------------

SETUP_ENVIRONMENT_NAME                                  = "Setup"
SETUP_ENVIRONMENT_CUSTOMIZATION_FILENAME                = "{}_custom.py".format(SETUP_ENVIRONMENT_NAME)

ACTIVATE_ENVIRONMENT_NAME                               = "Activate"
ACTIVATE_ENVIRONMENT_CUSTOMIZATION_FILENAME             = "{}_custom.py".format(ACTIVATE_ENVIRONMENT_NAME)

HOOK_ENVIRONMENT_CUSTOMIZATION_FILENAME                 = "ScmHook_custom.py"

GENERATED_DIRECTORY_NAME                                = "Generated"
GENERATED_BOOTSTRAP_JSON_FILENAME                       = "EnvironmentBootstrap.json"
GENERATED_BOOTSTRAP_DATA_FILENAME                       = "EnvironmentBootstrap.data"
GENERATED_ACTIVATION_FILENAME                           = "EnvironmentActivation.json"
GENERATED_ACTIVATION_ORIGINAL_ENVIRONMENT_FILENAME      = "EnvironmentActivation.OriginalEnvironment.json"

# Place a file or direectory with this name in the file system to prevent
# its siblings and their descendants from being scanned as potential repository 
# locations. This is espectially useful during Continuous Integration processes,
# where code associated with CI working directories should not be considered
# as potential dependencies for the CI processes itself.
IGNORE_DIRECTORY_AS_BOOTSTRAP_DEPENDENCY_SENTINEL_FILENAME = "IgnoreAsBootstrapDependency"

LIBRARIES_SUBDIR                                        = "Libraries"
SCRIPTS_SUBDIR                                          = "Scripts"
TOOLS_SUBDIR                                            = "Tools"

AGNOSTIC_OS_NAME                                        = "Agnostic"

# ----------------------------------------------------------------------
# |  Custom Setup Methods
SETUP_ENVIRONMENT_DEPENDENCIES_METHOD_NAME              = "GetDependencies"
SETUP_ENVIRONMENT_ACTIONS_METHOD_NAME                   = "GetCustomActions"

SETUP_ENVIRONMENT_COMMIT_HOOK_EVENT_HANDLER             = "Commit"
SETUP_ENVIRONMENT_PUSH_HOOK_EVENT_HANDLER               = "Push"
SETUP_ENVIRONMENT_PUSHED_HOOK_EVENT_HANDLER             = "Pushed"

# ----------------------------------------------------------------------
# |  Custom Activate Methods
ACTIVATE_ENVIRONMENT_ACTIONS_METHOD_NAME                                    = "GetCustomActions"
ACTIVATE_ENVIRONMENT_CUSTOM_SCRIPT_EXTRACTOR_METHOD_NAME                    = "GetCustomScriptExtractors"

SCRIPT_LIST_NAME                                                            = "DevEnvScripts"

# ----------------------------------------------------------------------
# |  Custom Hook Methods
HOOK_ENVIRONMENT_COMMIT_METHOD_NAME                     = "OnCommitting"
HOOK_ENVIRONMENT_PUSH_METHOD_NAME                       = "OnPushing"
HOOK_ENVIRONMENT_PULL_METHOD_NAME                       = "OnPulled"

# ----------------------------------------------------------------------
REPOSITORY_ID_FILENAME                                  = "__RepositoryId__"

REPOSITORY_ID_CONTENT_TEMPLATE                          = textwrap.dedent(
    """\
    This file is used to uniquely identify this repository for the purposes of dependency management.
    Other repositories that depend on this one will search for this file upon initial setup and 
    generate information that can be used when activating development environments.
    
    **** PLEASE DO NOT MODIFY, REMOVE, OR RENAME THIS FILE, AS DOING SO WILL LIKELY BREAK OTHER REPOSITORIES! ****
    
    Friendly Name:      {name}
    Id:                 {id}
    """)

# ----------------------------------------------------------------------
DE_FUNDAMENTAL_ROOT_NAME                                = "DEVELOPMENT_ENVIRONMENT_FUNDAMENTAL"

DE_REPO_ROOT_NAME                                       = "DEVELOPMENT_ENVIRONMENT_REPOSITORY"
DE_REPO_CONFIGURATION_NAME                              = "DEVELOPMENT_ENVIRONMENT_REPOSITORY_CONFIGURATION"
DE_REPO_GENERATED_NAME                                  = "DEVELOPMENT_ENVIRONMENT_REPOSITORY_GENERATED"

DE_REPO_ACTIVATED_FLAG                                  = "DEVELOPMENT_ENVIRONMENT_REPOSITORY_ACTIVATED_FLAG"

# ----------------------------------------------------------------------
TEMPORARY_FILE_EXTENSION                                = ".SourceRepositoryTools"
