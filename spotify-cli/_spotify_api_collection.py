import abc
from typing import List

import requests

import _authorizer


class RequestExecutorBase(abc.ABC):
    def __init__(self, request_url, scopes):
        self._requet_url = request_url
        self._scopes = scopes
        self._headers = {}
        self._params = {}
        self._body = {}

    @property
    def body(self) -> dict:
        return self._body

    @body.setter
    def body(self, payload: dict):
        if isinstance(payload, dict):
            self._body = payload

    @property
    def headers(self) -> dict:
        return self._headers

    @headers.setter
    def headers(self, payload: dict):
        if isinstance(payload, dict):
            self._headers = payload

    @property
    def params(self) -> dict:
        return self._params

    @params.setter
    def params(self, payload: dict):
        if isinstance(payload, dict):
            self._params = payload

    def add_parameter(self, parameter_name: str, parameter_value: str) -> str:
        self._params[parameter_name] = parameter_value
        return self._params[parameter_name]

    def add_header(self, header_name: str, header_value: str) -> str:
        self._headers[header_name] = header_value
        return self._headers[header_name]

    def add_payload(self, key: str, value: object) -> object:
        self._body[key] = value
        return self._body[key]

    def authorization_rquest(self):
        _authorizer.AuthorizerService.login()
        _authorizer.AuthorizerService.check_scopes(self._scopes)

    @abc.abstractmethod
    def execute_request(self):
        pass

    def execute(self):
        self.authorization_rquest()
        self.execute()
        return {}


class GetRequestExecutor(RequestExecutorBase):
    def __init__(self, request_url, scopes):
        super().__init__(request_url, scopes)

    def execute_request(self):
        response = requests.get(self._requet_url,
                                headers=self._headers,
                                params=self._params)
        return response


# region Spotify API Reference
class SpotifyAPIBase:
    def __init__(self):
        self.RequiredScopes = ''

    def get_fullname(self, func_name: str):
        return type(self).__name__ + func_name


class UserProfileAPI(SpotifyAPIBase):
    def __init__(self):
        super().__init__()
        self.RequiredScopes = [
            SpotifyScope.READ_EMAIL,
            SpotifyScope.READ_PRIVATE
        ]

    def get_current_users_profile(self):
        req = GetRequestExecutor(SpotifyEndPoints.CURRENT_USER,
                                 scopes=self.RequiredScopes)
        json_response = req.execute()
        return json_response

    def get_public_users_profile(self, user_id: str):
        fullurl = f'{SpotifyEndPoints.PUBLIC_USERS}/{user_id}'
        req = GetRequestExecutor(request_url=fullurl,
                                 scopes=self.RequiredScopes)
        json_response = req.execute()
        return json_response


class PersonalisationAPI(SpotifyAPIBase):
    def get_top_tracks_and_artists(self):
        pass


class LibraryAPI(SpotifyAPIBase):

    # region Read methods
    def check_albums(self, album_ids: List[str]):
        """Check if one or more albums is already saved in the current Spotify user’s library"""
        pass

    def get_saved_albums(self):
        pass

    def check_tracks(self, track_ids: List[str]):
        pass

    def get_saved_tracks(self):
        pass

    def check_saved_shows(self, show_ids: List[str]):
        pass

    def get_saved_shows(self):
        pass

    # endregion

    # region Add or Update methods
    def add_albums(self):
        pass

    def add_tracks(self):
        pass

    def add_shows(self):
        pass

    # endregion

    # region Delete methods
    def remove_alums(self, album_ids: List[str]):
        pass

    def remove_shows(self, show_ids: List[str]):
        pass

    def remove_tracks(self, track_ids):
        pass

    # endregion


class TracksAPI(SpotifyAPIBase):
    def get_track(self):
        pass

    def get_audio_featues(self):
        pass

    def get_audio_anlysis(self):
        pass
# endregion
