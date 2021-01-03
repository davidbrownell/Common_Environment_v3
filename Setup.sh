#!/bin/bash
# ----------------------------------------------------------------------
# |
# |  Setup.sh
# |
# |  David Brownell <db@DavidBrownell.com>
# |      2018-05-09 10:37:21
# |
# ----------------------------------------------------------------------
# |
# |  Copyright David Brownell 2018-21.
# |  Distributed under the Boost Software License, Version 1.0.
# |  (See accompanying file LICENSE_1_0.txt or copy at http://www.boost.org/LICENSE_1_0.txt)
# |
# ----------------------------------------------------------------------
set -e                                      # Exit on error
set +v                                      # Disable output

# ----------------------------------------------------------------------
# |
# |  Run as:
# |     sudo ./Setup.sh [/debug] [/verbose] [/name=<name>] [/configuration=<config_name>]*
# |
# ----------------------------------------------------------------------
# Note that sudo is necessary because the process updates ldconfig

# root is required the first time that this script is invoked. Root is not required
# if the environment has already been setup.
if [[ $EUID -ne 0 ]] && [[ -z "${DEVELOPMENT_ENVIRONMENT_FUNDAMENTAL}" ]]; then
    echo
    echo "ERROR: Please run this script as root (via sudo)."
    echo

    exit -1
fi

# Begin bootstrap customization
pushd "$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null 2>&1 && pwd )" > /dev/null

source ./RepositoryBootstrap/Impl/CommonFunctions.sh
bootstrap_func

prev_development_environment_fundamental=${DEVELOPMENT_ENVIRONMENT_FUNDAMENTAL}
export DEVELOPMENT_ENVIRONMENT_FUNDAMENTAL=$(dirname "$(readlink_func "${BASH_SOURCE[0]}")")

# Only run the fundamental setup if we are in a standard setup scenario
initial_char="$(echo $1 | head -c 1)"
if [[ "${initial_char}" == "" || "${initial_char}" == "/" || "${initial_char}" == "-" ]]
then
    # Get the tools unique name

    # This should match the value in RepositoryBootstrap/Constants.py:DEFAULT_ENVIRONMENT_NAME
    tools_unique_name=DefaultEnv

    ARGS=()
    for var in "$@"; do
        if [[ $var == /name=* ]] || [[ $var == -name=* ]]; then
            tools_unique_name=`echo $var | cut -d'=' -f 2`
        else
            ARGS+=("$var")
        fi
    done

    # This should match the value in RepositoryBootstrap/Constants.py:DE_ENVIRONMENT_NAME
    export DEVELOPMENT_ENVIRONMENT_ENVIRONMENT_NAME=${tools_unique_name}
    set -- ${ARGS[@]}

    source ${DEVELOPMENT_ENVIRONMENT_FUNDAMENTAL}/RepositoryBootstrap/Impl/Fundamental/Setup.sh "$@"
fi
# End bootstrap customization

if [[ "${DEVELOPMENT_ENVIRONMENT_FUNDAMENTAL}" = "" ]]
then
    echo
    echo "ERROR: Please run Activate within a repository before running this script. It may be necessary to Setup and Activate the Common_Environment repository before setting up this one."
    echo

    exit -1
fi

source ${DEVELOPMENT_ENVIRONMENT_FUNDAMENTAL}/RepositoryBootstrap/Impl/Setup.sh "$@"

# Bootstrap customization
if [[ "${prev_development_environment_fundamental}" != "" ]]; then
    export DEVELOPMENT_ENVIRONMENT_FUNDAMENTAL=${prev_development_environment_fundamental}
else
    unset DEVELOPMENT_ENVIRONMENT_FUNDAMENTAL
fi

popd > /dev/null
