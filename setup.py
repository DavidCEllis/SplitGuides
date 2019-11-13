from setuptools import setup, find_packages

__version__ = "0.3.1"
__author__ = "DavidCEllis"


setup(
    name="splitnotes2",
    version=__version__,
    packages=find_packages("src"),
    url="",
    license="GPLv3",
    description="Quick tool for handling SEG-Y metadata and geometry.",
    python_requires=">=3.6",
    classifiers=[
        "Development Status :: 1 - Early Development",
        "Operating System :: Microsoft :: Windows",
        "Programming Language :: Python",
        "Programming Language :: Python :: 3.7",
    ],
    package_dir={"": "src"},
    install_requires=["pyside2", "jinja2", "bleach"],
    tests_require=["pytest", "pytest-cov", "pytest-qt"],
    extras_require={"build_exe": ["cx-freeze"], "dev": ["black"]},
)
