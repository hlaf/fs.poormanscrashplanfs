import pkg_resources
import unittest

import fs
import fs.errors

# Add additional openers to the entry points
pkg_resources.get_entry_map('fs', 'fs.opener')['crashplanfs'] = \
    pkg_resources.EntryPoint.parse(
        'crashplanfs = fs_crashplanfs.opener:CrashPlanFSOpener',
        dist=pkg_resources.get_distribution('fs')
    )

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