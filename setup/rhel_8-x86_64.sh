# Run the following commands
#
#   docker run -it redhat/ubi8 bash
#   git clone https://github.com/arras-energy/gridlabd
#   gridlabd/setup.sh
#

# set -x # enable command echo

# required versions
PYTHONVER=3.10.18 
M4VER=1.4.20
AUTOCONFVER=2.72
AUTOMAKEVER=1.18
LIBTOOLVER=2.5.4
OPENSSLVER=1.1.1w
MDBTOOLSVER=1.0.1

#
# Setup variables
#
LOGFILE=$PWD/gridlabd-setup.log
cd $(dirname $0)
GRIDLABDIR=$(dirname $PWD)
PYTHONBIN=python${PYTHONVER%.*}

#
# Setup functions
#
function log ()
{
    if [ $# -eq 0 ]; then
        cat >> $LOGFILE
    else
        echo "$(date): $*" >>$LOGFILE
    fi
}

function notify ()
{
    echo "$(date): $*" | tee -a $LOGFILE > /dev/stderr
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
    echo "WARNING: $*" | tee -a $LOGFILE > /dev/stderr
}

function run ()
{
    echo "" 1>>$LOGFILE 2>&1
    echo "RUN [$PWD]: $1" 1>>$LOGFILE 2>&1
    $1 1>>$LOGFILE 2>&1
    test $? -ne 0 -a ! -z "$2" && error 1 $2
}

rm -rf $LOGFILE
notify "Running $PWD/$(basename $0) $*"

#
# Update yum
#
notify "Updating yum"
run "yum update -y" "unable to update yum"

#
# Check C/C++ compiler
#
if ( c++ --version 1>/dev/null 2>&1 ); then
    notify "C/++ compilers ok"
else
    notify "Installing gcc-c++"
    run "yum install -y gcc gcc-c++" "gcc-c++ install failed"
fi

#
# Check make
#
if ( make --version 1>/dev/null 2>&1 ); then
    notify "Build tool make ok"
else
    notify "Installing make"
    run "yum install -y make" "make install failed"
fi

#
# Install developer tools
#
notify "Updating developer tools"
run "yum groupinstall -y 'Development Tools'" 
run "yum install -y git wget perl subversion xz cmake diffutils" "developer tools install failed"
run "dnf install -y procps" "procps install failed"

#
# Install libraries
#
notify "Updating developer libraries"
run "yum install -y openssl-devel openssl-libs ncurses-devel libcurl-devel" "developer libraries install failed"
run "dnf install -y https://dl.fedoraproject.org/pub/epel/epel-release-latest-8.noarch.rpm" "unable to install extra packages"
run "yum install -y bzip2-devel libffi-devel zlib-devel sqlite-devel gdbm-devel" "developer libraries install failed"
run "dnf install -y https://pkgs.sysadmins.ws/el8/base/x86_64/mdbtools-libs-0.9.3-3.el8.x86_64.rpm" "mdbtools install failed"
# export CFLAGS="$CFLAGS -I/usr/include/openssl"

#
# Check Python version
#
if [ ! $($PYTHONBIN --version 2>/dev/null) != "Python $PYTHONVER" ]; then
    notify "Python $PYTHONVER is required"
    cd /usr/local/src
    if [ ! -d Python-$PYTHONVER ]; then
        notify "Downloading Python $PYTHONVER source code"
        (curl -s https://www.python.org/ftp/python/$PYTHONVER/Python-$PYTHONVER.tgz | tar xz) 2>>$LOGFILE || error 1 "$PYTHONVER download failed"
    fi
    cd Python-$PYTHONVER
    if [ ! -f Makefile ]; then
        notify "Configuring Python $PYTHONVER build"
        OPTIONS="--with-system-ffi --with-computed-gotos --enable-loadable-sqlite-extensions --enable-optimizations --enable-shared --with-openssl=/usr/include/openssl"
        run "./configure $PYTHON_OPTIONS" "$PYTHONVER configure failed"
    fi
    if [ ! -x python -o ! -x python-config ]; then
        notify "Building Python $PYTHONVER system"
        export CFLAGS="$CFLAGS -fPIC"
        run "make -j $(nproc)" "$PYTHONVER make failed"
    fi
    if [ ! -x /usr/local/bin/$PYTHONBIN ]; then
        notify "Installing Python $PYTHONVER"
        run "make altinstall" "$PYTHONVER make altinstall failed"
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
fi
notify "Python $PYTHONVER ok"

#
# Check library path
#
if [ ! -d "/etc/ld.so.conf.d" ]; then
    mkdir -p "/etc/ld.so.conf.d"
fi
if [ ! -f "/etc/ld.so.conf.d/local.conf" ]; then
    notify "Updating system library paths"
    echo "/usr/local/lib64" > "/etc/ld.so.conf.d/local.conf"
    run "ldconfig" "ldconfig failed"
fi

#
# Check active versions of main python executables
#
function checkver ()
{
    test "$($1 --version 1>/dev/null 2>&1)" == "$($2 --version 1>/dev/null 2>&1)" || warning "$1 is not linked to the correct version of $2"
}
cd /usr/local/bin
checkver python3 python3.10
checkver python python3
checkver pip3 pip3.10
checkver pip pip3

#
# GNU autotools
#
function gnubuild ()
{
    if [ "$($1 --version 2>/dev/null | sed -n '1p' | cut -f4 -d' ')" != "$2" ]; then
        notify "Upgrading $1 to $2"
        cd /usr/local/src
        (curl -s https://ftp.gnu.org/gnu/$1/$1-$2.tar.gz | tar xz) 2>>$LOGFILE || error 1 "unable to download $1-$2"
        cd $1-$2
        run "./configure" "unable to configure $1-$2"
        run "make install" "unable to make install $1-$2"
    fi    
    notify "$1-$2 ok"
}
gnubuild m4 $M4VER
gnubuild autoconf $AUTOCONFVER
gnubuild automake $AUTOMAKEVER
gnubuild libtool $LIBTOOLVER

#
# MDB tools
#
if [ "$(mdb-export --version 2>&1)" != "mdbtools v$MDBTOOLSVER" ]; then
    notify "Installing mdbtools"
    run "wget https://github.com/mdbtools/mdbtools/releases/download/v1.0.1/mdbtools-$MDBTOOLSVER.tar.gz" "unable to download mdbtools from github"
    run "tar xzf mdbtools-$MDBTOOLSVER.tar.gz" "unable to extract mdbtools-$MDBTOOLSVER"
    cd mdbtools-$MDBTOOLSVER
    run "./configure" "mdbtools configure failed"
    run "make" "mdbtools make failed"
    run "make install" "mdbtool install failed"
fi
notify "$(mdb-export --version) ok"

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
notify "System ready to build gridlabd. Run 'cd $GRIDLABDIR; ./build.sh --system --parallel' next."

exit 0
