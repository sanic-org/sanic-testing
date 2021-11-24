"""
Sanic
"""
import codecs
import os
import re

from setuptools import setup


def open_local(paths, mode="r", encoding="utf8"):
    path = os.path.join(os.path.abspath(os.path.dirname(__file__)), *paths)

    return codecs.open(path, mode, encoding)


with open_local(["sanic_testing", "__init__.py"], encoding="latin1") as fp:
    try:
        version = re.findall(
            r"^__version__ = \"([^']+)\"\r?$", fp.read(), re.M
        )[0]
    except IndexError:
        raise RuntimeError("Unable to determine version.")

with open_local(["README.md"]) as rm:
    long_description = rm.read()

setup_kwargs = {
    "name": "sanic-testing",
    "version": version,
    "url": "https://github.com/sanic-org/sanic-testing/",
    "license": "MIT",
    "author": "Adam Hopkins",
    "author_email": "admhpkns@gmail.com",
    "description": ("Core testing clients for Sanic"),
    "long_description": long_description,
    "long_description_content_type": "text/markdown",
    "packages": ["sanic_testing"],
    "platforms": "any",
    "classifiers": [
        "Development Status :: 3 - Alpha",
        "Environment :: Web Environment",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
    ],
}
requirements = [
    "httpx>=0.18,<0.22"
]

tests_require = [
    "pytest",
    "sanic>=21.3",
    "pytest-asyncio"
]

setup_kwargs["install_requires"] = requirements
setup_kwargs["tests_require"] = tests_require
setup(**setup_kwargs)
