"""Read the command line options and map the map the selected subcommand to the appropriate worker class"""

import abc
import argparse
import datetime
import sys
import traceback
from typing import Type

import dotenv

import _authorizer
import _shared_mod
import _spotify_api_collection as spotify

# region Parser Configuration

# Shared parser - stores shared options

common_fetch_parser = argparse.ArgumentParser(add_help=False)
common_fetch_parser.add_argument('--limit', '-l', default=30, dest='limit', help='The maximum number of objects to '
                                                                                 'return. Default: 20. Minimum: 1. '
                                                                                 'Maximum: 50')
common_fetch_parser.add_argument('--offset', '-o', default=0, dest='offset', help='Index of the first object to return')

# Top-level/Parent parser
parser = argparse.ArgumentParser(prog='Interact with the Spotify Web API via the command line')
subparsers = parser.add_subparsers(help='Typical usage: spt <subcommand> [subcomand options]')

# [Spotify] Authentication subparser
login_parser = subparsers.add_parser('login', help='Authenticate against Spotify Web API using OAuth')

# [Spotify] Library API subparser
library_parser = subparsers.add_parser('library', help='Get current users saved tracks, shows, albums etc.'
                                                       'Example: spt library GetSavedAlbums')
library_parser.add_argument('--limit', '-l', default=30, dest='limit', type=int,
                            help='Maximum no. of results per query')

# [Spotify] Personalisation API subparser
personalisation_parser = subparsers.add_parser('personalise', help='Get the current user’s top artists or tracks ')
personalize_subparsers = personalisation_parser.add_subparsers()

get_users_favourites_parser = personalize_subparsers.add_parser('GetTopArtists',
                                                                parents=[common_fetch_parser],
                                                                help="Example: spt personalise GetTopArtists")
get_users_favourites_parser.add_argument('--time', '-tr',
                                         dest='time_range',
                                         default='medium_term',
                                         choices=['long_term', 'medium_term', 'short_term'],
                                         help='Time range, i.e. medium term(6 months), short term(4 weeks)'
                                              ' or long term(several years)')


# endregion


# region Command handlers

class CommandHandler(abc.ABC):
    def __init__(self, context_object):
        self._Context = context_object

    @staticmethod
    def handle_missing_scopes_error(scopes):
        response = input('Would you like to request the required scopes? [Y or N]')
        if str(response) not in ('Y', 'y', 'yes'):
            return 0
        print('Initiating a request to get additional scopes: ', scopes)
        _authorizer.AuthorizerService.get_more_scopes(new_scopes=scopes)

    @abc.abstractmethod
    def handle(self):
        pass

    def execute(self):
        try:
            return self.handle()
        except _shared_mod.NotLoggedInError:
            print(traceback.format_exc())
        except _shared_mod.MissingScopesError as ex:
            print(traceback.format_exc())
            self.handle_missing_scopes_error(ex.scopes)
        except _shared_mod.SpotifyAPICallError:
            print(traceback.format_exc())
        except Exception as ex:
            print(f'[ {self.__name__} - execute encountered an unexpected error ]')
            print(ex)
            traceback.print_exc()


class LoginCommandHandler(CommandHandler):
    __SignInInprogress = False

    @staticmethod
    def on_auth_finished(has_error: bool):
        LoginCommandHandler.__SignInInprogress = False
        if has_error:
            print('Authorization flow completed with errors. Please try again')
            return -1
        _authorizer.AuthorizationServer.shutdown()
        return 0

    @staticmethod
    def _wait_for_sign_in_completion():
        while LoginCommandHandler.__SignInInprogress:
            pass  # Wait until we get a completed event from the auth service

    def handle(self):
        print(f'Authorization Code Flow intialised at {datetime.datetime.now()}')
        _authorizer.add_auth_subsciber(_authorizer.AuthEvent.AUTH_SUCCESS, LoginCommandHandler.on_auth_finished)
        LoginCommandHandler.__SignInInprogress = True
        _authorizer.AuthorizerService.login()
        self._wait_for_sign_in_completion()


class LibraryCommandHandler(CommandHandler):
    def handle(self):
        print('Library API handler intialised')


class PersonalisationCommandHandler(CommandHandler):
    def __init__(self, context_object):
        super().__init__(context_object)
        self._args = self._populate_args()
        self._func_command_map = {
            'GetTopArtists': self._get_top_artists
        }

    def _populate_args(self):
        self._args = _shared_mod.PersonlisationParams()
        self._args.time_range = self._Context.time_range
        self._args.offset = self._Context.offset
        self._args.limit = self._Context.limit
        return self._args

    def _get_top_artists(self):
        print('Finding your top artists..')
        self._args.entity_type = 'artists'
        api = spotify.PersonalisationAPI(params=self._args)
        json_response = api.get_top_tracks_and_artists()
        print()
        print(json_response)

    def handle(self):
        function_name = sys.argv[2]
        print(f'Personalisation API handler intialised. Function to call: {function_name}')
        func = self._func_command_map.get(function_name)
        if func is None:
            raise _shared_mod.InvalidCommandError(f'[{PersonalisationCommandHandler.__name__}] - '
                                                  f'Command {function_name} is invalid or not supported')
        return func()


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
        handlder_obj.execute()


class BootStrapper:
    @staticmethod
    def execute():
        dotenv.load_dotenv()


def main():
    try:
        print('Initialise spt CLI..')
        BootStrapper.execute()
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
