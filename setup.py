#!/usr/bin/python
from setuptools import setup, find_packages

# Import the module version
from powerconsul import __version__

# Run the setup
setup(
    name             = 'powerconsul',
    version          = __version__,
    description      = 'Service watcher and event triggers',
    long_description = open('DESCRIPTION.rst').read(),
    author           = 'David Taylor',
    author_email     = 'david.j.taylor@powerhrg.com',
    url              = 'http://github.com/powerhome/python-powerconsul',
    license          = 'GPLv3',
    install_requires = ['python-consul', 'termcolor', 'six'],
    packages         = find_packages(),
    entry_points     = {
        'console_scripts': [
            'powerconsul = powerconsul.__main__:main'
        ]
    },
    keywords         = 'ha infrastructure shell service consul',
    classifiers      = [
        'Development Status :: 3 - Alpha',
        'Environment :: Console',
        'License :: OSI Approved :: GNU General Public License v3 or later (GPLv3+)',
        'Natural Language :: English',
        'Operating System :: POSIX',
        'Programming Language :: Python',
        'Topic :: Terminals',
    ]
)
