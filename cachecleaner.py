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


def update_bar(bar, n):
    bar.update(min(bar.total, n + bar.n) - bar.n)


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


def clean_cache(workdir, capacity, quiet=False, time_type='st_atime', dry_run=False):
    workdir = os.path.realpath(workdir) + os.sep

    files, total_size = listdir(workdir, quiet, time_type)

    if total_size <= capacity:
        if not quiet:
            print('No files to delete!')
        return []

    with section('Sorting files', quiet) as write:
        files.sort()

        oldest = datetime.utcnow() - datetime.utcfromtimestamp(files[0][0])
        write('oldest file: {}'.format(oldest))

    with section('Deleting files', quiet) as write:
        skipped = deleted = deleted_size = 0
        with tqdm(total=total_size - capacity, disable=quiet,
                  bar_format=BAR_FORMAT, unit='b',
                  unit_scale=True, unit_divisor=1024) as bar:
            for file_time, size, file_name in files:
                if total_size - deleted_size <= capacity:
                    break

                file_name = workdir + file_name
                try:
                    stats = os.stat(file_name)
                    if getattr(stats, time_type) > file_time:
                        skipped += 1
                        continue
                    if not dry_run:
                        os.remove(file_name)
                except OSError:
                    skipped += 1
                    continue

                update_bar(bar, size)
                deleted_size += size
                deleted += 1

        oldest = datetime.utcnow() - datetime.utcfromtimestamp(file_time)
        write('oldest file: {}'.format(oldest))
        write('deleted: {} files, {:0.1f} mb'.format(
            deleted, deleted_size / MEGABYTE,
        ))
        write('skipped: {} files'.format(skipped))

    return files


def clean_forever(sleep_for, kwargs):
    while True:
        try:
            clean_cache(**kwargs)
        except Exception as e:
            print('Failed with exception:', e)

        if not kwargs['quiet']:
            print(f'Sleep for {sleep_for} seconds')
            print(flush=True)
        time.sleep(sleep_for)


def main():
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
    parser.add_argument('-d', '--dry-run', dest='dry_run', action='store_true',
                        default=False, help='do not delete anything')
    parser.add_argument('-s', '--sleep', dest='sleep_for', type=float,
                        default=None, help='run in endless mode with sleep '
                        'seconds between runs')

    kwargs = vars(parser.parse_args())
    kwargs['capacity'] = int(kwargs['capacity'] * MEGABYTE)
    kwargs['time_type'] = 'st_' + kwargs['time_type']

    sleep_for = kwargs.pop('sleep_for')
    if sleep_for is None:
        clean_cache(**kwargs)
    else:
        clean_forever(sleep_for, kwargs)


if __name__ == '__main__':
    main()
