"""Defines the CrashPlanFSOpener."""

__all__ = ['CrashPlanFSOpener']

from fs.opener import Opener

from .crashplan import CrashPlanFS


class CrashPlanFSOpener(Opener):
    protocols = ['crashplanfs']

    def open_fs(self, fs_url, parse_result, writeable, create, cwd):
        dir_path = parse_result.resource
        
        cpfs = CrashPlanFS(
              dir_path,
              log_file=None
        )
        return cpfs