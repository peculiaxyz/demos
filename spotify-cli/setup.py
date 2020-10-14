import setuptools

with open("ReadMe.md", "r") as fh:
    long_description = fh.read()

setuptools.setup(
    name="spotifycli",
    version="0.0.1",
    author="Ndamulelo Nemakhavhani",
    author_email="ndamuspector@gmail.com",
    description="Interact with the Spotify Web API via the command line",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/peculiaxyz/demos",
    packages=setuptools.find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires='>=3.6',
)
