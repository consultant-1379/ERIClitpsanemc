#!/bin/bash

G_SCRIPTDIR=$(cd $(dirname $0); pwd)
artifact=$1
host=$2
password=$3
remotetmpdir=/var/tmp

if [ -z "$artifact" ]; then
	echo "artifact must be specified"
	exit 1
fi
if [ -z "$host" ]; then
	echo "host/ip must be specified"
	exit 1
fi
if [ -z "$password" ]; then
	echo "password must be specified"
	exit 1
fi


echo "Copying artifact to $host"
/usr/bin/expect $G_SCRIPTDIR/ssh_setup2.sh scp "$artifact root@$host:$remotetmpdir" $password > /dev/null || {
	echo "Failed to copy artifact to host $host"
	exit 1
}

if [ ${artifact##*.} == "tar" ]; then
	echo "Installing tar file on $host"
	l_installdir=/opt/ericsson/sanapi
	echo "Removing existing version (if it exists) ..."
	/usr/bin/expect $G_SCRIPTDIR/ssh_setup2.sh ssh "root@$host /bin/rm -rf $l_installdir" $password > /dev/null 
	
	echo "Making dir on $host"
	/usr/bin/expect $G_SCRIPTDIR/ssh_setup2.sh ssh "root@$host mkdir -p $l_installdir" $password > /dev/null || {
		echo "Failed to make $l_installdir on host"
		exit 1
	}
	/usr/bin/expect $G_SCRIPTDIR/ssh_setup2.sh ssh "root@$host cd $l_installdir && tar xvf $remotetmpdir/$( basename $artifact )" $password > /dev/null || {
		echo "Failed to install $(basename $artifact) on $host "
		exit 1
	}
elif [ ${artifact##*.} == "rpm" ]; then
	echo "Installing rpm file on $host"
	/usr/bin/expect $G_SCRIPTDIR/ssh_setup2.sh ssh "root@$host rpm -Uvh --force $remotetmpdir/$( basename $artifact )" $password > /dev/null || {
		echo "Failed to install $(basename $artifact) on $host "
		exit 1
	}
	
	
else
	echo "Error - sorry can only handle tar and rpm artifacts at the moment"
	exit 1
fi



