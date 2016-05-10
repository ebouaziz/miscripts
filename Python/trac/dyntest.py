#!/usr/bin/env python2.7
# -*- coding: utf-8 -*-

# Prototyping XTest. Fully useless now

import os
import unittest
import sys

class DynTestCase(unittest.TestCase):

    def setUp(self):
        print "setUp"

    def tearDown(self):
        print "tearDown"

    def test_static(self):
        print 'test_static'

    def __init__(self, x):
        super(DynTestCase, self).__init__(x)
        print "INIT: %s %s" % (x, id(self))

    @classmethod
    def add_test(_cls_, name, value):
        def _test(self):
            if value == 'fail':
                raise AssertionError('Fake error')
            print "test_dynamic %s" % value
        _test.__doc__ = "Dynamic test for %s" % name
        _test.__name__ = "test_%s" % name
        setattr(_cls_, _test.__name__, _test)


def suite():
    suite = unittest.TestSuite()
    DynTestCase.add_test('new_test', 'parameter')
    DynTestCase.add_test('new_test2', 'something')
    DynTestCase.add_test('new_test3', 'fail')
    DynTestCase.add_test('new_test2', 'ok')
    suite.addTest(unittest.makeSuite(DynTestCase, 'test'))
    return suite


if __name__ == '__main__':
    unittest.main(defaultTest='suite')
