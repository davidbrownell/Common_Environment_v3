#!/bin/bash
# ----------------------------------------------------------------------
# |
# |  Setup.sh
# |
# |  David Brownell <db@DavidBrownell.com>
# |      2018-05-09 10:57:47
# |
# ----------------------------------------------------------------------
# |
# |  Copyright David Brownell 2018-19.
# |  Distributed under the Boost Software License, Version 1.0.
# |  (See accompanying file LICENSE_1_0.txt or copy at http://www.boost.org/LICENSE_1_0.txt)
# |
# ----------------------------------------------------------------------
set -e                                      # Exit on error

echo "----------------------------------------------------------------------"
echo "|                                                                    |"
echo "|             Performing fundamental repository setup                |"
echo "|                                                                    |"
echo "----------------------------------------------------------------------"

source ${DEVELOPMENT_ENVIRONMENT_FUNDAMENTAL}/RepositoryBootstrap/Impl/CommonFunctions.sh

this_dir="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

if [[ ${is_darwin} ]]
then
    os_name=Darwin
else
    os_name=Linux
fi

# ----------------------------------------------------------------------
# |  Python v2.7.14
echo ""
echo "------------------------  Python 2.7.14  -----------------------------"

source ${this_dir}/../../../Tools/Python/v2.7.14/${os_name}/Setup.sh "${DEVELOPMENT_ENVIRONMENT_ENVIRONMENT_NAME}"

echo "Installing python dependencies for v2.7.14..."

if [[ ${is_darwin} ]]
then
    # The old version of pip that ships with this version of python needs to be
    # updated, as it doesn't have support for TLS 1.2.
    ${setup_python_binary} ${this_dir}/../../../Tools/Python/v2.7.14/${os_name}/get-pip.py
fi

${setup_python_binary} -m pip install --quiet --no-cache-dir -r ${this_dir}/python_requirements.txt -r ${this_dir}/python_linux_requirements.txt
echo "DONE!"

# ----------------------------------------------------------------------
# |  Python v3.6.5
echo ""
echo "------------------------  Python 3.6.5  ------------------------------"

source ${this_dir}/../../../Tools/Python/v3.6.5/${os_name}/Setup.sh "${DEVELOPMENT_ENVIRONMENT_ENVIRONMENT_NAME}"

echo "Installing python dependencies for v3.6.5..."
${setup_python_binary} -m pip install --quiet --no-cache-dir -r ${this_dir}/python_requirements.txt -r ${this_dir}/python_linux_requirements.txt
echo "DONE!"

echo
echo

echo "----------------------------------------------------------------------"

# Invoke fundamental setup activities
${setup_python_binary} ${this_dir}/Setup.py "$@"

echo "----------------------------------------------------------------------"
echo "----------------------------------------------------------------------"
echo "----------------------------------------------------------------------"
