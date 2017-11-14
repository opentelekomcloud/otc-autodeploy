import os

def get_random_str():
    return ''.join(map(lambda xx:(hex(ord(xx))[2:]),os.urandom(8)))
