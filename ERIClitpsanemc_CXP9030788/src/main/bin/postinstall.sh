# Setup python path
SITE=`python -c "from distutils.sysconfig import get_python_lib; print(get_python_lib())"`
echo "# using 1_ in the .pth filename to ensure the following path occurs" > $SITE/1_sanapi.pth
echo "# occurs in PYTHONPATH before litp path" >> $SITE/1_sanapi.pth
echo "/${rpm-root}/${comp-name}/${install-path}" >> $SITE/1_sanapi.pth
/usr/bin/nohup /usr/bin/yum install -y python-requests &> /tmp/requests_install.log &
