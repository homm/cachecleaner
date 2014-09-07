from __future__ import division, print_function

import os
import time
from tqdm import tqdm
from contextlib import contextmanager


MEGABYTE = 2 ** 20


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


def listdir(workdir, quiet=False, time_type='st_atime'):
    workdir = os.path.realpath(workdir) + os.sep

    with section('Reading files list', quiet):
        files = os.listdir(workdir)

    if not quiet:
        print('    {} files'.format(len(files)))
        files = tqdm(files, mininterval=.1)

    with section('Reading files stats', quiet):
        files_with_stats = []
        for f in files:
            try:
                stats = os.stat(workdir + f)
            except OSError:
                continue
            files_with_stats.append(
                (getattr(stats, time_type), stats.st_size, f)
            )

    return files_with_stats


def clean_cache(workdir, capacity, quiet=False, time_type='st_atime'):
    workdir = os.path.realpath(workdir) + os.sep

    files = listdir(workdir, quiet, time_type)

    total_size = sum(stats[1] for stats in files)

    if not quiet:
        print('    total size: {:0.1f} mb'.format(total_size / MEGABYTE))

    if total_size <= capacity:
        if not quiet:
            print('    no files to delete')
        return []

    with section('Sorting files', quiet):
        files.sort(reverse=True)

        total_size = 0
        for i, (_, size, _) in enumerate(files):
            total_size += size
            if total_size > capacity:
                break
        files = files[i:]

    if quiet:
        filesiter = files
    else:
        print('    to delete: {} files, {:0.1f} mb'.format(
            len(files),
            sum(stats[1] for stats in files) / MEGABYTE,
        ))
        filesiter = tqdm(files, mininterval=.1)

    with section('Deleting files', quiet):
        for _, _, f in filesiter:
            try:
                os.remove(workdir + f)
            except OSError:
                continue

    return files


if __name__ == '__main__':
    from argparse import ArgumentParser

    parser = ArgumentParser(description='Keeps dir size in given capacity.')
    parser.add_argument('capacity', type=float,
                        help='cache capacity, megabytes')
    parser.add_argument('workdir', help='where is cache dir')
    parser.add_argument('-t', '--type', choices=['atime', 'ctime', 'mtime'],
                        dest='time_type', default='atime',
                        help='time attribute type')
    parser.add_argument('-q', '--quiet', dest='quiet', action='store_true',
                        default=False, help='do not output in console')

    kwargs = vars(parser.parse_args())
    kwargs['capacity'] *= MEGABYTE
    kwargs['time_type'] = 'st_' + kwargs['time_type']
    clean_cache(**kwargs)
