import setuptools

with open("README.md", "r") as fh:
    long_description = fh.read()

setuptools.setup(
    name="pybmr",
    version="0.5",
    author="Honza Slesinger",
    author_email="slesinger@gmail.com",
    description="Python library for communication with BMR HC64 Heating Controller units",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/slesinger/pybmr",
    packages=setuptools.find_packages(),
    install_requires=[
          'requests'
    ],
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
)