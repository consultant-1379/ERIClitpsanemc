#!/bin/bash

G_SCRIPTDIR=$(cd $(dirname $0); pwd)

tarfiledir=$1

if [ ! -d "$tarfiledir" ]; then
	echo "Error - tarfile dir $tarfiledir not found"
	exit 1
fi

codedir=$( cd $G_SCRIPTDIR/..; pwd )
pomfile=$( cd $G_SCRIPTDIR/../../..; pwd )/pom.xml
if [ ! -s $pomfile ]; then
	echo "Error - pomfile not found !!"
	exit 1
fi
productname=$( sed -n 's:.*<artifactId>\(.*\)</artifactId>.*:\1:p' $pomfile | grep ERIC | tr -d '\n' )
version=$( sed -n 's:.*<version>\(.*\)</version>.*:\1:p' $pomfile | head -n1 | tr -d '\n' )
sanapitarfile=${tarfiledir}/${productname}_${version}.tar

cd $G_SCRIPTDIR/../python
find . -name \*.pyc -exec rm {} \;
echo "Creating $sanapitarfile"
tar cvf $sanapitarfile . ../etc > /dev/null || {
	echo "Failed to create $sanapitarfile"
	exit 1
}

