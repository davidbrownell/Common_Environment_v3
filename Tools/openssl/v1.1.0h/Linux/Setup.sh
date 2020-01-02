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
# |  Copyright David Brownell 2018-20.
# |  Distributed under the Boost Software License, Version 1.0.
# |  (See accompanying file LICENSE_1_0.txt or copy at http://www.boost.org/LICENSE_1_0.txt)
# |  
# ----------------------------------------------------------------------
set -e                                      # Exit on error

setup_openssl_dir="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
pushd ${setup_openssl_dir} > /dev/null      # +dir

echo "Setting up openssl v1.1.0h..."

if [[ ! -d "$1" ]]
then 
    echo "  Unpacking content..."

    temp_dir=/tmp/openssl
    
    [[ ! -d ${temp_dir} ]] || rm -Rfd ${temp_dir}
    mkdir -p ${temp_dir}

    pushd ${temp_dir} > /dev/null           # +temp_dir

    tar -xzf ${setup_openssl_dir}/install.tgz
    mkdir -p "${setup_openssl_dir}/$1"
    mv * "${setup_openssl_dir}/$1"

    popd > /dev/null                        # -temp_dir
    rmdir ${temp_dir}
fi

# Link to the originally compile location
if [[ ! -e /opt/CommonEnvironment/openssl/1.1.0h ]]
then
    [[ -d /opt/CommonEnvironment/openssl ]] || mkdir -p "/opt/CommonEnvironment/openssl"
    ln -fsd "${setup_openssl_dir}/$1" /opt/CommonEnvironment/openssl/1.1.0h
fi

echo "DONE!"
echo

popd > /dev/null                            # -dir
