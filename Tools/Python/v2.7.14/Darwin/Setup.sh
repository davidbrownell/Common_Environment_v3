#/bin/bash
# ----------------------------------------------------------------------
# |  
# |  setup.sh
# |  
# |  David Brownell <db@DavidBrownell.com>
# |      2018-05-10 18:51:47
# |  
# ----------------------------------------------------------------------
# |  
# |  Copyright David Brownell 2018-19.
# |  Distributed under the Boost Software License, Version 1.0.
# |  (See accompanying file LICENSE_1_0.txt or copy at http://www.boost.org/LICENSE_1_0.txt)
# |  
# ----------------------------------------------------------------------
set -e                                      # Exit on error

source ${DEVELOPMENT_ENVIRONMENT_FUNDAMENTAL}/RepositoryBootstrap/Impl/CommonFunctions.sh

setup_python_dir="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
pushd ${setup_python_dir} > /dev/null       # +dir

if [[ ! $(pkgutil --pkgs=org.python.Python.PythonApplications-2.7) ]]
then
    echo "Installing python 2.7.14"
    echo
    installer -pkg ${setup_python_dir}/python-2.7.14-macosx10.6.pkg -target /
    echo "DONE!"
    echo
    echo
fi

if [[ ! -e  "/Library/Frameworks/Python.framework/Versions/2.7/bin/python" ]]
then
    ln_file_func "/Library/Frameworks/Python.framework/Versions/2.7/bin/python2" "/Library/Frameworks/Python.framework/Versions/2.7/bin/python"
fi

setup_python_binary=/Library/Frameworks/Python.framework/Versions/2.7/bin/python2

popd > /dev/null                            # -dir
