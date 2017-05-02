from distutils.core import setup

from setuptools import find_packages

setup(
    name='comicrock',
    version='0.5.0',
    packages=find_packages(exclude=['contrib', 'docs', 'tests']),
    url='https://github.com/ugurcan377/comicrock',
    license='GPLv3',
    author='Uğurcan Ergün',
    author_email='ugurcanergn@gmail.com',
    description='Comic downloader inspired by MangaRock',
    install_requires=['pillow', 'requests', 'click', 'beautifulsoup4', 'cfscrape'],
    entry_points={
        'console_scripts': [
            'comicrock=comicrock.cli:main',
        ],
    },
)
