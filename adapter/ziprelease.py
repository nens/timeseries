#!/usr/bin/python

from __future__ import print_function
from __future__ import unicode_literals
from __future__ import absolute_import
from __future__ import division

import os
import shlex
import shutil
import subprocess
import zipfile

BASEDIR = subprocess.check_output(shlex.split(
    'git rev-parse --show-toplevel',
)).strip()
ADAPTERDIR = os.path.join(BASEDIR, 'adapter')
VERSIONPATH = os.path.join(ADAPTERDIR, 'version.txt')


def get_last_tag():
    """ Return latest tag from git. """
    describe = subprocess.check_output(shlex.split(
        'git describe',
    )).strip()
    last_tag = describe.split('-')[0]
    return last_tag


def do(command):
    """ Do command via subprocess and return result. """
    return subprocess.call(shlex.split(command))


def checkout(tag=None):
    """ Checkout tag with git. """
    if tag is None:
        do('git checkout master')
        do('git stash pop')
    else:
        do('git stash save')
        return do('git checkout {}'.format(tag))
   

def create_version_file(versionpath, version):
    """ Create a versionfile at filepath. """
    with open(versionpath, 'w') as versionfile:
        versionfile.write('# version: {}\n'.format(version))


def create_zipfile(zippath, zipdir):
    """ Create a zipfile at zippath and add zipdir to it. """
    with zipfile.ZipFile(zippath, 'w', zipfile.ZIP_DEFLATED) as archivefile:
        for path, dirnames, filenames in os.walk(zipdir):
            for filename in filenames:
                if filename.endswith('.pyc'):
                    continue
                archivefile.write(
                    os.path.join(path, filename),
                    os.path.join(os.path.basename(zipdir), filename),
                )


def main(*args, **kwargs):
    last_tag = get_last_tag()
    zippath = os.path.join(BASEDIR, 'adapter-{}.zip'.format(last_tag))
    if checkout(last_tag) == 0:  # No errors
        create_version_file(versionpath=VERSIONPATH, version=last_tag)
        create_zipfile(zippath=zippath, zipdir=ADAPTERDIR)
        os.remove(VERSIONPATH)
    checkout()
