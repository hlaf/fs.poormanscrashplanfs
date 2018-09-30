from datetime import datetime, timedelta
import os
import pytz
import unittest

from fs.tempfs import TempFS
from fs.test import FSTestCases

from fs_crashplanfs.crashplan import CrashPlanFS

from test_utils import TestUtils

class TestCrashPlanFS(FSTestCases, unittest.TestCase, TestUtils):
    
    def make_fs(self):
        log_file = self.get_resource('crashplan_empty.log')
        fs = CrashPlanFS(log_file=log_file.strpath, show_local=True)
        return fs
    
    def countFiles(self, fs):
        return len([p for p in fs.walk.files()])

    def countDirs(self, fs):
        return len([p for p in fs.walk.dirs()])

    def test_logfile_to_fs_mapping(self):
        log_file = self.get_resource('crashplan_backup_files.log')
        fs = CrashPlanFS(log_file=log_file.strpath)
        
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
    
    def test_garbage_collection(self):
        
        log_file = self.get_resource('crashplan_backup_files.log')
        
        new_file = u'foo.txt'
        newer_file = u'/my/crashplan/backups/vms/finn/finn-2018-08-15_00-09-00/finn-5-s004.vmdk' 
        older_file = u'/my/crashplan/backups/vms/gabarolas/gabarolas-2018-08-02_16-07-17/gabarolas-s067.vmdk'
        
        with CrashPlanFS(log_file=log_file.strpath) as fs:
            assert not fs.exists(new_file)
            assert fs.exists(newer_file)
            assert fs.exists(older_file)
            older_file_remote_mtime = fs.getdetails(older_file).modified
        
        # Create a mock transfer area
        from fs.memoryfs import MemoryFS
        transfer_area = MemoryFS()
        
        # Populate the transfer area
        transfer_area.appendtext(new_file, u'This file is new')
        transfer_area.makedirs(os.path.split(newer_file)[0])
        transfer_area.appendtext(newer_file, u'This file has been modified locally')
        transfer_area.makedirs(os.path.split(older_file)[0])
        transfer_area.appendtext(older_file, u'This file is up-to-date')
        transfer_area.settimes(older_file, modified=older_file_remote_mtime)
        
        assert transfer_area.getdetails(older_file).modified <= older_file_remote_mtime
        
        # Pass the transfer area to crashplanfs
        fs = CrashPlanFS(log_file=log_file.strpath, transfer_area=transfer_area)
        
        # The new file should not be listed, as it only exists in the transfer area
        assert not fs.exists(new_file)
        
        # The newer file should be listed, with the remote modification time
        assert fs.exists(newer_file)
        assert transfer_area.getdetails(new_file).modified > fs.getdetails(newer_file).modified
        
        # The older file should be deleted from the transfer area
        assert not transfer_area.exists(older_file)
    
    def test_use_local_filesystem_as_transfer_area(self):
        
        log_file = self.get_resource('crashplan_backup_files.log')
        
        # Create a directory tree that can be used as a transfer area 
        with TempFS() as transfer_area:
            transfer_area.makedirs(u'/my/crashplan/backups')
            new_file = u'/my/crashplan/backups/foo.txt'

            with CrashPlanFS(log_file=log_file.strpath,
                             _local_fs_root=transfer_area.root_path) as fs:
                assert not transfer_area.exists(new_file)
                assert not fs.exists(new_file)
                fs.touch(new_file)
                assert transfer_area.exists(new_file)
        
        # Create a directory tree that cannot be mapped to the remote directory
        with TempFS() as transfer_area:
            transfer_area.makedirs(u'/unmapped/crashplan/backups')
            new_file = u'/my/crashplan/backups/foo.txt'

            with CrashPlanFS(log_file=log_file.strpath,
                             _local_fs_root=transfer_area.root_path) as fs:
                assert not transfer_area.exists(new_file)
                assert not fs.exists(new_file)
                fs.touch(new_file)
                assert not transfer_area.exists(new_file)
        
class TestCrashPlanFSSubDir(FSTestCases, unittest.TestCase, TestUtils):
    
    def make_fs(self):
        log_file = self.get_resource('crashplan_backup_files.log')
        fs = CrashPlanFS(log_file=log_file.strpath,
                         dir_path='/my/crashplan/backups/vms/empty_dir',
                         show_local=True)
        assert len(fs.listdir('/')) == 0
        return fs

    def test_listdir_nonempty_dir(self):
        fs = CrashPlanFS(
                log_file=self.get_resource('crashplan_backup_files.log').strpath,
                dir_path='/my/crashplan/backups')
        expected_dirs = set(['hypervisor', 'kinks', 'bureau', 'vms'])
        assert set(fs.listdir('/')) == expected_dirs
