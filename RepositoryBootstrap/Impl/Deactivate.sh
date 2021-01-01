#/bin/bash
# ----------------------------------------------------------------------
# |
# |  Deactivate.sh
# |
# |  David Brownell <db@DavidBrownell.com>
# |      2020-04-08 13:20:36
# |
# ----------------------------------------------------------------------
# |
# |  Copyright David Brownell 2020-21
# |  Distributed under the Boost Software License, Version 1.0. See
# |  accompanying file LICENSE_1_0.txt or copy at
# |  http://www.boost.org/LICENSE_1_0.txt.
# |
# ----------------------------------------------------------------------
set +v                                      # Disable output

# Note that we can't exit or return from this script, as it is invoked via a short cut at the
# repo's root. Because of this, we use the ugly 'should_continue hack.
should_continue=1

this_dir="$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null 2>&1 && pwd )"
source ${this_dir}/CommonFunctions.sh

if [[ "${DEVELOPMENT_ENVIRONMENT_REPOSITORY_GENERATED}" = ="" ]]
then
    echo ""
    echo "ERROR: It does not appear that this environment has been activated."
    echo ""
    echo "       [DEVELOPMENT_ENVIRONMENT_ENVIRONMENT_NAME was not defined]"
    echo ""

    should_continue=0
fi

# Ensure that the script is being invoked via source ( as it modifies the current environment).
if [[ ${should_continue} == 1 && ${0##*/} == Deactivate.sh ]]
then
    echo ""
    echo "ERROR: This script deactivates an activated console."
    echo ""
    echo "       Because this process makes changes to environment variables, it must be run within the current context. To do this, please source (run) the script as follows:"
    echo ""
    echo "          source ./Deactivate.sh"
    echo ""
    echo "              - or -"
    echo ""
    echo "          . ./Deactivate.sh"
    echo ""
    echo ""

    should_continue=0
fi

# Generate...
if [[ ${should_continue} == 1 ]]
then
    temp_script_name=$(mktemp_func)
    [[ ! -e ${temp_script_name} ]] || rm -f "${temp_script_name}"

    python -m RepositoryBootstrap.Impl.Deactivate ${temp_script_name} "$@"
    generation_error=$?

    if [[ -e ${temp_script_name} ]]
    then
        chmod u+x ${temp_script_name}
        source ${temp_script_name}
    fi
    execution_error=$?

    if [[ ${generation_error} != 0 ]]
    then
        echo ""
        echo "ERROR: Errors were encountered and the environment has not been successfully deactivated."
        echo ""
        echo "       [${DEVELOPMENT_ENVIRONMENT_FUNDAMENTAL}/RepositoryBootstrap/Impl/Dectivate.py failed]"
        echo ""

        should_continue=0

    elif [[ ${execution_error} != 0 ]]
    then
        echo ""
        echo "ERROR: Errors were encountered and the environment has not been successfully deactivated."
        echo ""
        echo "       [${temp_script_name} failed]"
        echo ""

        should_continue=0
    fi
fi

# Cleanup
[[ ! -f ${temp_script_name} ]] || rm -f "${temp_script_name}"

if [[ ${should_continue} == 1 ]]
then
    echo "                                                                       ^v^v^v^v^v^v^v^v^v^v^v^v^v^v^v^v^v^v^v^v^v^v^v^"
    echo "                                                                       <                                             >"
    echo "                                                                       >    The environment has been deactivated.    <"
    echo "                                                                       <                                             >"
    echo "                                                                       ^v^v^v^v^v^v^v^v^v^v^v^v^v^v^v^v^v^v^v^v^v^v^v^"
    echo ""
    echo ""
fi
