import unittest
import re


class TestSanEMC(unittest.TestCase):

    def assertIsInstance(self, obj, cls):
        """
        Implementation of assertIsInstance (which is available in 2.7)
        """
        yes = isinstance(obj, cls)
        if not yes:
            self.fail("%s is type %s, should be %s" % (obj, type(obj), cls))

    def assertRaisesRegexp(self, exceptiontype, message, function, *args,
            **kwargs):
        '''
        implementation of AssertRaisesRegexp for 2.6
        (AssertRaisesRegexp was added to 2.7)

        '''
        try:
            function(*args, **kwargs)
        except exceptiontype as e:
            if not re.search(message, e.args[0]):
                self.fail("Exception " + str(exceptiontype) +
                        " does not contain expected message " + message +
                               ". Contents of exception:" + e.args[0])
        except Exception as e:
            self.fail("No Exception of type " + str(exceptiontype)
                    + " raised," + "Exception '" + str(e) +
                    "' raised instead.")
        else:
            self.fail("No Exception of any type raised")

    def assertRaises(self, exceptiontype, function, *args, 
            **kwargs):
        try:
            function(*args, **kwargs)
        except exceptiontype as e:
            return True
        except Exception as e:
            self.fail("No Exception of type " + str(exceptiontype)
                    + " raised," + "Exception '" + str(e) +
                    "' raised instead.")
        else:
            self.fail("No Exception of any type raised")
