#/bin/sh
# 
# Note: double hash comments indicates help documentation
#
## Syntax: build.sh [OPTIONS]
## 
## Build gridlabd on this local system. You must have run `setup.sh` first.
## 
## Options:
## 
##   -v|--verbose)   Enable output of commands as they are executed
## 
##   -s|--silent)    Disable output to stderr
## 
##   -q|--quiet)     Disable output to stdout
## 
##   --validate)     Enable validation of build (requires --install)
##
##   --validateghactions)     Enable validation of build, enables adjustments to account for github runner differences (requires --install)
## 
##   --install)      Install build to target folder
## 
##   --system)       Make the install the system default installation
## 
##   --target PATH)  Specify the target folder (default is output of /usr/local/opt)
## 
##   --clean)        Delete all new uncommitted source files before starting build
## 
##   --upload)       Upload installed image to AWS when build is done
## 
##   --release)      Make AWS upload the default image for system/machine type
## 
##   --parallel[=N]) Run the build in parallel if possible. N specifies how many jobs
##                   per CPU. The default is 3 jobs per CPU.
## 
##   --srcdir=DIR    Specify an alternate source directory to use (default is
##                   same as build.sh script) 
##
##   --workdir=DIR   Specify an alternate working directory to use (default is
##                   same as build.sh script)
##
## Environment variables:
## 
##   MAKEFLAGS   Specify additional make options
## 
##   CFLAGS      Specify additional C compiler flags
## 
##   CPPFLAGS    Specify additional C++ compiler flags
## 
##   LDFLAGS     Specify additional linker flags
## 
## Example:
## 
##   A typical first-time build/install command is usually
##
##   $ ./build.sh --parallel --system
##
cd $(dirname $0)
STDOUT=/dev/stdout
STDERR=/dev/stderr
error () { echo "ERROR [build.sh]: $*" > $STDERR ; exit 1; }
TARGET=
if [ -d "config.cache" ]; then
	CONFIGURE="-C"
else
	CONFIGURE=
fi
UPLOAD=
SRCDIR=$PWD
WORKDIR=$PWD
SILENT_RULES="--enable-silent-rules"
while [ $# -gt 0 ]; do
	case "$1" in
		-h | --help | help )
			cat $0 | grep '^## ' | cut -c4-
			exit 0
			;;
		-v | --verbose )
			set -x
			MAKEFLAGS="$MAKEFLAGS --debug V=1"
			unset SILENT_RULES
			;;
		-s | --silent )
			STDERR=/dev/null
			;;
		-q | --quiet )
			STDOUT=/dev/null
			;;
		--validate )
			if [ -z "$VERIFY" ]; then
				error "cannot validate unless you install"
			fi
			VERIFY="-T 0 --validate"
			;;
   		--validateghactions )
			if [ -z "$VERIFY" ]; then
				error "cannot validate unless you install"
			fi
			VERIFY="-T 0 --validate -D github_actions=yes"
			;;
		--ignore )
			export MAKEFLAGS="$MAKEFLAGS -i"
			;;
		--install )
			VERIFY="--version=all"
			TARGET="$TARGET install"
			;;
		--system)
			VERIFY="--version=all"
			TARGET="$TARGET system"
			;;
		--target )
			CONFIGURE="$CONFIGURE --prefix=$2"
			shift 1
			;;
		--clean )
			utilities/cleanwc
			;;
		--upload )
			UPLOAD=aws-image
			;;
		--release )
			UPLOAD=aws-image-default
			;;
		--nomakemd )
			MAKEFLAGS="$MAKEFLAGS MAKEMD=no"
			;;
		--parallel | --parallel=* )
			PROCS=$(echo $1 | cut -f2 -d=)
			test "$PROCS" = "--parallel" && PROCS=3
			if nproc --help 1>/dev/null 2>&1 ; then
				export MAKEFLAGS="$MAKEFLAGS -j$(($(nproc)*$PROCS))"
			elif sysctl -a 1>/dev/null 2>&1 ; then
				export MAKEFLAGS="$MAKEFLAGS -j$(($(sysctl -n hw.ncpu)*$PROCS))"
			else
				error "unable to determine the number of available CPUs"
			fi
			;;
		--srcdir=*)
			SRCDIR=$(echo $1 | cut -f2 -d=)
			;;
		--workdir=* )
			WORKDIR=$(echo $1 | cut -f2 -d=)
			mkdir -p $WORKDIR
			cd $WORKDIR
			;;
		* )
			error "option '$1' is not valid"
			;;
	esac
	shift 1
done

OS_NAME=$(uname -s)
OS_VERSION=$(uname -r)

if [ "$OS_NAME" = "Darwin" ] && [ "${OS_VERSION%%.*}" -ge 23 ]; then
    REQUIRED_AUTOCONF_VERSION="2.72"
	TEST_AUTOCONF_VERSION="2.71"
else
    REQUIRED_AUTOCONF_VERSION="2.71"
	TEST_AUTOCONF_VERSION="2.70"
fi

mkdir -p /usr/local/opt/gridlabd || error "you do not have permission to create /usr/local/opt/gridlabd"
autoconf --version 1>/dev/null 2>&1 || error "autoconf not installed. Did you run setup.sh?"
test "$(autoconf --version 2>/dev/null | head -n 1 | grep -o '[^ ]*$')" '>' "$TEST_AUTOCONF_VERSION" || error "autoconf version $REQUIRED_AUTOCONF_VERSION or later required. Did you run setup.sh?"
git --version 1>/dev/null 2>&1 || error "you must install git to build GridLAB-D"
test -f $SRCDIR/configure.ac || error "you must build from the source directory where configure.ac is located"
test -f $HOME/.gridlabd/bin/activate || error "$HOME/.gridlabd is not found. Run setup.sh again."
test ! -z "$VIRTUAL_ENV" || . $HOME/.gridlabd/bin/activate 1>$STDOUT 2>$STDERR
test ! -z "$VIRTUAL_ENV" || error "unable to activate gridlabd venv"
test -f $SRCDIR/configure || autoreconf -isf $SRCDIR 1>$STDOUT 2>$STDERR || error "autoconf failed"
test -f Makefile || $SRCDIR/configure $SILENT_RULES $CONFIGURE 1>$STDOUT 2>$STDERR || error "./configure failed"
make $MAKEFLAGS $TARGET 1>$STDOUT 2>$STDERR || error "unable to make build"
if [ ! -z "$VERIFY" ]; then
	$($SRCDIR/build-aux/version.sh --install)/bin/gridlabd $VERIFY 1>$STDOUT 2>$STDERR || error "unable to verify install"
fi
test -z "$UPLOAD" || make $UPLOAD 1>$STDOUT 2>$STDERR
