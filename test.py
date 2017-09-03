#!/usr/bin/env python

import unittest

def main():
    
    suite = unittest.defaultTestLoader.discover("tests")
    
    unittest.TextTestRunner(verbosity=2).run(suite)

if __name__ == '__main__':
    main()