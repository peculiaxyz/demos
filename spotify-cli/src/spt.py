__all__ = ['main']
__author__ = 'N Nemakhavhani'
__version__ = '1.0.0'
__licencse__ = 'MIT'

import argparse
import sys
import traceback
import typing

import _app_config
import _cli_parser as cli
import _shared_mod
import dotenv
from _logger import default_logger as log


class CommandDispatcher:
    def __init__(self, parser_obj: argparse.ArgumentParser):
        self._parser = parser_obj
        self._command_handler_map = {
            'login': cli.LoginCommandHandler,
            'library': cli.LibraryCommandHandler,
            'personalise': cli.PersonalisationCommandHandler
        }

    def _extract_subcommand_from_stdin(self):
        log.debug('Extracting command to execute from STDIN: ', sys.argv)
        subcommand = str(sys.argv[1]).strip().lower()
        if subcommand not in self._command_handler_map.keys():
            raise _shared_mod.InvalidCommandError(f'Invalid or unsurpoted command | {subcommand} |')
        return subcommand

    def _get_command_handler(self, command: str) -> typing.Type[cli.CommandHandler]:
        handler_class = self._command_handler_map.get(command)
        if not issubclass(handler_class, cli.CommandHandler):
            raise _shared_mod.InvalidCommandHandlerError(f'Handler must be a subclass of {cli.CommandHandler.__name__}')
        log.debug(f'Found handler {handler_class.__name__} for  command {command}')
        return handler_class

    def execute(self):
        log.debug('Executing CommandDispatcher')
        selected_command = self._extract_subcommand_from_stdin()
        command_handler = self._get_command_handler(selected_command)
        handler_context = self._parser.parse_args()
        handlder_obj = command_handler(handler_context)
        handlder_obj.execute()


class BootStrapper:
    @staticmethod
    def execute():
        log.debug('Executing BootStrapper')
        dotenv.load_dotenv()
        log.debug(' > Enviroment variables loaded')

        _app_config.GlobalConfiguration.initialise()
        log.debug(' > Global configuration loaded')


def main():
    try:
        log.info('Spotify CLI. @Copyright 2020')
        BootStrapper.execute()
        cmd_dispatcher = CommandDispatcher(parser_obj=cli.main_cli_parser)
        cmd_dispatcher.execute()
    except _shared_mod.InvalidCommandError:
        log.debug(traceback.format_exc())
        cli.main_cli_parser.print_help()
    except Exception as ex:
        log.debug(traceback.format_exc())
        log.error(f'A critical error has occured. {ex}.\nThe app will now close.')


if __name__ == '__main__':
    main()
