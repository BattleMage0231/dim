import setuptools
import sys

with open("README.md", "r") as fh:
    long_description = fh.read()

setuptools.setup(
    name="dim-editor",
    version="1.0.1",
    author="Leyang Zou",
    description="A simple terminal text editor based on Vim",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/BattleMage0231/dim",
    packages=["dim"],
    package_data={"dim": ["debug/*", "tutorial/*"]},
    include_package_data=True,
    python_requires='>=3.8',
    entry_points={
        "console_scripts": [
            "dim = dim.dim:launch",
        ],
    },
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    extras_require={
        ':sys_platform == "win32"': [
            'windows-curses'
        ],
    },
)