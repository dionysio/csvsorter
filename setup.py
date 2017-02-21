import os
from distutils.core import setup

def read(filename):
    return open(os.path.join(os.path.dirname(__file__), filename)).read()

setup(
    name='csvsorter',
    version='1.4',
    packages=['csvsorter'],
    package_dir={'csvsorter' : '.'},
    author='Richard Penman, Dionyz Lazar',
    author_email='richard@webscraping.com, contact@dionysio.com',
    description='Sort large CSV files on disk rather than in memory',
    long_description=read('README.rst'),
    keywords=['csv', 'sort', 'large csv'],
    url='https://github.com/dionysio/csvsorter',
    download_url = 'https://github.com/dionysio/csvsorter/tarball/1.4',
    license='lgpl',
)
