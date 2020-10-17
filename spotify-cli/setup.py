import setuptools


class PostInstallTasks:
    @staticmethod
    def execute():
        with open('C:\\postinstall.txt', 'w') as f:
            f.write('Random things')
        print('TESTING: I AM A POST INSTALL SCRIPT')


with open("README.md", "r") as fh:
    long_description = fh.read()

setuptools.setup(
    name="spt",
    version="1.1.0",
    author="Ndamulelo Nemakhavhani",
    author_email="ndamuspector@gmail.com",
    description="Interact with the Spotify Web API via the command line",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/peculiaxyz/demos",
    packages=setuptools.find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: GNU General Public License v3 (GPLv3)",
        "Operating System :: OS Independent",
    ],
    python_requires='>=3.6',
    data_files=[
        ("config", ["spt/config/sptconfig.ini"])
    ]
)

# Setup program data folders,config etc.
PostInstallTasks().execute()
