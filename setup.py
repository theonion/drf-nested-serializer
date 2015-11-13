#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
from setuptools import setup

# ---------------------------------------
# set this sucker!!

VERSION = '1.0.2'
# ---------------------------------------

name = "drf-nested-serializers"
package = "nested_serializers"
description = "America's Finest Namespace"
url = "https://github.com/theonion/drf-nested-serializers"
author = "Onion Devs"
author_email = "webtech@theonion.com"
license = "BSD"

requires = [
    "django>1.8,<1.9",
    "djangorestframework>=3.0,<4.0",
    "six",
]

dev_requires = [
    "model-mommy==1.2.4",
    "coveralls==0.5",
    "coverage==3.7.1"
]


def get_packages(package):
    """Return root package and all sub-packages.
    """
    return [dirpath
            for dirpath, dirnames, filenames in os.walk(package)
            if os.path.exists(os.path.join(dirpath, "__init__.py"))]


def get_package_data(package):
    """Return all files under the root package, that are not in a package themselves.
    """
    walk = [(dirpath.replace(package + os.sep, "", 1), filenames)
            for dirpath, dirnames, filenames in os.walk(package)
            if not os.path.exists(os.path.join(dirpath, "__init__.py"))]

    filepaths = []
    for base, filenames in walk:
        filepaths.extend([os.path.join(base, filename)
                          for filename in filenames])
    return {package: filepaths}


setup(
    name=name,
    version=VERSION,
    url=url,
    license=license,
    description=description,
    author=author,
    author_email=author_email,
    packages=get_packages(package),
    package_data=get_package_data(package),
    install_requires=requires,
    extras_require={
        'dev': dev_requires,
    },
    test_suite="example.runtests"
)
