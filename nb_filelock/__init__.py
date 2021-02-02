import os
import abc
import pathlib

"""

python 中引入给文件加锁的 fcntl模块


import fcntl
打开一个文件


##当前目录下test文件要先存在，如果不存在会报错。或者以写的方式打开
f = open('./test')
对该文件加密：


fcntl.flock(f,fcntl.LOCK_EX)
这样就对文件test加锁了，如果有其他进程对test文件加锁，则不能成功，会被阻塞，但不会退出程序。

解锁：fcntl.flock(f,fcntl.LOCK_UN)

fcntl模块：

flock() : flock(f, operation)

operation : 包括：
    fcntl.LOCK_UN 解锁
    fcntl.LOCK_EX  排他锁
    fcntl.LOCK_SH  共享锁
    fcntl.LOCK_NB  非阻塞锁

LOCK_SH 共享锁:所有进程没有写访问权限，即使是加锁进程也没有。所有进程有读访问权限。

LOCK_EX 排他锁:除加锁进程外其他进程没有对已加锁文件读写访问权限。
LOCK_NB 非阻塞锁:
如果指定此参数，函数不能获得文件锁就立即返回，否则，函数会等待获得文件锁。

LOCK_NB可以同LOCK_SH或LOCK_NB进行按位或（|）运算操作。 fcnt.flock(f,fcntl.LOCK_EX|fcntl.LOCK_NB)
"""
if os.name == 'nt':
    # noinspection PyPep8,PyPep8
    import win32con
    import win32file
    import pywintypes

    LOCK_EX = win32con.LOCKFILE_EXCLUSIVE_LOCK
    LOCK_SH = 0  # The default value
    LOCK_NB = win32con.LOCKFILE_FAIL_IMMEDIATELY
    _overlapped = pywintypes.OVERLAPPED()  # noqa
else:
    import fcntl


class BaseLock(metaclass=abc.ABCMeta):
    def __init__(self, lock_file_path: str):
        self.f = open(lock_file_path, 'a')

    @abc.abstractmethod
    def __enter__(self):
        raise NotImplemented

    @abc.abstractmethod
    def __exit__(self, exc_type, exc_val, exc_tb):
        raise NotImplemented


class WindwosFileLock(BaseLock):
    """
    已近经过测试，即使某个脚本把文件锁获得后，突然把那个脚本关了，另一个脚本也会获得文件锁。不会死锁导致代码无限等待。
    """

    def __enter__(self):
        self.hfile = win32file._get_osfhandle(self.f.fileno())  # noqa
        win32file.LockFileEx(self.hfile, LOCK_EX, 0, 0xffff0000, _overlapped)

    def __exit__(self, exc_type, exc_val, exc_tb):
        # noinspection PyProtectedMember
        # hfile = win32file._get_osfhandle(self.f.fileno())
        win32file.UnlockFileEx(self.hfile, 0, 0xffff0000, _overlapped)


class LinuxFileLock(BaseLock):
    def __enter__(self):
        fcntl.flock(self.f, fcntl.LOCK_EX)

    def __exit__(self, exc_type, exc_val, exc_tb):
        fcntl.flock(self.f, fcntl.LOCK_UN)


FileLock = WindwosFileLock if os.name == 'nt' else LinuxFileLock

# noinspection PyUnresolvedReferences,PyUnresolvedReferences
if __name__ == '__main__':
    """ 把这个脚本连续反复启动多个可以测试文件锁，只有获得文件锁，代码块才能执行"""
    import nb_log
    import time

    print('wait for lock')
    with FileLock(pathlib.Path(__file__).parent / pathlib.Path('testx.lock')):
        print('hi')
        time.sleep(20)
        print('hello')
