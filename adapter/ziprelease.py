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

# Get the version and latest tag from git
describe = subprocess.check_output(shlex.split(
    'git describe',
)).strip()
print('Currently at {}'.format(describe))
lasttag = describe.split('-')[0]

# checkout latest tag
print('Trying to checkout tag {}'.format(lasttag))
status = subprocess.call(shlex.split('git checkout {}'.format(lasttag)))
if status:
    exit()

# Determine paths
basedir = subprocess.check_output(shlex.split(
    'git rev-parse --show-toplevel',
)).strip()
adapterdir = os.path.join(basedir, 'adapter')
archivepath = os.path.join(basedir, 'adapter-{}.zip'.format(lasttag))
versionpath = os.path.join(adapterdir, 'version.txt')

# Create versionfile
with open(versionpath, 'w') as versionfile:
    versionfile.write('# version {}\n'.format(lasttag))

# Create the zipfile
with zipfile.ZipFile(archivepath, 'w', zipfile.ZIP_DEFLATED) as archivefile:
    for path, dirnames, filenames in os.walk(adapterdir):
        for filename in filenames:
            if filename.endswith('.pyc'):
                continue
            archivefile.write(
                os.path.join(path, filename),
                os.path.join('adapter', filename),
            )

# Remove versionfile and checkout master
os.remove(versionpath)
subprocess.call(shlex.split('git checkout master')).strip()
