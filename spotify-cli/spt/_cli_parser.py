import abc
import argparse
import datetime
import sys
import traceback

from progress.spinner import Spinner

import _authorizer
import _shared_mod
import _spotify_web_api as spotify
from _logger import default_logger as log

# region Parser Configuration

# Shared main_cli_parser - stores shared options

common_fetch_parser = argparse.ArgumentParser(add_help=False)
common_fetch_parser.add_argument('--limit', '-l', default=30, dest='limit', help='The maximum number of objects to '
                                                                                 'return. Default: 20. Minimum: 1. '
                                                                                 'Maximum: 50')
common_fetch_parser.add_argument('--offset', '-o', default=0, dest='offset', help='Index of the first object to return')

# Top-level/Parent main_cli_parser
main_cli_parser = argparse.ArgumentParser(prog='Interact with the Spotify Web API via the command line')
subparsers = main_cli_parser.add_subparsers(help='Typical usage: spt <subcommand> [subcomand options]')

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
    def __init__(self, context_object: argparse.Namespace):
        self._Context = context_object
        # TODO
        # self._save_to_file = context_object.save_to_file
        # self._output_file = context_object.output_file
        # self._file_format = context_object.file_format

    @staticmethod
    def handle_missing_scopes_error(scopes):
        response = input('Would you like to request additional scopes [Y or N]?    ')
        if str(response) not in ('Y', 'y', 'yes'):
            return
        log.info('Initiating request to get additional scopes: ', scopes)
        if isinstance(scopes, list):
            scopes = ' '.join(scopes).strip()

        _authorizer.AuthorizerService.add_auth_subsciber(_authorizer.AuthEvent.AUTH_COMPLETED,
                                                         LoginCommandHandler.on_auth_finished)
        _authorizer.AuthorizerService.get_more_scopes(new_scopes=scopes)

    @abc.abstractmethod
    def handle(self):
        pass

    def execute(self):
        try:
            return self.handle()
        except _shared_mod.NotLoggedInError:
            log.error(traceback.format_exc())
        except _shared_mod.MissingScopesError as ex:
            log.error(traceback.format_exc())
            self.handle_missing_scopes_error(ex.scopes)
        except _shared_mod.SpotifyAPICallError:
            log.error(traceback.format_exc())
        except Exception as ex:
            log.error(f'[ {type(self).__name__} - handle() encountered an unexpected error. {ex}.')
            log.debug(traceback.format_exc())


class LoginCommandHandler(CommandHandler):
    __SignInInprogress = False

    @staticmethod
    def on_auth_finished(has_error: bool):
        log.debug(f'Handle Auth Completed Event. Has Errors = {has_error} ')
        LoginCommandHandler.__SignInInprogress = False
        if has_error:
            log.warn('Authorization flow completed with errors. Please try again')
            return -1
        return 0

    @staticmethod
    def _wait_for_sign_in_completion():
        log.info('Authentication in progress')
        spinner = Spinner('Please wait...')
        while LoginCommandHandler.__SignInInprogress:
            spinner.next()  # Wait until we get a completed event from the auth service
        spinner.finish()

    def handle(self):
        log.info(f'Authorization Code Flow intialised at {datetime.datetime.now()}')
        _authorizer.AuthorizerService.add_auth_subsciber(_authorizer.AuthEvent.AUTH_COMPLETED,
                                                         LoginCommandHandler.on_auth_finished)
        LoginCommandHandler.__SignInInprogress = True
        login_in_progress = _authorizer.AuthorizerService.login()
        if login_in_progress:
            self._wait_for_sign_in_completion()


class LibraryCommandHandler(CommandHandler):
    def handle(self):
        print('Library API handler intialised')


class PersonalisationCommandHandler(CommandHandler):
    def __init__(self, context_object):
        super().__init__(context_object)
        self._args = self._populate_args()
        self._func_command_map = {
            'GetTopArtists': self._get_top_artists,
            'GetTopTracks': self._get_top_tracks
        }

    def _populate_args(self):
        self._args = _shared_mod.PersonlisationParams()
        self._args.time_range = self._Context.time_range
        self._args.offset = self._Context.offset
        self._args.limit = self._Context.limit
        return self._args

    def _get_top_artists(self):
        log.info('Finding your top artists..')
        self._args.entity_type = _shared_mod.PersonalisationEntityTypes.Artists.value
        api = spotify.PersonalisationAPI(params=self._args)
        json_response = api.get_top_tracks_and_artists()
        print()  # TODO: allow clients to specify multiple output options
        print(spotify.PersonalisationAPI.pretify_json(json_response))
        return json_response

    def _get_top_tracks(self):
        log.info('Finding your top tracks..')
        self._args.entity_type = _shared_mod.PersonalisationEntityTypes.Tracks.value
        api = spotify.PersonalisationAPI(params=self._args)
        json_response = api.get_top_tracks_and_artists()
        print()
        print(spotify.PersonalisationAPI.pretify_json(json_response))
        return json_response

    def handle(self):
        function_name = sys.argv[2]
        log.debug(f'Personalisation API handler intialised. Function to call: {function_name}')
        func = self._func_command_map.get(function_name)
        if func is None:
            raise _shared_mod.InvalidCommandError(f'[{PersonalisationCommandHandler.__name__}] - '
                                                  f'Command {function_name} is invalid or not supported')
        return func()

# endregion
