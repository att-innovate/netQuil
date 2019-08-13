import setuptools

with open("README.md", "r") as fh:
    long_description = fh.read()

setuptools.setup(
    name="netQuil",
        version = "1.0.0",
    author="Zac Espinosa, Matt Radzihovsky",
    author_email="zespinosa97@gmail.com, mattradz@stanford.edu",
    description="A Distributed Quantum Network Simulator",
    license="MIT",
    long_description="NetQuil is an open-source Python framework built on pyQuil designed specifically for simulating quantum networks.",
    long_description_content_type="text/markdown",
    url="https://github.com/att-innovate/netQuil",
    packages=setuptools.find_packages(),
    classifiers=(
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ),
    install_requires=[
        "numpy",
        "pyquil"
    ],
)
