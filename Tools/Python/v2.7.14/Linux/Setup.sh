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

setup_python_dir="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
pushd ${setup_python_dir} > /dev/null       # +dir

echo "Setting up Python v2.7.14..."

if [[ ! -d ./bin ]]
then
    echo "  Unpacking content..."

    temp_dir=/tmp/python

    [[ ! -d ${temp_dir} ]] || rm -Rfd ${temp_dir}
    mkdir -p ${temp_dir}

    pushd ${temp_dir} > /dev/null           # +temp_dir

    tar -xzf ${setup_python_dir}/install.tgz
    mv * ${setup_python_dir}

    popd > /dev/null                        # -temp_dir
    rmdir ${temp_dir}
fi

echo "  Finalizing..."

# Convert sep in '-', then remove the initial '-'
conf_file=$(echo $(pwd)/bin/python2.7 | tr / - | cut -c 2-).conf

if [[ ! -e /etc/ld.so.conf.d/${conf_file} ]]
then
    
cat > /etc/ld.so.conf.d/${conf_file} << END
`pwd`/lib
END
    set +e
    ldconfig
    set -e
fi

# Link to the originally compiled location
if [[ ! -e /opt/CommonEnvironment/python/2.7.14 ]]
then
    [[ -d /opt/CommonEnvironment/python ]] || mkdir -p "/opt/CommonEnvironment/python"
    ln -fsd ${setup_python_dir} /opt/CommonEnvironment/python/2.7.14
fi

echo "DONE!"
echo ""

popd > /dev/null                            # -dir
