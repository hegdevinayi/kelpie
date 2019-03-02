import os
import shutil
import datetime
from contextlib import contextmanager
from kelpie.utils.serialization import jsonable


@contextmanager
def change_working_dir(new_dir):
    current_dir = os.getcwd()
    os.chdir(new_dir)
    try:
        yield
    finally:
        os.chdir(current_dir)


def time_stamped_folder(base_name='archive'):
    now = datetime.datetime.now()
    return '_'.join([base_name, jsonable(now)])


def backup_files(list_of_files=None, folder_name='archive', gzip=True):
    if not list_of_files:
        list_of_files = ['POSCAR', 'INCAR', 'OSZICAR', 'OUTCAR', 'vasprun.xml']
    ts_folder = time_stamped_folder(base_name=folder_name)
    os.mkdir(ts_folder)
    for src_file in list_of_files:
        if not os.path.isfile(src_file):
            continue
        if gzip:
            dest_file = os.path.join(ts_folder, src_file+'.gz')
            with open(src_file, 'rb') as fsrc:
                with open(dest_file, 'wb') as fdest:
                    shutil.copyfileobj(fsrc, fdest)
        else:
            dest_file = os.path.join(ts_folder, src_file)
            shutil.copyfile(src_file, dest_file)


def copy_files(src_folder=None, dest_folder=None, list_of_filenames=None):
    if any([s is None for s in [src_folder, dest_folder, list_of_filenames]]):
        return
    for fn in list_of_filenames:
        src_file = os.path.join(src_folder, fn)
        dest_file = os.path.join(dest_folder, fn)
        shutil.copyfile(src_file, dest_file)

