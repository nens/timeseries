#!/usr/bin/python
import os
import shlex
import shutil
import subprocess
import tempfile

VERSION = 'version'

basedir = subprocess.check_output(shlex.split(
    'git rev-parse --show-toplevel',
)).strip()
version = subprocess.check_output(shlex.split(
    'git describe',
)).strip()
scriptpath = os.path.join(basedir, 'timeseries', 'statistics.py')
dummypath = tempfile.mkstemp()[1]

scriptfile = open(scriptpath)
dummyfile = open(dummypath, 'w')

for lineno, line in enumerate(scriptfile):
    if lineno == 3:
        dummyfile.write('# {}: {}\n'.format(VERSION, version))
        if VERSION in line:
            continue
    dummyfile.write(line)

scriptfile.close()
dummyfile.close()
shutil.move(dummypath, scriptpath)
