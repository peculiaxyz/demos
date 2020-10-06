"""Read the command line options and map the map the selected subcommand to the appropriate worker class"""

import abc
import argparse
import sys
import traceback
from typing import Type

import _shared_mod

# Top-level/Parent parser
parser = argparse.ArgumentParser(prog='Interact with the Spotify Web API via the command line')
subparsers = parser.add_subparsers(help='Typical usage: spt <subcommand> [subcomand options]')

# [Spotify] Library API subparser
library_parser = subparsers.add_parser('library', help='Get current users saved tracks, shows, albums etc.'
                                                       'Example: spt library GetSavedAlbums')
library_parser.add_argument('--limit', '-l', default=30, dest='limit', type=int,
                            help='Maximum no. of results per query')

# [Spotify] Personalisation API subparser
personalisation_parser = subparsers.add_parser('personalise', help='Get the current user’s top artists or tracks ')
personalisation_parser.add_argument('--baz', choices='XYZ', help='baz help')


# region Command handlers

class CommandHandler(abc.ABC):
    def __init__(self, context_object):
        self._Context = context_object

    @abc.abstractmethod
    def handle(self):
        pass


class LoginCommandHandler(CommandHandler):
    def handle(self):
        print('Authorization flow intialised')


class LibraryCommandHandler(CommandHandler):
    def handle(self):
        print('Library API handler intialised')


class PersonalisationCommandHandler(CommandHandler):
    def handle(self):
        print('Personalisation API handler intialised')


# endregion


class CommandDispatcher:
    def __init__(self, parser_obj: argparse.ArgumentParser):
        self._parser = parser_obj
        self._command_handler_map = {
            'login': LoginCommandHandler,
            'library': LibraryCommandHandler,
            'personalise': PersonalisationCommandHandler
        }

    def _retrive_subcommand(self):
        print('Retrieving selected command from the arguments: ', sys.argv)
        selected_command = str(sys.argv[1]).strip().lower()
        if selected_command not in self._command_handler_map.keys():
            raise _shared_mod.InvalidCommandError(f'Invalid or unsurpoted command | {selected_command} |')
        return selected_command

    def _retrive_command_handler(self, command: str) -> Type[CommandHandler]:
        handler_cls = self._command_handler_map.get(command)
        if not issubclass(handler_cls, CommandHandler):
            raise _shared_mod.InvalidCommandHandlerError(f'Handler must be a subclass of {CommandHandler.__name__}')
        return handler_cls

    def execute(self):
        selected_command = self._retrive_subcommand()
        command_handler = self._retrive_command_handler(selected_command)
        handler_context = self._parser.parse_args()
        handlder_obj = command_handler(handler_context)
        handlder_obj.handle()


def main():
    try:
        print('Initialise spt CLI..')
        cmd_dispatcher = CommandDispatcher(parser_obj=parser)
        cmd_dispatcher.execute()
    except _shared_mod.InvalidCommandError:
        print(traceback.format_exc())
        parser.print_help()
    except Exception as e:
        print('A critical error had occured. The app will now close...')
        print(e)
        print(traceback.format_exc())


if __name__ == '__main__':
    main()
