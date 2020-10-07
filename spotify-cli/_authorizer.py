"""Handler for Spotify Authorization Flow Callback Requests"""

__author__ = 'N Nemakhavhani'
__all__ = ['AuthorizerService', 'AuthEvent']

import json
import os
import threading
import traceback
import urllib.parse as urllib
import webbrowser
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from http import HTTPStatus

import requests
from flask import Flask, request

import _shared_mod

app = Flask(__name__)
_auth_subscribers = {}
DEFAULT_SCOPES = ' '.join([_shared_mod.SpotifyScope.READ_PRIVATE.value,
                           _shared_mod.SpotifyScope.READ_EMAIL.value,
                           _shared_mod.SpotifyScope.READ_LIBRARY.value])
STD_DATETIME_FMT = '%Y%m%d_%H:%M:%S'
AUTHENTICATION_ERROR = 'Authorization code not received.\nError Code: Http %s.\nError Message: %s'


class AuthEvent(Enum):
    AUTH_COMPLETED = 'AUTH_COMPLETED'
    AUTH_SUCCESS = 'AUTH_SUCCESS'
    AUTH_FAILED = 'AUTH_FAILED'
    AUTH_STARTED = 'AUTH_STARTED'


class AuthServerStatus(Enum):
    RUNNING = 'RUNNING'
    STOPPED = 'STOPPED'


@dataclass
class SpotifyToken:
    access_token: str = ''
    token_type: str = ''
    scopes: str = ''
    expires_in: int = ''  # In seconds
    refresh_token: str = ''
    last_refreshed: datetime = datetime.now()

    @classmethod
    def from_json_response(cls, json_response):
        token = cls()
        token.access_token = json_response[_shared_mod.SpotifyAuthSections.ACCESS_TOKEN.value]
        token.refresh_token = json_response[_shared_mod.SpotifyAuthSections.REFRESH_TOKEN.value]
        token.token_type = json_response[_shared_mod.SpotifyAuthSections.TOKEN_TYPE.value]
        token.scopes = json_response[_shared_mod.SpotifyAuthSections.SCOPE.value]
        token.expires_in = json_response[_shared_mod.SpotifyAuthSections.EXPIRES_IN.value]
        return token

    @property
    def has_expired(self):
        elapsed_seconds = (self.last_refreshed - datetime.now()).total_seconds()
        is_token_expired = abs(round(elapsed_seconds)) >= self.expires_in
        return is_token_expired

    @property
    def is_authenticated(self):
        return self.access_token not in (None, '') and self.has_expired is False

    def has_scopes(self, scopes: str):
        """Verify that the currently granted token has the passed in scopes"""
        input_scopes_list = filter(lambda x: x not in (None, ''), scopes.split(' '))
        granted_scopes_list = filter(lambda x: x not in (None, ''), self.scopes.split(' '))
        return all(item in granted_scopes_list for item in input_scopes_list)

    def to_dict(self):
        token = {
            'access_token': self.access_token,
            'refresh_token': self.refresh_token,
            'token_type': self.token_type,
            'scope': self.scopes,
            'expires_in': self.expires_in,
            'last_refreshed': datetime.strftime(self.last_refreshed, STD_DATETIME_FMT)
        }
        return token


class AuthorizerService:
    CurrentUserEmail = 'todo@spotify.com'
    __credentials = None

    @staticmethod
    def set_credentials(credentials: SpotifyToken):
        AuthorizerService.__credentials = credentials
        return AuthorizerService.__credentials

    @staticmethod
    def _load_credentials_from_file():
        credpath = os.getenv('CREDENTIALS_STORE')
        if not os.path.exists(credpath):
            return None

        with open(credpath) as json_file:
            credentials = json.load(json_file)
            last_refreshed = datetime.strptime(credentials['last_refreshed'], STD_DATETIME_FMT)
            AuthorizerService.__credentials = SpotifyToken.from_json_response(credentials)
            AuthorizerService.__credentials.last_refreshed = last_refreshed
            return AuthorizerService.__credentials

    @staticmethod
    def get_user_credentials():
        if AuthorizerService.__credentials is not None:
            return AuthorizerService.__credentials
        return AuthorizerService._load_credentials_from_file()

    @staticmethod
    def get_access_token():
        credentials = AuthorizerService.get_user_credentials()
        return credentials.access_token if credentials is not None else ''

    @staticmethod
    def is_logged_in():
        if AuthorizerService.get_user_credentials() is None:
            print('Credent object is None. is logged in = false')
            return False
        is_authenticated = AuthorizerService.get_user_credentials().is_authenticated
        print('Is authenticated', is_authenticated)
        return is_authenticated

    @staticmethod
    def check_scopes(scopes, request_required_scope=True):
        """Check if the required scopes are already granted, else request the scopes from auth server"""
        has_scopes = AuthorizerService.get_user_credentials().has_scopes(scopes)
        if has_scopes is False and request_required_scope:
            pass
        return has_scopes

    @staticmethod
    def login(scopes=DEFAULT_SCOPES):
        print('Check if user is already logged in...')
        if AuthorizerService.is_logged_in():
            print(f'Already logged in as..{AuthorizerService.CurrentUserEmail}')
            _notify_auth_completed(has_error=False)
            return False
        auth_req_params = {'response_type': 'code',
                           'client_id': os.getenv('CLIENT_ID'),
                           'redirect_uri': os.getenv('REDIRECT_URI'),
                           'scope': scopes,
                           'state': 'anythingRandom',
                           'show_dialog': 'true'}
        auth_url = _shared_mod.SpotifyEndPoints.AUTHORIZE_URL.value + urllib.urlencode(auth_req_params)
        webbrowser.open_new_tab(auth_url)
        AuthorizationServer.start()
        return True

    @staticmethod
    def get_more_scopes(new_scopes: str):
        if AuthorizerService.is_logged_in() is False:
            raise _shared_mod.InvalidOperationError('You must be logged-in to request more scopes. '
                                                    'Use `spotify login` to authenticate')
        existing_scopes = AuthorizerService.get_user_credentials().scopes
        scopes = f'{existing_scopes.strip()} {new_scopes.strip()}'

        auth_req_params = {'response_type': 'code',
                           'client_id': os.getenv('CLIENT_ID'),
                           'redirect_uri': os.getenv('REDIRECT_URI'),
                           'scope': scopes,
                           'state': 'anythingRandom',
                           'show_dialog': 'true'}
        auth_url = _shared_mod.SpotifyEndPoints.AUTHORIZE_URL + urllib.urlencode(auth_req_params)
        webbrowser.open_new_tab(auth_url)
        AuthorizationServer.start()


class AuthorizationServer:
    __status = AuthServerStatus.STOPPED

    @staticmethod
    def get_status():
        return AuthorizationServer.__status

    @staticmethod
    def _start():
        print('AuthorizationServer started at %s' % datetime.now())
        app.run(os.getenv('HOST_IP'), os.getenv('HOST_PORT'))
        AuthorizerService.__status = AuthServerStatus.RUNNING
        return AuthorizationServer.__status

    @staticmethod
    def start():
        t = threading.Thread(target=AuthorizationServer._start)
        t.start()
        return AuthorizationServer.__status

    @staticmethod
    def shutdown():
        if AuthorizationServer.__status == AuthServerStatus.STOPPED:
            return AuthorizationServer.__status
        AuthorizationServer._shutdown_dev_server()
        AuthorizationServer.__status = AuthServerStatus.STOPPED
        print('Authorizer server status = %s at %s' % (AuthorizationServer.__status, datetime.now()))
        return AuthorizationServer.__status

    @staticmethod
    def _shutdown_dev_server():
        print('Authorization Server Shutting down..')
        func = request.environ.get('werkzeug.server.shutdown')
        if func is None:
            raise RuntimeError('Not running with the Werkzeug Server')
        func()


# region Events

def add_auth_subsciber(event_id, event_handler):
    if event_id in _auth_subscribers:
        _auth_subscribers[event_id].append(event_handler)
        return 0
    _auth_subscribers[event_id] = [event_handler]


# endregion

# region Request Handler Helpers

def _save_access_token(json_response):
    token_object = SpotifyToken.from_json_response(json_response)
    with open(os.getenv('CREDENTIALS_STORE'), 'w') as json_file:
        json.dump(token_object.to_dict(), json_file, indent=4)
        print('Security info succcessfully stored.')
        return token_object


def _notify_auth_started():
    print('Raise %s event' % AuthEvent.AUTH_STARTED)
    if not _auth_subscribers:
        return

    subscriber_list = _auth_subscribers.get(AuthEvent.AUTH_STARTED)
    for sub in subscriber_list:
        sub()


def _notify_auth_completed(has_error: bool):
    print('Raise %s event' % AuthEvent.AUTH_COMPLETED)
    if not _auth_subscribers:
        return

    subscriber_list = _auth_subscribers.get(AuthEvent.AUTH_COMPLETED)
    for sub in subscriber_list:
        sub(has_error)


def _notify_auth_success():
    print('Raise %s event' % AuthEvent.AUTH_SUCCESS)
    if not _auth_subscribers:
        return

    subscriber_list = _auth_subscribers.get(AuthEvent.AUTH_SUCCESS)
    for sub in subscriber_list:
        sub()


def _notify_auth_failed(ex):
    print('Raise %s event' % AuthEvent.AUTH_FAILED)
    if not _auth_subscribers:
        return

    subscriber_list = _auth_subscribers.get(AuthEvent.AUTH_FAILED) or []
    for sub in subscriber_list:
        sub()


def _on_auth_code_received():
    """Going to use the code we received to get an Access + Refresh token"""
    code = request.args.get('code')
    body = {'grant_type': 'authorization_code',
            'code': code,
            'client_id': os.getenv('CLIENT_ID'),
            'client_secret': os.getenv('CLIENT_SECRET'),
            'redirect_uri': os.getenv('REDIRECT_URI')
            }
    response = requests.post(_shared_mod.SpotifyEndPoints.TOKEN_EXCHANGE_URL.value, data=body)
    if response.status_code == HTTPStatus.OK:
        saved_credentials = _save_access_token(response.json())
        AuthorizerService.set_credentials(saved_credentials)
        _notify_auth_completed(has_error=False)
        return 0
    raise _shared_mod.SpotifyAuthenticationError(AUTHENTICATION_ERROR % (response.status_code, response.text))


# endregion


# region Routes

@app.route('/')
def index():
    return 'Nothing to see here'


@app.route('/authcallback')
def on_auth_callback():
    try:
        code = request.args.get('code')
        if code not in (None, ''):
            _on_auth_code_received()
            return 'Authorization Code granted. Now Requesting Access token'

        raise _shared_mod.SpotifyAuthenticationError('Authorization code not granted. Check your Spotify Dashboard '
                                                     'configuration.\nAuth server response %s' % request.args)
    except Exception as ex:
        _notify_auth_completed(has_error=True)
        print(traceback.format_exc())
        return 'Unexpected authentication error. %s' % ex

# endregion
