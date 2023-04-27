import setuptools

with open("README.md", "r") as fh:
    long_description = fh.read()

setuptools.setup(
    name="emgwcave",
    version="0.0.0",
    author="Viraj Karambelkar",
    long_description=long_description,
    long_description_content_type="text/markdown",
    license="MIT",
    url="https://github.com/virajkaram/emgwcave",
    keywords="astronomy MMA vetting",
    packages=setuptools.find_packages(),
    classifiers=[
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
    ],
    python_requires='>=3.7',
    install_requires=[
        "pathlib",
        "pandas",
        "astropy",
        "penquins @ git+https://github.com/dmitryduev/penquins.git",
        "matplotlib",
        "requests",
        "typing",
        "snipergw @ git+https://github.com/robertdstein/snipergw.git"
    ],
    package_data={
    }
)