from dataclasses import dataclass
from enum import Enum
from typing import Union


class AppConfig:
    pass


# region Custom Exceptions

class InvalidCommandError(Exception):
    pass


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


# endregion


# region Spotify Request Param Objects
@dataclass
class PersonlisationParams(object):
    entity_type = ''
    time_range: str = ''
    limit = 0
    offset = 0

# region
