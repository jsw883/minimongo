"""
Setup module using setuptools (which is much better than distutils).

Created on Mar 11, 2016

@author: Williams, James S.
"""

from setuptools import setup, find_packages
from setuptools.command.install import install as InstallCommand
from setuptools.command.develop import develop as DevelopCommand
from setuptools.command.test import test as TestCommand

import sys

from imp import reload


# Custom post install function to manually load NLTK data dependency
def post_install_command():
    # Update PYTHONPATH
    import site
    reload(site)
    # Post install actions (anything requiring dependencies)


# Extend InstallCommand
class CustomInstallCommand(InstallCommand):
    def run(self):
        InstallCommand.run(self)
        self.execute(post_install_command, [],
                     msg="Running post_install_command()")


# Extend DevelopCommand.
class CustomDevelopCommand(DevelopCommand):
    def run(self):
        DevelopCommand.run(self)
        self.execute(post_install_command, [],
                     msg="Running post_install_command()")


# Extend TestCommand
class PyTestCommand(TestCommand):
    user_options = [('pytest-args=', None, "py.test arguments")]

    def initialize_options(self):
        TestCommand.initialize_options(self)
        self.pytest_args = []

    def run_tests(self):
        # Import inside, otherwise eggs aren't loaded
        import pytest
        errno = pytest.main(self.pytest_args)
        sys.exit(errno)

# Setup config
setup(
    # Package name, version, description, classifiers, and keywords
    name='minimongo',
    version='0.2.0',
    description='Lightweight ORM for MongoDB.',
    classifiers=[
        'Development Status :: 4 - Beta',
        'Intended Audience :: Developers',
        'Topic :: Scientific/Engineering',
        'Programming Language :: Python :: 3.5'
    ],
    keywords='repository mongo pymongo minimongo ORM',
    # Find packages, namespace specified by directory
    packages=find_packages(exclude=['scripts']),
    package_data={'': ['data/*', 'config/*']},
    install_requires=[
        'sphinx>=1.3.0',
        'pytest>=2.9.1',
        'colorama>=0.3.7',
        'log4mongo>=1.4.3',
        'pyyaml>=3.1.1',
        'inflection>=0.3.1',
        'pymongo>=3.0.3',
    ],
    cmdclass={
        'install': CustomInstallCommand,
        'develop': CustomDevelopCommand,
        'test': PyTestCommand,
    },
)
