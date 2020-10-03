from enum import Enum


class AppConfig:
    pass


class SpotifyAuthSections(Enum):
    ACCESS_TOKEN = 'access_token'
    REFRESH_TOKEN = 'refresh_token'
    TOKEN_TYPE = 'token_type'
    EXPIRES_IN = 'expires_in'
    CODE = 'code'
    SCOPE = 'scope'
