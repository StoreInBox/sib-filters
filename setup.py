#!/usr/bin/env python

from setuptools import setup, find_packages


dev_requires = []

tests_requires = []

install_requires = [
    'Django>=1.7,<1.9',
]

setup(
    name='sib-filters',
    version='0.1.0',
    author='zymud',
    author_email='zymud@i.ua',
    url='https://github.com/StoreInBox/sib-filters',
    description='Part of SIB project',
    long_description=open('README.rst').read(),
    packages=find_packages(exclude=["*.tests", "*.tests.*", "tests.*", "tests"]),
    install_requires=install_requires,
    extras_require={
        'dev': dev_requires,
        'tests': tests_requires,
    },
    # tests_require=tests_requires,
    # test_suite='nodeconductor.server.test_runner.run_tests',
    include_package_data=True,
    classifiers=[
        'Framework :: Django',
        'Intended Audience :: Developers',
        'Intended Audience :: System Administrators',
        'Operating System :: OS Independent',
    ],
)
