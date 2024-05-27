
from portalocker import Lock
from functools import partial
FileLock = partial(Lock,timeout=600,fail_when_locked=False,check_interval=0.1)

# noinspection PyUnresolvedReferences,PyUnresolvedReferences
if __name__ == '__main__':
    """ 把这个脚本连续反复启动多个可以测试文件锁，只有获得文件锁，代码块才能执行"""
    import nb_log
    import time
    import pathlib
    print('wait for lock')
    with FileLock(pathlib.Path(__file__).parent / pathlib.Path('testx.lock')):
        print('hi')
        time.sleep(20)
        print('hello')
