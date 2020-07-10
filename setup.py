import setuptools

with open("README.md", "r") as fh:
    long_description = fh.read()

with open("requirements.txt") as fh:
    install_requires = [line for line in fh if line and line[0] not in "#-"]

with open("test-requirements.txt") as fh:
    tests_require = [line for line in fh if line and line[0] not in "#-"]

setuptools.setup(
    name="pybmr",
    version="0.7",
    author="Honza Slesinger",
    author_email="slesinger@gmail.com",
    description="Python library for communication with BMR HC64 Heating Controller units",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/slesinger/pybmr",
    packages=setuptools.find_packages(),
    install_requires=install_requires,
    tests_require=tests_require,
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: Apache Software License",
        "Operating System :: OS Independent",
    ],
)
