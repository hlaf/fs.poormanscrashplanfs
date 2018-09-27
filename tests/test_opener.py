import pkg_resources
import unittest

import fs
import fs.errors

from test_utils import TestUtils

# Add additional openers to the entry points
pkg_resources.get_entry_map('fs', 'fs.opener')['crashplanfs'] = \
    pkg_resources.EntryPoint.parse(
        'crashplanfs = fs_crashplanfs.opener:CrashPlanFSOpener',
        dist=pkg_resources.get_distribution('fs')
    )

class TestOpener(unittest.TestCase, TestUtils):
    
    def test_create(self):
        directory = '/'
        base = 'crashplanfs://' 

        log_file = self.get_resource('crashplan_backup_files.log').strpath

        # Check that the protocol is recognized
        with fs.open_fs(base) as cp_fs:
            cp_fs.listdir('/')
        
        # Make sure a non-existent log file raises `CreateFailed`
        with self.assertRaises(fs.errors.CreateFailed):
            cp_fs = fs.open_fs(base + '?logfile={}'.format('nonexistent.log'))
        
        # Make sure a valid log file is read-in correctly 
        with fs.open_fs(base + '?logfile={}'.format(log_file)) as cp_fs:
            assert set(cp_fs.listdir('/')) == set(['my'])
            assert set(cp_fs.listdir('/my/')) == set(['crashplan'])
            assert set(cp_fs.listdir('/my/crashplan')) == set(['backups'])
        
        nonexistent_dir = '/no/such/directory'
        
        # Make sure a non-existent directory raises `CreateFailed`
        with self.assertRaises(fs.errors.CreateFailed):
            cp_fs = fs.open_fs(base + nonexistent_dir)

        # Opening a non-existent directory with `create` should work
        with fs.open_fs(base + nonexistent_dir + '?logfile={}&show_local=true'.format(log_file),
                        create=True) as cp_fs:
            self.assertTrue(cp_fs.isdir(nonexistent_dir))

        # Check that the URL returned by geturl() contains all the information
        # required to reopen the resource
        valid_path = '/my/crashplan/backups'
        with fs.open_fs(base + '?logfile={}'.format(log_file)) as cp_fs: 
            self.assertTrue(cp_fs.isdir(valid_path))
            self.assertTrue('vms' in cp_fs.listdir(valid_path))
            valid_path_url = cp_fs.geturl(valid_path)
        with fs.open_fs(valid_path_url) as cp_fs:
            self.assertTrue('vms' in cp_fs.listdir('/'))
