import os
import random
import string
from datetime import datetime


def get_random_str():
    return ''.join(map(lambda xx:(hex(ord(xx))[2:]),os.urandom(8)))


def gen_password():
    chars = string.ascii_letters + string.digits + '!@#$%^&*()'
    random.seed = (os.urandom(1024))
    return ''.join(random.choice(chars) for i in range(16))


def exe_time(func):
    def newFunc(*args, **args2):
        start = datetime.now()
        back = func(*args, **args2)
        print ('Elapsed: ' + str(datetime.now() - start))
        return back
    return newFunc
