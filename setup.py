from setuptools import setup, find_packages
from intra_search.config import SHORT_DESC


def read_requirements(file):
    with open(file) as f:
        return f.read().splitlines()


def read_file(file):
    with open(file) as f:
        return f.read()


requirements = read_requirements("./requirements.txt")
long_description = read_file("README.md")

setup(
    name="intra-search",
    version="0.1.0",
    author="Monish Prabhu",
    author_email="monish.prabhu.official@gmail.com",
    url="https://github.com/monish-prabhu/Intra-Search",
    description=SHORT_DESC,
    long_description_content_type="text/markdown",
    long_description=long_description,
    license="MIT License",
    packages=find_packages(),
    install_requires=requirements,
    python_requires=">=3.8",
    keywords=["semantic search", "document search", "sentence transformers", "nlp", "text analysis"],
    project_urls={
        "Bug Reports": "https://github.com/monish-prabhu/Intra-Search/issues",
        "Source": "https://github.com/monish-prabhu/Intra-Search",
    },
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "Intended Audience :: Science/Research",
        "Topic :: Scientific/Engineering :: Artificial Intelligence",
        "Topic :: Text Processing :: Linguistic",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Programming Language :: Python :: 3.13",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    entry_points={"console_scripts": ["intra-search = intra_search.cli:cli"]},
    package_data={
        "intra_search": ["../ui/dist/**/*"],
    },
)
