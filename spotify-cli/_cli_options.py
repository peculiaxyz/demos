"""Helper module that uses built-in argparse library to extract command line options and save them in a custom object
"""

__author__ = 'N Nemakhavhani'
__all__ = ['CommandLineOptions', 'CLIOptionsReader']

import argparse

_parser = argparse.ArgumentParser(description='Interact with the Spotify Web API via the command line')


# parser.add_argument('-c', '--config', dest='config', type=str, required=True,
#                     help='Specify the full windows path of the xml configuration file')
# parser.add_argument('-l', '--log', dest='logdir', required=True, help='Root directory for log file')


class CommandLineOptions:
    def __init__(self, namespace_obj):
        self._config_file = namespace_obj.config
        self._log_dir = namespace_obj.logdir

    @property
    def log_dir(self):
        return self._log_dir

    @property
    def config_file(self):
        return self._config_file

    def __str__(self):
        result = "Captured Command Line Options:\n"
        result += f"Config file location: {self._config_file}\n"
        result += f"Log-files root: {self._log_dir}"
        return result.strip()


class CLIOptionsReader:
    def __init__(self):
        self.CLIOptions = None

    def execute(self) -> CommandLineOptions:
        self.CLIOptions = CommandLineOptions(_parser.parse_args())
        return self.CLIOptions
