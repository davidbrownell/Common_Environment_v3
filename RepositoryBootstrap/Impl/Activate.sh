#!/bin/bash
# ----------------------------------------------------------------------
# |
# |  Activate.sh
# |
# |  David Brownell <db@DavidBrownell.com>
# |      2018-05-11 16:53:08
# |
# ----------------------------------------------------------------------
# |
# |  Copyright David Brownell 2018-19.
# |  Distributed under the Boost Software License, Version 1.0.
# |  (See accompanying file LICENSE_1_0.txt or copy at http://www.boost.org/LICENSE_1_0.txt)
# |
# ----------------------------------------------------------------------
set +v                                      # Disable output

# Note that we can't exit or return from this script, as it is invoked via a short cut at the
# repo's root. Because of this, we use the ugly 'should_continue hack.
should_continue=1
previous_fundamental=${DEVELOPMENT_ENVIRONMENT_FUNDAMENTAL}

# Read data created during setup
if [[ ${should_continue} == 1 && ! -e `pwd`/Generated/Linux/${DEVELOPMENT_ENVIRONMENT_ENVIRONMENT_NAME}/EnvironmentBootstrap.data ]]
then
    echo ""
    echo "ERROR: It appears that Setup.sh has not been run for this repository. Please run Setup.sh and run this script again."
    echo ""
    echo "       [`pwd`/Generated/Linux/${DEVELOPMENT_ENVIRONMENT_ENVIRONMENT_NAME}/EnvironmentBootstrap.data was not found]"
    echo ""

    should_continue=0
fi

# Parse the bootstrap info, extracting the relevant info
if [[ ${should_continue} == 1 ]]
then
    while read line;
    do
        if [[ ${line} == fundamental_repo* ]]
        then
            export DEVELOPMENT_ENVIRONMENT_FUNDAMENTAL=`readlink -f ${line#fundamental_repo=}`
        elif [[ ${line} == is_mixin_repo* ]]
        then
            is_mixin_repo=${line#is_mixin_repo=}
        elif [[ ${line} == is_configurable* ]]
        then
            is_configurable=${line#is_configurable=}
        fi

    done < "`pwd`/Generated/Linux/${DEVELOPMENT_ENVIRONMENT_ENVIRONMENT_NAME}/EnvironmentBootstrap.data"
fi

# Find the python binary
python_dir=${DEVELOPMENT_ENVIRONMENT_FUNDAMENTAL}/Tools/Python
pushd ${python_dir} > /dev/null                                             # +python_dir

for d in $(find v* -maxdepth 0 -type d);
do
    if [[ -e ${python_dir}/${d}/Linux/${DEVELOPMENT_ENVIRONMENT_ENVIRONMENT_NAME}/bin/python ]]
    then
        python_binary=${python_dir}/${d}/Linux/${DEVELOPMENT_ENVIRONMENT_ENVIRONMENT_NAME}/bin/python
    fi
done

popd > /dev/null                                                            # -python_dir

export PYTHONPATH=${DEVELOPMENT_ENVIRONMENT_FUNDAMENTAL}

# ----------------------------------------------------------------------
# |  List configurations if requested
if [[ "$1" == "ListConfigurations" ]]
then
    shift 1

    ${python_binary} -m RepositoryBootstrap.Impl.Activate ListConfigurations "`pwd`" "$@"
    should_continue=0
fi

# Ensure that the script is being invoked via source ( as it modifies the current environment).
if [[ ${should_continue} == 1 && ${0##*/} == Activate.sh ]]
then
    echo ""
    echo "ERROR: This script activates a console for development according to information specific to the repository."
    echo ""
    echo "       Because this process makes changes to environment variables, it must be run within the current context. To do this, please source (run) the script as follows:"
    echo ""
    echo "          source ./Activate.sh"
    echo ""
    echo "              - or -"
    echo ""
    echo "          . ./Activate.sh"
    echo ""
    echo ""

    should_continue=0
fi

# If here, we are in a verified activation scenario. Set the previous value to this value, knowing that that is the value
# that will be committed.
previous_fundamental=${DEVELOPMENT_ENVIRONMENT_FUNDAMENTAL}

# ----------------------------------------------------------------------
# |  Only allow one activated environment at a time (unless we are activating a mixin repo)
if [[ ${should_continue} == 1 && "${DEVELOPMENT_ENVIRONMENT_REPOSITORY}" != "" && "${DEVELOPMENT_ENVIRONMENT_REPOSITORY}" != "`pwd`" ]]
then
    echo ""
    echo "ERROR: Only one repository can be activated within an environment at a time, and it appears as if one is already active. Please open a new console and run this script again."
    echo ""
    echo "       [DEVELOPMENT_ENVIRONMENT_REPOSITORY is already defined as \"${DEVELOPMENT_ENVIRONMENT_REPOSITORY}\"]"
    echo ""

    should_continue=0
fi

# ----------------------------------------------------------------------
# |  A mixin repository can't be activated in isolation
if [[ ${should_continue} == 1 && ${is_mixin_repo} == "1" && "${DEVELOPMENT_ENVIRONMENT_REPOSITORY_ACTIVATED_FLAG}" != "1" ]]
then
    echo ""
    echo "ERROR: A mixin repository cannot be activated in isolation. Activate another repository before activating this one."
    echo ""
    echo ""

    should_continue=0
fi

# ----------------------------------------------------------------------
# |  Prepare the args
if [[ ${should_continue} == 1 ]]
then
    if [[ ${is_configurable} == "1" ]]
    then
        if [[ "$1" == "" ]]
        then
            echo ""
            echo "ERROR: This repository is configurable, which means that it can be activated in a variety of different ways. Please run this script again with a configuration name provided on the command line."
            echo ""
            echo "       Available configurations are:"
            echo ""
            ${python_binary} -m RepositoryBootstrap.Impl.Activate ListConfigurations `pwd` command_line
            echo ""
            echo ""

            should_continue=0

        fi

        if [[ "${DEVELOPMENT_ENVIRONMENT_REPOSITORY_CONFIGURATION}" != "" && "${DEVELOPMENT_ENVIRONMENT_REPOSITORY_CONFIGURATION}" != "$1" ]]
        then
            echo ""
            echo "ERROR: The environment was previously activated with this repository but using a different configuration. Please open a new console window and activate this repository with the new configuration."
            echo ""
            echo "       ["${DEVELOPMENT_ENVIRONMENT_REPOSITORY_CONFIGURATION}" != "$1"]"
            echo ""

            should_continue=0
        fi

        configuration=$1
        shift 1
    else
        configuration=None
    fi
fi

# Generate...
if [[ ${should_continue} == 1 ]]
then
    temp_script_name=`mktemp`
    [[ ! -e ${temp_script_name} ]] || rm "${temp_script_name}"

    ${python_binary} -m RepositoryBootstrap.Impl.Activate Activate ${temp_script_name} "`pwd`" ${configuration} "$@"
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
        echo "ERROR: Errors were encountered and the environment has not been successfully activated for development."
        echo ""
        echo "       [${DEVELOPMENT_ENVIRONMENT_FUNDAMENTAL}/RepositoryBootstrap/Impl/Activate.py failed]"
        echo ""

        should_continue=0

    elif [[ ${execution_error} != 0 ]]
    then
        echo ""
        echo "ERROR: Errors were encountered and the environment has not been successfully activated for development."
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
    echo "                                                ^v^v^v^v^v^v^v^v^v^v^v^v^v^v^v^v^v^v^v^v^v^v^v^v^v^v^v^v^v^v^v^v^v^v^v^v^v^v^v^v^v^v^v^v^v^v^"
    echo "                                                <                                                                                           >"
    echo "                                                >   The environment has been activated for this repository and is ready for development.    <"
    echo "                                                <                                                                                           >"
    echo "                                                ^v^v^v^v^v^v^v^v^v^v^v^v^v^v^v^v^v^v^v^v^v^v^v^v^v^v^v^v^v^v^v^v^v^v^v^v^v^v^v^v^v^v^v^v^v^v^"
    echo ""
    echo ""
fi

unset PYTHONPATH

if [[ "${previous_fundamental}" != "" ]]; then
    export DEVELOPMENT_ENVIRONMENT_FUNDAMENTAL=${previous_fundamental}
else
    unset DEVELOPMENT_ENVIRONMENT_FUNDAMENTAL
fi
