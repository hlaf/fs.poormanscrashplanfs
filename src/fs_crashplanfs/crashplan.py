import atexit
from datetime import datetime
import glob
import io
import logging
import os
import tempfile

from fs import ResourceType
from fs.base import FS
from fs.mode import Mode
from fs.path import dirname
import fs.errors
from fs.info import Info
from fs.subfs import SubFS
from fs.permissions import Permissions

logger = logging.getLogger(__name__)

DEFAULT_CRASHPLAN_LOG_PATH = '/usr/local/crashplan/log'

class CrashPlanFile(io.IOBase):
    
    @classmethod
    def factory(cls, filename, mode):
        local_file = file(filename, mode.to_platform())
        proxy = cls(local_file, filename, mode)
        return proxy
    
    def __init__(self, f, filename, mode):
        self._f = f
        self.__filename = filename
        self.__mode = mode

    def flush(self):
        return self._f.flush()

    def readable(self):
        return self.__mode.reading

    def seek(self, offset, whence=os.SEEK_SET):
        if whence not in (os.SEEK_CUR, os.SEEK_END, os.SEEK_SET):
            raise ValueError("invalid value for 'whence'")
        self._f.seek(offset, whence)
        return self._f.tell()

    def seekable(self):
        return True

    def tell(self):
        return self._f.tell()

    def writable(self):
        return self.__mode.writing

    def read(self, n=-1):
        if not self.__mode.reading:
            raise IOError('not open for reading')
        return self._f.read(n)
    
    def write(self, b):
        if not self.__mode.writing:
            raise IOError('not open for writing')
        self._f.write(b)
        return len(b)

    def truncate(self, size=None):
        if size is None:
            size = self._f.tell()
        self._f.truncate(size)
        return size

class CrashPlanLog:
    def __init__(self, log_path=None, log_file=None):
        if log_path is None:
            log_path = DEFAULT_CRASHPLAN_LOG_PATH

        if log_file:
            log_files = [log_file]
        else:
            log_files = glob.glob(os.path.join(log_path, 'backup_files.log.*'))

        lines = []
        for log_file in log_files:
            with open(log_file, 'r') as f:
                lines.extend(f.readlines())
        self._lines = lines

    def getLines(self):
        return self._lines
        
    def getLinesFor(self, s):
        res = [l for l in self.getLines() if s in l and l.startswith('I ')
                                                    and len(l.split()) > 6
                                                    and len(l.split()[4]) == 32
                                                    and l.split()[6].startswith(s)]
        return res
        
class CrashPlanFS(FS):
    
    _meta = {
        'invalid_path_chars': '\0',
    }
    
    def __init__(self, root_dir='/', log_file=None):
        super(CrashPlanFS, self).__init__()
        
        self._data_provider = CrashPlanLog(log_file=log_file)
        
        root_dir_tmp = tempfile.mkdtemp(prefix='crashplanfs')
        self.proxy_root = root_dir_tmp
    
    def _info_from_remote_resource(self, path, namespaces):
        resource_lines = self._data_provider.getLinesFor(path)
        if len(resource_lines) == 0:
            raise fs.errors.ResourceNotFound(path)
        
        # check if it is an exact match
        exact_matches = [r for r in resource_lines if r.split()[6] == path]
        
        if len(exact_matches) == 0:
            # It's an intermediate directory, without a dedicated log entry
            entry = resource_lines[-1]
            is_dir = True
        else: # get the most recent entry for the resource
            entry = exact_matches[-1]
            is_dir = int(entry.split()[5]) == 1
        
        raw_info = {}
        
        # basic namespace
        basic = {}
        raw_info['basic'] = basic
        basic['name'] = os.path.split(path)[-1]
        basic['is_dir'] = is_dir

        # details namespace
        if 'details' in namespaces:
            details = {}
            raw_info['details'] = details
            date_str = ' '.join(entry.split()[1:3])
            date_obj = datetime.strptime(date_str, '%m/%d/%y %I:%M%p')
            epoch_time = (date_obj - datetime(1970, 1, 1)).total_seconds()
            details['modified'] = epoch_time
            details['type'] = int(ResourceType.directory if basic['is_dir']
                                  else ResourceType.file)
        
        if 'access' in namespaces:
            access = {}
            raw_info['access'] = access
            access['permissions'] = Permissions(mode=0o755).dump()
        
        return raw_info
    
    def _get_local_path(self, path):
        return os.path.join(self.proxy_root, path.lstrip('/'))
        
    def getinfo(self, resource_path, namespaces=None):
        self.check()
        namespaces = namespaces or ()
        
        # check if the resource exists in the transfer area
        local_resource_path = self._get_local_path(resource_path)
        is_local = os.path.exists(local_resource_path)

        if not is_local:
            return Info(self._info_from_remote_resource(resource_path, namespaces))
            
        # basic namespace
        info = {}
        basic = {}
        info['basic'] = basic
        basic['name'] = os.path.split(resource_path)[-1]
        basic['is_dir'] = os.path.isdir(local_resource_path)
        
        if 'details' in namespaces:
            details = {}
            info['details'] = details
            #date_str = ' '.join(entry.split()[1:3])
            #date_obj = datetime.strptime(date_str, '%m/%d/%y %I:%M%p')
            #epoch_time = (date_obj - datetime(1970, 1, 1)).total_seconds()
            #details['modified'] = epoch_time
            details['size'] = os.stat(local_resource_path).st_size
            details['type'] = int(ResourceType.directory if basic['is_dir']
                                  else ResourceType.file)
        
        if 'access' in namespaces:
            access = {}
            info['access'] = access
            access['permissions'] = Permissions(mode=0o755).dump()
        
        return Info(info)
        
    def _has_local_version(self, path):
        return os.path.exists(self._get_local_path(path))
    
    def listdir(self, path):
        self.check()
        
        _type = self.gettype(path)
        if _type is not ResourceType.directory:
            raise fs.errors.DirectoryExpected(path)
        
        local_path_entries = []
        if self._has_local_version(path):
            local_path_entries = os.listdir(self._get_local_path(path))
        
        entries = [line.split() for line in self._data_provider.getLinesFor(path)]
        remote_path_entries = set(os.path.basename(e[6]) for e in entries if os.path.dirname(e[6]) == path)
        
        return list(remote_path_entries.union(local_path_entries))

    def makedir(self, path, permissions=None, recreate=False):
        self.check()
        _path = self.validatepath(path)
        
        if not self.isdir(dirname(_path)):
            raise fs.errors.ResourceNotFound(path)
        
        try:
            self.getinfo(path)
        except fs.errors.ResourceNotFound:
            # The directory exists neither remotely nor locally
            os.makedirs(self._get_local_path(_path))
        else:
            if recreate:
                return self.opendir(_path)
            else:
                raise fs.errors.DirectoryExists(path)
        
        return SubFS(self, path)

    def openbin(self, path, mode="r", buffering=-1, **options):
        _mode = Mode(mode)
        _mode.validate_bin()
        self.check()
        self.validatepath(path)
        
        if _mode.create:
            try:
                dir_path = dirname(path)
                if dir_path != '/':
                    self.getinfo(dir_path)
            except fs.errors.ResourceNotFound:
                raise fs.errors.ResourceNotFound(path)
            
            try:
                info = self.getinfo(path)
            except fs.errors.ResourceNotFound:
                pass
            else:
                if _mode.exclusive:
                    raise fs.errors.FileExists(path)
                if info.is_dir:
                    raise fs.errors.FileExpected(path)
            
            cpfile = CrashPlanFile.factory(self._get_local_path(path), _mode)
        else:
            info = self.getinfo(path)
            if info.is_dir:
                raise fs.errors.FileExpected(path)
            
            cpfile = CrashPlanFile.factory(self._get_local_path(path), _mode)
        
        return cpfile

    def remove(self, path):
        self.check()
        info = self.getinfo(path)
        if info.is_dir:
            raise fs.errors.FileExpected(path)
        os.remove(self._get_local_path(path))

    def removedir(self, path):
        self.check()
        _path = self.validatepath(path)
        if _path == '/':
            raise fs.errors.RemoveRootError()
        info = self.getinfo(_path)
        if not info.is_dir:
            raise fs.errors.DirectoryExpected(path)
        if not self.isempty(path):
            raise fs.errors.DirectoryNotEmpty(path)
        os.rmdir(self._get_local_path(_path))

    def setinfo(self, path, info):
        self.getinfo(path)

    def geturl(self, path, purpose='download'):
        _path = self.validatepath(path)
        if _path == '/':
            raise fs.errors.NoURL(path, purpose)
        if purpose == 'download':
            return "crashplanfs://{}".format(_path)
        else:
            raise fs.errors.NoURL(path, purpose)
