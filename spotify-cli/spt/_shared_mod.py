import json
from dataclasses import dataclass
from enum import Enum
from typing import List, Union

APP_INFO_LOG = 'Spotify Shell. @Copyright 2020'
LEGAL_NOTICE = """"
    Spotify CLI  Copyright (C) 2020  Ndamulelo Nemakhavhani
    This program comes with ABSOLUTELY NO WARRANTY; for details type `show w'.
    This is free software, and you are welcome to redistribute it
    under certain conditions; type `show c' for details
"""
CRITICAL_ERROR_LOG = 'A critical error has occured, the app will now close.\n%s'


class AppConfig:
    pass


# region Custom Exceptions
class GlobalConfigurationError(Exception):
    def __init__(self, filepath):
        self._config_store = filepath

    def __str__(self):
        return f'Configuration file {self._config_store} not found'


class InvalidCommandError(Exception):
    pass


class InvalidUsageError(Exception):
    def __str__(self):
        return 'Invalid usage, please type spt --help to view usage instructions'


class InvalidCommandHandlerError(Exception):
    pass


class NotLoggedInError(Exception):
    def __str__(self):
        return 'You need to be loggen in order to execute this command. Use `spt login` to login'


class MissingScopesError(Exception):
    def __init__(self, mising_scope: Union[str, list, tuple]):
        self.scopes = mising_scope

    def __str__(self):
        return f'The following scopes required to execute the comand are missing. {self.scopes}.'


class InvalidOperationError(Exception):
    pass


class SpotifyAPICallError(Exception):
    pass


class SpotifyAuthenticationError(Exception):
    pass


class LocalAuthServerStartupError(Exception):
    def __init__(self, inner_exception: Exception):
        self._inner_exception = inner_exception

    def __str__(self):
        return f'Authortization server failed to start\n{self._inner_exception}'


class LocalAuthServerShutdownError(Exception):
    def __init__(self, inner_exception: Exception):
        self._inner_exception = inner_exception

    def __str__(self):
        return f'Authortization server failed to shutdown\n{self._inner_exception}'


# endregion


# region Spotify constants

class SpotifyScope(Enum):
    READ_EMAIL = 'user-read-email'
    READ_PRIVATE = 'user-read-private'
    READ_LIBRARY = 'user-library-read'
    READ_TOP = 'user-top-read'


class SpotifyEndPoints(Enum):
    # Authentication/Authorization endpoints
    AUTHORIZE_URL = 'https://accounts.spotify.com/authorize/?'
    TOKEN_EXCHANGE_URL = 'https://accounts.spotify.com/api/token/?'

    # API endpoints
    CURRENT_USER = 'https://api.spotify.com/v1/me'
    PUBLIC_USERS = 'https://api.spotify.com/v1/users'
    TOP_TRACKS_ARTISTS = 'https://api.spotify.com/v1/me/top'


class SpotifyAuthSections(Enum):
    ACCESS_TOKEN = 'access_token'
    REFRESH_TOKEN = 'refresh_token'
    TOKEN_TYPE = 'token_type'
    EXPIRES_IN = 'expires_in'
    CODE = 'code'
    SCOPE = 'scope'


class PersonalisationEntityTypes(Enum):
    Artists = 'artists'
    Tracks = 'tracks'


# endregion


# region Spotify Request Param Objects
@dataclass
class PersonlisationParams:
    entity_type = ''
    time_range: str = ''
    limit = 0
    offset = 0


@dataclass
class UserLibraryParams:
    pass


# region


class SptOutputChannels(Enum):
    SdtOut = "StdOut"
    JsonFile = "JsonFile"


class SptOutputWriter:
    """Given a json output from a REST API call, print results to the console or json file
    """

    def __init__(self, channels: List[SptOutputChannels], output_path=None):
        self._channels = channels
        self._outpath = output_path
        self._channel_handler_map = {
            SptOutputChannels.SdtOut.value: SptOutputWriter.print_to_std_out,
            SptOutputChannels.JsonFile.value: SptOutputWriter.print_to_json_file,
        }

    @staticmethod
    def pretify_json(json_data: dict) -> str:
        pretty_json = json.dumps(json_data, indent=4)
        return pretty_json

    @staticmethod
    def print_to_std_out(payload):
        pretty_payload = SptOutputWriter.pretify_json(payload)
        print(pretty_payload)

    def print_to_json_file(self, payload):
        with open(self._outpath, 'w') as json_file:
            json.dump(payload, json_file, indent=4)

    def execute(self, payload: dict):
        for out_channel in self._channels:
            handler = self._channel_handler_map.get(out_channel)
            if handler is not None:
                handler(payload)
