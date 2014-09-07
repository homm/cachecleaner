import os
from random import random
from tqdm import tqdm
from time import time

mtime = time()

for i in tqdm(range(100000)):
    name = 'test/file%08d' % i
    content = "1234567890" * int(random() * 1000)
    atime = mtime - random() * 1000000

    with open(name, 'w') as f:
        f.write(content)
    os.utime(name, (atime, mtime))
