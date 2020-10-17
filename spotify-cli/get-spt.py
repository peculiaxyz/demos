""""
1. Installs spt module using pip
2. Download the spt executable from git and add it to the python 3 scripts directory
3. Prints the version of the installed spt program to the console
"""
import os
import pathlib
import shutil
import sys
from datetime import datetime

PYTHON3_EXE_PATH = sys.executable
PYTHON3_HOME = pathlib.Path(PYTHON3_EXE_PATH).parent
INSTALL_SPT_CMD = "pip install -i https://test.pypi.org/simple/ spt --upgrade"
SPT_BIN_DOWNLOAD_URL = "https://peculiapublicstorage.blob.core.windows.net/peculia-bins/spt.exe"
SPT_BIN_DOWNLOAD_URL_POSIX = ""  # TODO


class GetSptError(Exception):
    pass


def _run_test_command():
    test_cmd = f"{PYTHON3_EXE_PATH} -m pip --version"
    exit_code = os.system(test_cmd)
    if exit_code:
        error = f'Problems encountered while executing the test command: {test_cmd}\n'
        error += "Please ensure that you have installed Python3.8.x and added it to your PATH"
        raise GetSptError(error)


def _check_for_pip_updates():
    print("Checking for pip updates\n")
    pip_update_cmd = f"{PYTHON3_EXE_PATH} -m pip install pip --upgrade"
    exit_code = os.system(pip_update_cmd)
    if exit_code:
        error = f'Unknown problems encountered while executing command: {pip_update_cmd}\n'
        raise GetSptError(error)
    print("Pip update done.\n")


def _install_or_update_spt_from_pip():
    print(f"=========Executing {_install_or_update_spt_from_pip.__name__}=============\n")
    cmd = f"{PYTHON3_EXE_PATH} -m {INSTALL_SPT_CMD}"
    exit_code = os.system(cmd)
    if exit_code:
        error = f'Problems encountered while executing the command: {cmd}\n'
        error += "Please ensure that the package name exists on PYPI"
        raise GetSptError(error)
    print("Spt module successfully installed.\n")


def _download_spt_exe():
    import urllib.request as req
    print(f"===== Downloading spt binary from {SPT_BIN_DOWNLOAD_URL} =======")
    if os.name == 'nt':
        download_location = os.path.join(os.getenv('LOCALAPPDATA'), 'Temp', f'spt_temp_{os.getpid()}.exe')

        start_time = datetime.now()
        print(f'Begin download...{start_time}')
        req.urlretrieve(SPT_BIN_DOWNLOAD_URL, filename=download_location)
        elapsed_seconds = (datetime.now() - start_time).total_seconds()
        print(f"Download completed in {elapsed_seconds} seconds")

        print(f"Spt binary successfully downloaded to {download_location}")
        return download_location
    raise NotImplementedError('Support for Posix coming soon..')


def _copy_bin_to_python_scripts_path(src: str):
    if not os.path.exists(src):
        raise FileNotFoundError(src)

    destination = os.path.join(PYTHON3_HOME, 'spt.exe') if pathlib.Path(PYTHON3_HOME).name.lower() == "scripts" else \
        os.path.join(PYTHON3_HOME, 'Scripts', 'spt.exe')

    destination = shutil.move(src, destination)
    print(f"Spt bin successfully copied from {src} to {destination}")


def main():
    _run_test_command()
    _check_for_pip_updates()
    _install_or_update_spt_from_pip()
    download_location = _download_spt_exe()
    _copy_bin_to_python_scripts_path(download_location)


if __name__ == '__main__':
    main()
    # print(PYTHON3_HOME)
