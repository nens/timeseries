from setuptools import setup

version = 'y.dev0'

long_description = '\n\n'.join([
    open('README.rst').read(),
    open('TODO.rst').read(),
    open('CREDITS.rst').read(),
    open('CHANGES.rst').read(),
    ])

install_requires = [
    'pkginfo',
    'setuptools',
    'nens',
    ],

tests_require = [
    ]

setup(name='timeseries',
      version=version,
      description="Package to implement time series and generic operations on time series.",
      long_description=long_description,
      # Get strings from http://www.python.org/pypi?%3Aaction=list_classifiers
      classifiers=[],
      keywords=[],
      author='Pieter Swinkels',
      author_email='pieter.swinkels@nelen-schuurmans.nl',
      url='',
      license='GPL',
      packages=['timeseries'],
      include_package_data=True,
      zip_safe=False,
      install_requires=install_requires,
      tests_require=tests_require,
      extras_require = {'test': tests_require},
      entry_points={
          'console_scripts': [
              'ziprelease = adapter.ziprelease:main',
          ]},
      )
