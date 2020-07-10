#!/usr/bin/env python

import pathlib
from setuptools import find_packages, setup

VERSION = "0.0.1"

REPO_ROOT = pathlib.Path(__file__).parent

with open(REPO_ROOT / "README.md", encoding="utf-8") as f:
    README = f.read()

REQUIREMENTS = ["distributed", "requests", "typing-extensions"]

EXTRAS = {
    "runner": ["fastapi", "uvicorn"],
    "deployment": ["kubernetes-asyncio==10.*,>=10.0.0"],
}


setup_args = dict(
    # Description
    name="dask-remote",
    version=VERSION,
    description="Dask cluster based on a Kubernetes-native Deployment.",
    long_description=README,
    long_description_content_type="text/markdown",
    # Credentials
    license="MIT",
    author="Octopus Energy",
    author_email="tech@octopus.energy",
    url="https://github.com/octoenergy/dask-remote",
    # Package data
    package_dir={"": "src"},
    packages=find_packages("src", exclude=["*tests*"]),
    # Dependencies
    platforms=["Any"],
    python_requires="==3.*,>=3.7.0",
    install_requires=REQUIREMENTS,
    extras_require=EXTRAS,
)


if __name__ == "__main__":

    # Make install
    setup(**setup_args)
