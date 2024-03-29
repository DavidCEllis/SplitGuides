from setuptools import setup, find_packages

__version__ = "0.8.0"
__author__ = "DavidCEllis"


test_requirements = ["pytest", "pytest-cov", "pytest-qt"]


setup(
    name="splitguides",
    version=__version__,
    packages=find_packages("src"),
    url="",
    license="GPLv3",
    description="Speedrun notes tool for advancing notes automatically with Livesplit.",
    python_requires=">=3.11",
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Operating System :: Microsoft :: Windows",
        "Programming Language :: Python",
        "Programming Language :: Python :: 3.11",
    ],
    package_dir={"": "src"},
    install_requires=[
        "pyside6",
        "jinja2",
        "bleach[css]==6.0",  # Each upgrade to bleach has broken something so pin it.
        "flask",
        "markdown",
        "keyboard",
        "prefab-classes",
        "waitress",
    ],
    tests_require=test_requirements,
    extras_require={
        "build_exe": ["cx-freeze", "pywin32"],
        "dev": ["black"],
        "tests": test_requirements,
    },
)
