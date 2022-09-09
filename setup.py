from setuptools import setup, find_packages

__version__ = "0.6.1"
__author__ = "DavidCEllis"


setup(
    name="splitguides",
    version=__version__,
    packages=find_packages("src"),
    url="",
    license="GPLv3",
    description="Speedrun notes tool for advancing notes automatically with Livesplit.",
    python_requires=">=3.9",
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Operating System :: Microsoft :: Windows",
        "Programming Language :: Python",
        "Programming Language :: Python :: 3.9",
    ],
    package_dir={"": "src"},
    install_requires=[
        "pyside2",
        "jinja2",
        "bleach[css]",
        "flask",
        "attrs",
        "markdown",
        "keyboard",
    ],
    tests_require=["pytest", "pytest-cov", "pytest-qt"],
    extras_require={"build_exe": ["cx-freeze", "pywin32"], "dev": ["black"]},
)
