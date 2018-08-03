import setuptools

with open("README.md", "r") as fh:
    long_description = fh.read()
    
setuptools.setup(
    name = "taxon_parser",
    version = "0.2.0",
    author = "Augustin Roche",
    author_email = "aroche@photoherbarium.fr",
    description = "A library to parse taxon names into elementary components",
    long_description = long_description,
    long_description_content_type = "text/markdown",
    url = "https://github.com/aroche/taxon_parser",
    packages = setuptools.find_packages(),
    package_data = {'': ('*/latin-endings.txt', )},
    python_requires = ">=3.4",
    install_requires = ("regex", ),
    classifiers = (
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: Apache Software License",
        "Operating System :: OS Independent",
    ),
)

