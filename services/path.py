__all__ = (
    'create_dir',
    'clear_dir',
    'create_src'
)

import os
import sys

from utils.utils import create_directory, clear_directory

machine = sys.platform


class Path:

    def __init__(self, message_id=None, file_path=None):
        self.msg_id = message_id
        self.f_path = file_path
        self.get_cwd = os.getcwd()

    def file_path(self):
        return os.path.join(self.get_cwd, 'src', f'{self.msg_id}', self.f_path)

    def photo_path(self):
        return os.path.join(self.get_cwd, 'src', f'{self.msg_id}', 'photos')

    def video_path(self):
        return os.path.join(self.get_cwd, 'src', f'{self.msg_id}', 'videos')

    def report_path(self):
        return os.path.join(self.get_cwd, 'src', 'reports')


def create_src(message_id: int = None, file_path: str = None) -> str:
    if machine in ['win32']:
        return Path(message_id=message_id, file_path=file_path.replace("/", "\\")).file_path()
    elif machine in ['aix', 'linux', 'cygwin', 'darwin']:
        return Path(message_id=message_id, file_path=file_path).file_path()


def create_dir(message_id: int = None, dir_type: str = 'photo') -> None:
    if dir_type == 'photo':
        create_directory(Path(message_id=message_id).photo_path())
    elif dir_type == 'video':
        create_directory(Path(message_id=message_id).video_path())
    elif dir_type == 'report':
        create_directory(Path().report_path())
    else:
        raise AttributeError("Не известный тип файла: '%s'" % dir_type)


def clear_dir(message_id: int = None, dir_type: str = 'photo') -> None:
    if dir_type == 'photo':
        clear_directory(Path(message_id=message_id).photo_path())
    elif dir_type == 'video':
        clear_directory(Path(message_id=message_id).video_path())
    elif dir_type == 'report':
        clear_directory(Path().report_path())
    else:
        raise AttributeError("Не известный тип файла: '%s'" % dir_type)
