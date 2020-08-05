import setuptools

with open("README.md", "r") as fh:
    long_description = fh.read()

setuptools.setup(
    name="dim-editor",
    version="1.0.0",
    author="Leyang Zou",
    description="A simple terminal text editor based on Vim",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/BattleMage0231/dim",
    packages=setuptools.find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires='>=3.8',
)