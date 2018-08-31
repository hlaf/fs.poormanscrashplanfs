import codecs
import os
import re
from setuptools import setup, find_packages


def get_absolute_path(*args):
    """Transform relative pathnames into absolute pathnames."""
    return os.path.join(os.path.dirname(os.path.abspath(__file__)), *args)


def get_contents(*args):
    """Get the contents of a file relative to the source distribution directory."""
    with codecs.open(get_absolute_path(*args), 'r', 'UTF-8') as handle:
        return handle.read()


def get_version(*args):
    """Extract the version number from a Python module."""
    contents = get_contents(*args)
    metadata = dict(re.findall('__([a-z]+)__ = [\'"]([^\'"]+)', contents))
    return metadata['version']


def get_requirements(*args):
    """Get requirements from pip requirement files."""
    requirements = set()
    with open(get_absolute_path(*args)) as handle:
        for line in handle:
            # Strip comments.
            line = re.sub(r'^#.*|\s#.*', '', line)
            # Ignore empty lines
            if line and not line.isspace():
                requirements.add(re.sub(r'\s+', '', line))
    return sorted(requirements)

setup(
    name='fs-poormanscrashplanfs',
    author='Henrique Lindgren',
    author_email='henrique.lindgren@gmail.com',
    description='CrashPlan filesystem for PyFilesystem2',
    install_requires=get_requirements('requirements.txt'),
    license='MIT',
    packages=find_packages('src'),
    keywords=['pyfilesystem', 'CrashPlan'],
    platforms=['any'],
    url='https://github.com/hlaf/fs.poormanscrashplanfs',
    version=get_version('src', 'fs_crashplanfs', '__init__.py'),
    package_dir={'':'src'},   # tell distutils packages are under src
    entry_points={
        "fs.opener": [
            "crashplanfs = fs_crashplanfs.opener:CrashPlanFSOpener",
        ],
    },
)