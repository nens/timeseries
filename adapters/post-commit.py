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

versionpath = os.path.join(basedir, 'adapters', 'version.txt')

with open(versionpath, 'w') as versionfile:
    versionfile.write('# {}: {}\n'.format(VERSION, version))
