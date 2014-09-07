from __future__ import division, print_function

import os
import time
from tqdm import tqdm
from contextlib import contextmanager


@contextmanager
def section(caption, quiet=False):
    if not quiet:
        print(caption + '...')
        start = time.time()
    yield
    if not quiet:
        print('\033[1F\033[{}C{:0.2f} sec'.format(
            len(caption) + 4,
            time.time() - start,
        ))


def clean_cache(workdir, capacity, quiet=False):
    workdir = os.path.realpath(workdir) + os.sep

    with section('Reading files list', quiet):
        files = os.listdir(workdir)

    if not quiet:
        print('    {} files'.format(len(files)))
        files = tqdm(files, mininterval=.1)

    with section('Reading files stats', quiet):
        files_with_stats = []
        for f in files:
            stats = os.stat(workdir + f)
            files_with_stats.append((stats.st_atime, stats.st_size, f))
        del files

    total_size = sum(stats[1] for stats in files_with_stats)

    if not quiet:
        print('    total size: {:0.1f} mb'.format(total_size / 1024 /1024))

    if total_size <= capacity:
        if not quiet:
            print('    no files to delete')
        return []

    with section('Sorting files', quiet):
        files_with_stats.sort(reverse=True)

        total_size = 0
        for i, (_, size, _) in enumerate(files_with_stats):
            total_size += size
            if total_size > capacity:
                break
        files_with_stats = files_with_stats[i:]

    if not quiet:
        print('    to delete: {} files, {:0.1f} mb'.format(
            len(files_with_stats),
            sum(stats[1] for stats in files_with_stats) / 1024 / 1024,
        ))
        files_with_stats = tqdm(files_with_stats, mininterval=.1)

    with section('Deleting files', quiet):
        for _, _, f in files_with_stats:
            os.remove(workdir + f)

    return files_with_stats


if __name__ == "__main__":
    from argparse import ArgumentParser

    parser = ArgumentParser(description='Keeps dir size in given capacity.')
    parser.add_argument("capacity", type=float,
                        help="cache capacity, megabytes")
    parser.add_argument("workdir", help="where is cache dir")
    parser.add_argument("-q", "--quiet", dest="quiet", action="store_true",
                        default=False, help="do not output in console")

    kwargs = vars(parser.parse_args())
    kwargs['capacity'] *= 2 ** 20
    clean_cache(**kwargs)
