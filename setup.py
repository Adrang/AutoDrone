"""
https://packaging.python.org/tutorials/packaging-projects/
"""

import setuptools

from auto_drone import version, name

with open('README.md', 'r') as desc_file:
    long_description = desc_file.read()

with open('requirements.txt', 'r') as req_file:
    requirements_list = req_file.readlines()

setuptools.setup(
    name=name,
    version=version,

    description='Interface for controlling a drone through a web-browser',
    ong_description=long_description,
    long_description_content_type='text/markdown',
    url='https://github.com/adrang/AutoDrone',

    author='Andrew Festa',
    author_email='andrew@andrewtfesta.com',

    packages=setuptools.find_packages(),

    python_requires='>=3.7',
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],

    install_requires=requirements_list,
    dependency_links=[],
)