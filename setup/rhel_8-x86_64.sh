# Run the following commands
#
#   docker run -it -v $PWD:/usr/local/src/gridlabd redhat/ubi8 bash
#   cd /usr/local/src/gridlabd
#   ./setup.sh
#
#set -x
PYTHONVER=3.10.18
PYTHONBIN=python${PYTHONVER%.*}
LOGFILE=$PWD/setup.log

function log ()
{
    if [ $# -eq 0 ]; then
        cat >> $LOGFILE
    else
        echo "$(date): $*"
    fi
}

function notify ()
{
    echo "$(date): $*" | tee -a $LOGFILE > /dev/stdout
}

function error ()
{
    RC=$1
    shift 1
    echo "ERROR: $*" | tee -a $LOGFILE > /dev/stderr
    echo "       See $LOGFILE for details" > /dev/stderr
    exit $RC
}

function warning ()
{
    echo "WARNING: $*" > /dev/stderr
}

rm -rf $LOGFILE
log "Running $0 $*"

#
# Check RedHat registration
#
if ( yum update 1>>$LOGFILE 2>&1 ); then
    notify "RedHat registration ok"
else
    notify "Attempting to register this RedHat system"
    if [ ! -z "$REDHAT_USERNAME" -a ! -z "$REDHAT_PASSWORD" ]; then
        ( subscription-manager register --username $REDHAT_USERNAME --password $REDHAT_PASSWORD 1>>$LOGFILE 2>&1 ) || error 1 "non-tty subscription-manager register failed"
    elif [ -t 0 ] ; then
        ( subscription-manager register ) || error 1 "tty subscription-manager register failed"
    else
        error 1 "you need to register this system (see https://www.redhat.com/wapps/ugc/register.html)"
    fi
fi    

#
# Check C/C++ compiler
#
if ( c++ --version 1>>$LOGFILE 2>&1 ); then
    notify "C/++ compilers ok"
else
    notify "Installing gcc-c++"
    yum install gcc gcc-c++ -y 1>>$LOGFILE 2>&1 || error 1 "gcc-c++ install failed"
fi

#
# Check make
#
if ( make --version 1>>$LOGFILE 2>&1 ); then
    notify "Build tool make ok"
else
    notify "Installing make"
    yum install make -y 1>>$LOGFILE 2>&1 || error 1 "make install failed"
fi

#
# Install developer tools
#
notify "Updating developer tools"
yum groupinstall 'Development Tools' -y 1>>$LOGFILE 2>&1
yum install git perl -y 1>>$LOGFILE 2>&1

#
# Install libraries
#
notify "Updating developer libraries"
yum install zlib-devel -y 1>>$LOGFILE 2>&1 || error 1 "developer libraries install failed"

#
# Check Python version
#
cd /usr/local/src
if ( $PYTHONBIN --version 1>>$LOGFILE 2>&1 ); then
    notify "Python $PYTHONVER ok"
else
    notify "Python $PYTHONVER is required"
    if [ ! -d /usr/local/src/Python-$PYTHONVER ]; then
        notify "Downloading Python $PYTHONVER source code"
        (curl -s https://www.python.org/ftp/python/$PYTHONVER/Python-$PYTHONVER.tgz | tar xz) || error 1 "$PYTHONVER download failed"
    fi
    cd Python-$PYTHONVER
    if [ ! -f Makefile ]; then
        notify "Configuring Python $PYTHONVER build"
        (./configure --with-system-ffi --with-computed-gotos --enable-loadable-sqlite-extensions --enable-optimizations --enable-shared 1>>$LOGFILE 2>&1 ) || error 1 "$PYTHONVER configure failed"
    fi
    if [ ! -x python -o ! -x python-config ]; then
        notify "Building Python $PYTHONVER system"
        (make -j $(nproc) 1>>$LOGFILE 2>&1) || error 1 "$PYTHONVER make failed"
    fi
    if [ ! -x /usr/local/bin/$PYTHONBIN ]; then
        notify "Installing Python $PYTHONVER"
        (make altinstall 1>>$LOGFILE 2>&1) || error 1 "$PYTHONVER make altinstall failed"
    fi
    cd /usr/local/bin
    notify "Updating python links"
    test -x python3 || ln -s $PYTHONBIN python3
    test -x python3-config || ln -s $PYTHONBIN-config python3-config
    test -x pip3 || ln -s pip${PYTHONVER%.*} pip3
    test -x pydoc3 || ln -s pydoc${PYTHONVER%.*} pydoc3
    test -x pip || ln -s pip3 pip
    test -x python || ln -s python3 python
    test -x python-config || ln -s python3-config python-config
    test -x pydoc || ln -sf pydoc3 pydoc
    notify "Python $PYTHONVER installed ok"
fi

#
# Check library path
#
if [ ! -d /etc/ld.so.conf.d ]; then
    mkdir -p /etc/ld.so.conf.d
fi
if [ ! -f /etc/ld.so.conf.d/local.conf ]; then
    notify "Updating system library paths"
    echo /usr/local/lib > /etc/ld.so.conf.d/local.conf
    ldconfig 1>>$LOGFILE 2>&1 || error 1 "ldconfig failed"
fi

#
# Check active versions of main python executables
#
function checkver ()
{
    test "$($1 --version)" == "$($2 --version)" || warning "$1 is not linked to the correct version of $2"
}
cd /usr/local/bin
checkver python3 python3.10
checkver python python3
checkver pip3 pip3.10
checkver pip pip3

#
# Install m4
#
M4VER=1.4.20
if [ "$(m4 --version 2>/dev/null | sed -n '1p' | cut -f4 -d' ')" != "$M4VER" ]; then
    notify "Upgrading m4 to $M4VER"
    cd /usr/local/src
    curl -s https://ftp.gnu.org/gnu/m4/m4-$M4VER.tar.gz | tar xz || error 1 "unable to download m4-$M4VER"
    cd m4-$M4VER
    ./configure 1>>$LOGFILE 2>&1 || error 1 "unable to configure m4-$M4VER"
    make install 1>>$LOGFILE 2>&1 || error 1 "unable to make install m4-$M4VER"
    notify "m4 upgraded to $M4VER"
else
    notify "m4-$M4VER ok"
fi


#
# Install autoconf
#
AUTOCONFVER=2.72
if [ "$(autoconf --version 2>/dev/null | sed -n '1p' | cut -f4 -d' ')" != "$AUTOCONFVER" ]; then
    notify "Upgrading autoconf to $AUTOCONFVER"
    cd /usr/local/src
    curl -s https://ftp.gnu.org/gnu/autoconf/autoconf-$AUTOCONFVER.tar.gz | tar xz || error 1 "unable to download autoconf-$AUTOCONFVER source"
    cd autoconf-$AUTOCONFVER
    ./configure  1>>$LOGFILE 2>&1 || error 1 "unable to configure autoconf-$AUTOCONFVER"
    make install 1>>$LOGFILE 2>&1 || error 1 "unable to make install autoconf-$AUTOCONFVER"
    notify "autoconf upgraded to $AUTOCONFVER"
else
    notify "autoconf-$AUTOCONFVER ok"
fi    

#
# Install automake
#
AUTOMAKEVER=1.18
if [ "$(automake --version 2>/dev/null | sed -n '1p' | cut -f4 -d' ')" != "$AUTOMAKEVER" ]; then
    notify "Upgrading automake to $AUTOMAKEVER"
    cd /usr/local/src
    curl -s https://ftp.gnu.org/gnu/automake/automake-$AUTOMAKEVER.tar.gz | tar xz || error 1 "unable to download automake-$AUTOMAKEVER source"
    cd automake-$AUTOMAKEVER
    ./configure  1>>$LOGFILE 2>&1 || error 1 "unable to configure automake-$AUTOMAKEVER"
    make install 1>>$LOGFILE 2>&1 || error 1 "unable to make install automake-$AUTOMAKEVER"
    notify "automake upgraded to $AUTOMAKEVER"
else
    notify "automake-$AUTOMAKEVER ok"
fi    

#
# Install libtool
#
LIBTOOLVER=2.5.4
if [ "$(libtool --version 2>/dev/null | sed -n '1p' | cut -f4 -d' ')" != "$LIBTOOLVER" ]; then
    notify "Upgrading libtool to $LIBTOOLVER"
    cd /usr/local/src
    curl -s https://ftp.gnu.org/gnu/libtool/libtool-$LIBTOOLVER.tar.gz | tar xz || error 1 "unable to download libtool-$LIBTOOLVER source"
    cd libtool-$LIBTOOLVER
    ./configure  1>>$LOGFILE 2>&1 || error 1 "unable to configure libtool-$LIBTOOLVER"
    make install 1>>$LOGFILE 2>&1 || error 1 "unable to make install libtool-$LIBTOOLVER"
    notify "libtool upgraded to $LIBTOOLVER"
else
    notify "libtool-$LIBTOOLVER ok"
fi    

#
# Set up gridlabd's venv
#
if [ ! -d $HOME/.gridlabd ]; then
    notify "Creating $HOME/.gridlabd venv for $PYTHONBIN"
    $PYTHONBIN -m venv $HOME/.gridlabd
fi

#
# Done
#
notify "System ready to build gridlabd. Run './build.sh --system --parallel' next."

exit 0
