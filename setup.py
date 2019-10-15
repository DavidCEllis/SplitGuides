from setuptools import setup, find_packages

__version__ = '0.0.2'
__author__ = 'DavidCEllis'


setup(
    name='splitnotes2',
    version=__version__,

    packages=find_packages('src'),
    url='',
    license='GPLv2+',
    description='Quick tool for handling SEG-Y metadata and geometry.',
    python_requires='>=3.6',
    classifiers=[
        'Development Status :: 1 - Early Development',
        'Operating System :: Microsoft :: Windows',
        'Programming Language :: Python',
        'Programming Language :: Python :: 3.7',
    ],
    package_dir={"": "src"},
    install_requires=[
        'pyside2',
        'jinja2',
    ],
    tests_require=[
        'pytest',
        'pytest-cov',
    ]
)
