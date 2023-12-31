apt update 
apt install curl -y
. /etc/os-release

LATEST=$(curl -sL http://install.gridlabd.us/master.txt)

curl -sL https://install.gridlabd.us/

apt-get install git -y
git clone https://github.com/$GRIDLABD_ORG/$GRIDLABD_REPO -b $GRIDLABD_BRANCH --depth 1 gridlabd

cd /gridlabd
. $HOME/.gridlabd/bin/activate
autoreconf -isf
./configure
make -j$(($(nproc)*3)) system
gridlabd -T 0 --validate
