import unittest

import fs
import fs.errors

class TestOpener(unittest.TestCase):
    
    def test_create(self):
        directory = '/'
        base = 'crashplanfs://' 
        url = base + directory
        
        # Check that the protocol is recognized
        with fs.open_fs(base) as cp_fs:
            cp_fs.listdir('/')
        
        # Make sure a non-existent directory raises `CreateFailed`
        #with self.assertRaises(fs.errors.CreateFailed):
        #    cp_fs = fs.open_fs(base + '/no/such/directory')
        
#        cp_fs = fs.open_fs(base + '/')
#        print cp_fs.listdir('/')