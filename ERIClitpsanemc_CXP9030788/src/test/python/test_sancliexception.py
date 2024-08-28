'''
Created on 26 Jun 2014

@author: edavmax
'''
import unittest
from sancliexception import  *
from testfunclib import *


class TestSanCliException(unittest.TestCase):


    def setUp(self):
        pass

    def tearDown(self):
        pass


    def test_cmdexception(self):
        ''' check exception message and return code can be accessed'''
        exceptionmsg1="Here is some error text"
        exceptioncode1=43
        print self.shortDescription()
        myassert_raises_regexp(self, SanCliException, exceptionmsg1,  self.exception_raiser, exceptionmsg1, exceptioncode1)

    def exception_raiser(self, msg, code):
        ''' function to raise and exeception '''
        raise SanCliException(msg, code)

if __name__ == "__main__":
    #import sys;sys.argv = ['', 'Test.testName']
    unittest.main()
