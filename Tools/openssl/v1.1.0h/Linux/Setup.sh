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
# |  Copyright David Brownell 2018.
# |  Distributed under the Boost Software License, Version 1.0.
# |  (See accompanying file LICENSE_1_0.txt or copy at http://www.boost.org/LICENSE_1_0.txt)
# |  
# ----------------------------------------------------------------------
set -e                                      # Exit on error

setup_openssl_dir="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
pushd $setup_openssl_dir > /dev/null        # +dir

echo "Setting up openssl v1.1.0h..."

# Link to the originally compile location
[[ -d /opt/CommonEnvironment/openssl ]] || mkdir -p "/opt/CommonEnvironment/openssl"
ln -fsd $setup_openssl_dir /opt/CommonEnvironment/openssl/1.1.0h

echo "  Unpacking content..."

if [[ ! -d ./bin ]]
then 
    temp_dir=/tmp/openssl
    
    [[ ! -d $temp_dir ]] || rm -Rfd $temp_dir
    mkdir -p $temp_dir

    pushd $temp_dir > /dev/null             # +temp_dir

    tar -xzf $setup_openssl_dir/install.tgz
    mv * $setup_openssl_dir

    popd > /dev/null                        # -temp_dir
    rmdir $temp_dir
fi

echo "DONE!"
echo

popd > /dev/null                            # -dir
