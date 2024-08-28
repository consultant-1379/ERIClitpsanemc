'''
Created on 26 Jun 2014

@author: edavmax
'''
import unittest
from sanapiexception import  *
from testfunclib import *


class TestSanApiException(unittest.TestCase):


    def setUp(self):
        pass
        
    def tearDown(self):
        pass


    def test_cmdexception(self):
        ''' check exception message and return code can be accessed'''
        exceptionmsg1="Here is some error text"
        exceptioncode1=43
        print self.shortDescription() 
        myassert_raises_regexp(self, SanApiException, exceptionmsg1,  self.exception_raiser, exceptionmsg1, exceptioncode1)
        
    def exception_raiser(self, msg, code):
        ''' function to raise and exeception '''
        raise SanApiException(msg, code)

if __name__ == "__main__":
    #import sys;sys.argv = ['', 'Test.testName']
    unittest.main()
