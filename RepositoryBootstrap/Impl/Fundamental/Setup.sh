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

this_dir="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

source ${this_dir}/../../../Tools/openssl/v1.0.2o/Linux/Setup.sh
${this_dir}/../../../Tools/Python/v2.7.14/Linux/Setup.sh

source ${this_dir}/../../../Tools/openssl/v1.1.0h/Linux/Setup.sh
${this_dir}/../../../Tools/Python/v3.6.5/Linux/Setup.sh

set +e
ldconfig
set -e

echo "Installing python dependencies for v2.7.14..."
/opt/CommonEnvironment/python/2.7.14/bin/python -m pip install --quiet --no-warn-script-location --no-cache-dir -r ${this_dir}/python_requirements.txt -r ${this_dir}/python_linux_requirements.txt 
echo "DONE!"
echo

echo "Installing python dependencies for v3.6.5..."
/opt/CommonEnvironment/python/3.6.5/bin/python -m pip install --quiet --no-warn-script-location --no-cache-dir -r ${this_dir}/python_requirements.txt -r ${this_dir}/python_linux_requirements.txt 
echo "DONE!"
echo

# Invoke fundamental setup activities
/opt/CommonEnvironment/python/3.6.5/bin/python ${this_dir}/Setup.py "$@"

echo "----------------------------------------------------------------------"
echo
