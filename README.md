## 1. pip install nb_filelock

基于代码所在机器的跨进程 跨解释器的文件互斥锁。兼容windwos和linux

filelock,which can run on linux and windwos.

## 文件锁的功能意义
```
此文件锁并不是为了解决多个python程序写入同一个txt文件的问题(当然顺便也解决了这个问题)，
而是借助文件锁这种中间件介质(类比redis分布式锁使用redis做中间件介质)，
从而实现当前机器无论启动多少次脚本，只有一个脚本能获得锁从而执行锁里面的代码块。
```

## 各种锁的能力影响范围大小

锁的能力范围大小是  多线程锁  <  多进程锁  <  文件锁  <  redis分布式锁。

```
线程锁只能确保单一进程的不同线程只有一个线程能获得锁从而执行代码块

多进程锁针对不同进程，但有个前提是，进程必须是这么饿启动的，
例如 a.py 文件，在a.py文件里面的代码需要引用muliprossing包的Process(target=func).start()来启动多进程
如果是把 a.py反复手动运行两次，而不是用了muliprossing包来一次性启动的，两次a.py的进程完全毫不相关，
这种不同的脚本进程彼此没法知道另一个进程里面的变量，此时需要引入一种中间介质，每个脚本都去读取这个中间件介质来获得锁才可以，
可以使用redis分布式锁，但这种比较烦需要安装一个redis，没安装redis的环境代码就无法运行了。所以就是要开发一种文件锁，不需要安装中间件。

文件锁, 影响范围是当前机器，能够跨不同批次的启动脚本的解释器，确保代码里面只有一个地方能获得文件锁，从而执行代码块。
比如希望在当前机器只能同时运行某一个代码块，完全豪不相关的两次启动xx.py，没有办法使用进程锁，
压根就不是使用multiprossing包同时启动的多个子进程而是手动两次运行了python xx.py，
好的方式是使用redis分布式锁，可以保证所有机器只提示一个获得锁，但如果没安装redis切要保证当前机器只有一个能执行代码块，就需要这个。


redis分布式锁，能影响的范围最强力最广泛，不进能够跨本机的解释器，还能跨机器，可以确保几百台电脑只有一个地方能获得锁从而执行代码块，但要安装redis。
```


### 测试例子。

```
把下面的python文件复制到一个文件中叫test.py,然后重复启动两次 python test.py，
当第一个脚本还没执行完代码块时候，另一个脚本会等待第一个脚本执行完成代码块的语句才会开始print hi。
```

```python
import nb_log
import time
from nb_filelock import FileLock

print('wait filelock')
with FileLock('testx.lock'):
    print('hi')
    time.sleep(20)
    print('hello')
```

### 实现代码
```python
import os
import abc

if os.name == 'nt':
    import win32con, win32file, pywintypes

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
    def __enter__(self):
        hfile = win32file._get_osfhandle(self.f.fileno())
        win32file.LockFileEx(hfile, LOCK_EX, 0, 0xffff0000, _overlapped)

    def __exit__(self, exc_type, exc_val, exc_tb):
        hfile = win32file._get_osfhandle(self.f.fileno())
        win32file.UnlockFileEx(hfile, 0, 0xffff0000, _overlapped)


class LinuxFileLock(BaseLock):
    def __enter__(self):
        fcntl.flock(self.f, fcntl.LOCK_EX)

    def __exit__(self, exc_type, exc_val, exc_tb):
        fcntl.flock(self.f, fcntl.LOCK_UN)


FileLock = WindwosFileLock if os.name == 'nt' else LinuxFileLock

if __name__ == '__main__':
    """ 把这个脚本连续反复启动多个可以测试文件锁，只有获得文件锁，代码块才能执行"""
    import nb_log
    import time

    print('等待获得锁')
    with FileLock('testx.lock'):
        print('hi')
        time.sleep(20)
        print('hello')
    

```




多个脚本都写入一个txt文件可以这样。
```
with FileLock('D:/testx.lock'):
    with open("yourtxt.txt") as f:
           f.write("xxxx")
```
