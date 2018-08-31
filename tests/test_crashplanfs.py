from datetime import datetime, timedelta
import os
import pytz
import unittest

import py
from fs.test import FSTestCases

from fs_crashplanfs.crashplan import CrashPlanFS


class TestUtils(object):
    
    def get_test_data_dir(self):
        return py.path.local(os.path.dirname(os.path.abspath(__file__))).join('data')

    def get_resource(self, resource_name):
        resource_path = self.get_test_data_dir().join(resource_name)
        assert resource_path.check()
        return resource_path


class TestCrashPlanFS(FSTestCases, unittest.TestCase, TestUtils):
    
    def make_fs(self):
        log_file = self.get_resource('crashplan_backup_files.log')
        fs = CrashPlanFS(log_file=log_file.strpath)
        return fs
    
    def countFiles(self, fs):
        return len([p for p in fs.walk.files()])

    def countDirs(self, fs):
        return len([p for p in fs.walk.dirs()])

    def test_logfile_to_fs_mapping(self):
        fs = self.make_fs()
        expected_dirs = set(['hypervisor', 'kinks', 'bureau', 'vms'])
        assert set(fs.listdir('/my/crashplan/backups')) == expected_dirs
        
        vms_fs = fs.opendir('/my/crashplan/backups/vms')
        assert len(vms_fs.listdir('/')) == 16
        
        assert self.countFiles(vms_fs.opendir('unbearable')) == 48
        assert self.countDirs(vms_fs.opendir('unbearable')) == 2
        
        assert self.countFiles(vms_fs.opendir('gabarolas')) == 418
        assert self.countDirs(vms_fs.opendir('gabarolas')) == 4
        
        assert self.countFiles(vms_fs.opendir('morning_dew')) == 516
        assert self.countDirs(vms_fs.opendir('morning_dew')) == 4
        
        assert self.countFiles(fs.opendir('/my/crashplan/backups/bureau')) == 90
        assert self.countDirs(fs.opendir('/my/crashplan/backups/bureau')) == 90

        # test modification date
        # AM time
        modified = vms_fs.getinfo('gabarolas/gabarolas-2018-08-02_16-07-17/'
                                  'gabarolas-s067.vmdk',
                                  namespaces=['details']).modified
        assert modified == datetime(2018, 8, 21, 0, 14, tzinfo=pytz.UTC)
        
        # PM time
        modified = vms_fs.getinfo('finn/finn-2018-08-15_00-09-00/finn-5-s004.vmdk',
                                  namespaces=['details']).modified
        assert modified == datetime(2018, 8, 23, 14, 45, tzinfo=pytz.UTC)
        
        
class TestCrashPlanFSSubDir(FSTestCases, unittest.TestCase, TestUtils):
    
    def make_fs(self):
        log_file = self.get_resource('crashplan_backup_files.log')
        fs = CrashPlanFS(log_file=log_file.strpath,
                         dir_path='/my/crashplan/backups/vms/empty_dir')
        assert len(fs.listdir('/')) == 0
        return fs

    def test_listdir_nonempty_dir(self):
        fs = CrashPlanFS(
                log_file=self.get_resource('crashplan_backup_files.log').strpath,
                dir_path='/my/crashplan/backups')
        expected_dirs = set(['hypervisor', 'kinks', 'bureau', 'vms'])
        assert set(fs.listdir('/')) == expected_dirs
