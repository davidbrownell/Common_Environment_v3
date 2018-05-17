#/bin/bash
# ----------------------------------------------------------------------
# |  
# |  build_linux.sh
# |  
# |  David Brownell <db@DavidBrownell.com>
# |      2018-05-12 22:22:08
# |  
# ----------------------------------------------------------------------
# |  
# |  Copyright David Brownell 2018.
# |  Distributed under the Boost Software License, Version 1.0.
# |  (See accompanying file LICENSE_1_0.txt or copy at http://www.boost.org/LICENSE_1_0.txt)
# |  
# ----------------------------------------------------------------------
set -e                                      # Exit on error
set -x                                      # statements

# Builds python code using docker.
#
#   Docker command:
#       [Linux]     docker run -it --rm -v `pwd`/..:/local centos:6.8 bash /local/Python/build_linux.sh <2.7.14|3.6.5>
#       [Windows]   docker run -it --rm -v %cd%\..:/local  centos:6.8 bash /local/Python/build_linux.sh <2.7.14|3.6.5>

if [[ "$1" == "2.7.14" ]]
then
    VERSION=2.7.14
    VERSION_SHORT=2.7
    VERSION_SHORTER=2

    OPENSSL_VERSION=1.0.2o
elif [[ "$1" == "3.6.5" ]]
then
    VERSION=3.6.5
    VERSION_SHORT=3.6
    VERSION_SHORTER=3

    OPENSSL_VERSION=1.1.0h
else
    echo "Invalid python version; expected (2.7.14 or 3.6.5)"
    exit
fi

UpdateEnvironment()
{
    set +x
    echo "# ----------------------------------------------------------------------"
    echo "# |  "
    echo "# |  Updating Development Environment"
    echo "# |  "
    echo "# ----------------------------------------------------------------------"
    set -x

    yum update -y
    yum groupinstall -y 'Development Tools'
    yum install -y bluez-libs-devel bzip2 bzip2-devel db4 db4-devel expat-devel gdbm gdbm-devel libpcap-devel ncurses-devel python-devel readline readline-devel sqlite-devel tk-devel xz-devel zlib-devel
}

BuildOpenSSL()
{
    set +x
    echo "# ----------------------------------------------------------------------"
    echo "# |  "
    echo "# |  Building OpenSSL"
    echo "# |  "
    echo "# ----------------------------------------------------------------------"
    set -x

    name=openssl-$OPENSSL_VERSION

    curl https://www.openssl.org/source/$name.tar.gz | gunzip -c | tar xf -

    pushd $name > /dev/null                                                         # +src dir

    ./config shared --prefix=/opt/CommonEnvironment/openssl/$OPENSSL_VERSION
    make clean
    make
    make install

    pushd /opt/CommonEnvironment/openssl/$OPENSSL_VERSION > /dev/null               # +install dir
    tar czf - * > /local/openssl/v$OPENSSL_VERSION/Linux/setup.tgz
    popd > /dev/null                                                                # -install dir
    popd > /dev/null                                                                # -src dir
}

BuildPython()
{
    set +x
    echo "# ----------------------------------------------------------------------"
    echo "# |  "
    echo "# |  Building Python"
    echo "# |  "
    echo "# ----------------------------------------------------------------------"
    set -x

    curl https://www.python.org/ftp/python/$VERSION/Python-$VERSION.tgz | gunzip -c | tar xf -

    pushd Python-$VERSION > /dev/null                                               # +src dir
    
    # Update Setup.dist
    cp ./Modules/Setup.dist ./Modules/Setup.dist.bak
    sed -r "s:#SSL=/usr/local/ssl:SSL=/opt/CommonEnvironment/openssl/$OPENSSL_VERSION:" ./Modules/Setup.dist.bak |\
        sed -r "s:#_ssl _ssl.c:    _ssl _ssl.c:" |\
        sed -r "s:#\s+-DUSE_SSL -I\\$\\(SSL\\)/include -I\\$\\(SSL\\)/include/openssl:    -DUSE_SSL -I\\$\\(SSL\\)/include -I\\$\\(SSL\\)/include/openssl:" |\
        sed -r "s:#\s+-L\\$\\(SSL\\)/lib -lssl -lcrypto:    -L\\$\\(SSL\\)/lib -lssl -lcrypto:" \
        > ./Modules/Setup.dist
    
    # Update setup.py
    cp setup.py setup.py.bak
    sed -r "s:search_for_ssl_incs_in = \[:search_for_ssl_incs_in = \[ '/opt/CommonEnvironment/openssl/$OPENSSL_VERSION/include', :" setup.py.bak | \
        sed -r "s:\['/usr/local/ssl/lib',:\['/opt/CommonEnvironment/openssl/$OPENSSL_VERSION/lib', '/usr/local/ssl/lib',:" \
        > setup.py
    
    export LD_LIBRARY_PATH=/opt/CommonEnvironment/openssl/$OPENSSL_VERSION/lib
    export LDFLAGS="$LDFLAGS -Wl,-rpath,/opt/CommonEnvironment/openssl/$OPENSSL_VERSION/lib"

    ./configure --enable-ipv6 --enable-shared --enable-optimizations --with-threads --prefix=/opt/CommonEnvironment/python/$VERSION
    make clean
    make
    make altinstall
    
    pushd /opt/CommonEnvironment/python/$VERSION > /dev/null                        # +install dir

    pushd ./bin > /dev/null                                                         # +bin
    
    ln -fs python$VERSION_SHORT python
    ln -fs python$VERSION_SHORT python$VERSION_SHORTER
    
    popd > /dev/null                                                                # -bin

    export PATH=/opt/CommonEnvironment/python/$VERSION/bin:$PATH
    export LD_LIBRARY_PATH=/opt/CommonEnvironment/python/$VERSION/lib:$LD_LIBRARY_PATH

    python -m ensurepip --default-pip
    python -m pip install --upgrade pip
    
    tar czf - * > /local/Python/v$VERSION/Linux/setup.tgz

    popd > /dev/null                                                                # -install dir
    popd > /dev/null                                                                # -src dir
}

[[ -d /src ]] || mkdir "/src"
pushd /src > /dev/null
    
UpdateEnvironment
BuildOpenSSL
BuildPython

set +x
echo DONE!
