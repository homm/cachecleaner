from __future__ import division, print_function

import os
import time
from tqdm import tqdm
from contextlib import contextmanager
from datetime import datetime


MEGABYTE = 2 ** 20
BAR_FORMAT = '    {l_bar}{bar}{r_bar}'


@contextmanager
def section(caption, quiet=False):
    def write(s):
        if not quiet:
            print('    ' + s)

    if not quiet:
        print(caption + '...')
        start = time.time()
    yield write
    write('took {:0.2f} sec'.format(time.time() - start))
    write('')


def listdir(workdir, quiet=False, time_type='st_atime'):
    workdir = os.path.realpath(workdir) + os.sep

    with section('Reading files list', quiet) as write:
        files = os.listdir(workdir)
        write('total {} files in cache'.format(len(files)))

    files_with_stats = []
    total_size = 0
    with section('Reading files stats', quiet) as write:
        for f in tqdm(files, disable=quiet, bar_format=BAR_FORMAT):
            try:
                stats = os.stat(workdir + f)
            except OSError:
                continue
            total_size += stats.st_size
            files_with_stats.append(
                (getattr(stats, time_type), stats.st_size, f)
            )
        write('total size: {:0.1f} mb'.format(total_size / MEGABYTE))

    return files_with_stats, total_size


def clean_cache(workdir, capacity, quiet=False, time_type='st_atime'):
    workdir = os.path.realpath(workdir) + os.sep

    files, total_size = listdir(workdir, quiet, time_type)

    if total_size <= capacity:
        if not quiet:
            print('No files to delete!')
        return []

    with section('Sorting files', quiet) as write:
        files.sort(reverse=True)

        oldest = datetime.utcnow() - datetime.utcfromtimestamp(files[-1][0])
        write('oldest file: {}'.format(oldest))

        total_size = 0
        for i, (_, size, _) in enumerate(files):
            total_size += size
            if total_size > capacity:
                break
        files = files[i:]

        lifetime = datetime.utcnow() - datetime.utcfromtimestamp(files[0][0])
        write('cache lifetime: {}'.format(lifetime))

    with section('Deleting files', quiet) as write:
        for _, _, f in tqdm(files, disable=quiet, bar_format=BAR_FORMAT):
            try:
                os.remove(workdir + f)
            except OSError:
                continue
        write('deleted: {} files, {:0.1f} mb'.format(
            len(files),
            sum(stats[1] for stats in files) / MEGABYTE,
        ))

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
