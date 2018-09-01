"""Defines the CrashPlanFSOpener."""

__all__ = ['CrashPlanFSOpener']

from fs.opener import Opener

from .crashplan import CrashPlanFS


class CrashPlanFSOpener(Opener):
    protocols = ['crashplanfs']

    def open_fs(self, fs_url, parse_result, writeable, create, cwd):
        dir_path = parse_result.resource
        
        cp_fs = CrashPlanFS(
              dir_path=dir_path,
              log_file=parse_result.params.get('logfile'),
              create=create,
        )
        return cp_fs