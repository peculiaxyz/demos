"""Handler for Spotify Authorization Flow Callback Requests"""

__author__ = 'N Nemakhavhani'
__all__ = ['AuthorizerService', 'AuthEvent']

import json
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

app = Flask(__name__)
HOST_IP = '127.0.0.1'
HOST_PORT = 6949
CREDENTIALS_STORE = '.creds.json'  # TODO: must be an environment variable
STD_DATETIME_FMT = '%Y%m%d_%H:%M:%S'
_auth_subscribers = {}

"""
For testing we will  use Implicit Grant Flow(Only works on pure JS sites - No servers).

However Authorization Code Flow is 'more' secure.
Ref: https://developer.okta.com/blog/2018/04/10/oauth-authorization-code-grant-type
"""
AUTHORIZE_URL = 'https://accounts.spotify.com/authorize/?'
TOKEN_EXCHANGE_URL = 'https://accounts.spotify.com/api/token/?'
SCOPES = 'user-read-private user-read-email'
CLIENT_ID = '8fed9a69a36f416e9d1069c3a74f23f3'
CLIENT_SECRET = '3f5b1bbc48ed4f06bb8b44dc1bfed495'
REDIRECT_URI = 'http://localhost:6949/authcallback'
REQUEST_PARAMS = {'response_type': 'code',
                  'client_id': CLIENT_ID,
                  'redirect_uri': REDIRECT_URI,
                  'scope': SCOPES,
                  'state': 'anythingRandom',
                  'show_dialog': 'true'}
request_url = AUTHORIZE_URL + urllib.urlencode(REQUEST_PARAMS)


class AuthEvent(Enum):
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
        token.access_token = json_response['access_token']
        token.refresh_token = json_response['refresh_token']
        token.token_type = json_response['token_type']
        token.scopes = json_response['scope']
        token.expires_in = json_response['expires_in']
        return token

    @property
    def has_expired(self):
        elapsed_seconds = (self.last_refreshed - datetime.now()).seconds
        return elapsed_seconds >= self.expires_in

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
    __status = AuthServerStatus.STOPPED

    @staticmethod
    def get_status():
        return AuthorizerService.__status

    @staticmethod
    def _shutdown_dev_server():
        func = request.environ.get('werkzeug.server.shutdown')
        if func is None:
            raise RuntimeError('Not running with the Werkzeug Server')
        func()

    @staticmethod
    def get_access_token():
        with open(CREDENTIALS_STORE) as json_file:
            credentials = json.load(json_file)
            return credentials.get('access_token')

    @staticmethod
    def _start():
        print('Authorizer service started at %s' % datetime.now())
        app.run(HOST_IP, HOST_PORT)
        AuthorizerService.__status = AuthServerStatus.RUNNING
        return AuthorizerService.__status

    @staticmethod
    def start():
        t = threading.Thread(target=AuthorizerService._start)
        t.start()
        return AuthorizerService.__status

    @staticmethod
    def shutdown():
        AuthorizerService._shutdown_dev_server()
        AuthorizerService.__status = AuthServerStatus.STOPPED
        return AuthorizerService.__status

    @staticmethod
    def is_logged_in():
        pass

    @staticmethod
    def login():
        webbrowser.open_new_tab(request_url)
        AuthorizerService.start()


def add_auth_subsciber(event_id, event_handler):
    if event_id in _auth_subscribers:
        _auth_subscribers[event_id].append(event_handler)
        return 0
    _auth_subscribers[event_id] = [event_handler]


# region Request Handler Helpers

def _save_access_token(json_response):
    token_object = SpotifyToken.from_json_response(json_response)
    with open(CREDENTIALS_STORE, 'w') as json_file:
        json.dump(token_object.to_dict(), json_file, indent=4)
        print('Security info succcessfully stored.')


def _notify_auth_started():
    print('Raise %s event' % AuthEvent.AUTH_STARTED)
    if not _auth_subscribers:
        return

    subscriber_list = _auth_subscribers.get(AuthEvent.AUTH_STARTED)
    for sub in subscriber_list:
        sub()


def _notify_auth_success():
    print('Raise %s event' % AuthEvent.AUTH_SUCCESS)
    if not _auth_subscribers:
        return

    subscriber_list = _auth_subscribers.get(AuthEvent.AUTH_SUCCESS)
    for sub in subscriber_list:
        sub()


def _notify_auth_failed():
    print('Raise %s event' % AuthEvent.AUTH_FAILED)
    if not _auth_subscribers:
        return

    subscriber_list = _auth_subscribers.get(AuthEvent.AUTH_FAILED) or []
    for sub in subscriber_list:
        sub()


def _on_access_tokens_received(json_response):
    _save_access_token(json_response)
    _notify_auth_success()
    return 0


def _on_auth_code_received():
    """Going to use the code we received to get an Access + Refresh token"""
    code = request.args.get('code')
    body = {'grant_type': 'authorization_code',
            'code': code,
            'client_id': CLIENT_ID,
            'client_secret': CLIENT_SECRET,
            'redirect_uri': REDIRECT_URI
            }
    response = requests.post(TOKEN_EXCHANGE_URL, data=body)
    if response.status_code == HTTPStatus.OK:
        return _on_access_tokens_received(response.json())
    print(response.text)  # TODO: use a logger
    raise ValueError('Request for access token from autorization code failed')


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
            return 'Code granted.Requesting Access tokeb'

        raise RuntimeError('Authorization code not granted')
    except Exception as e:
        _notify_auth_failed()
        traceback.print_exc()
        return 'Not authenticated, unexpected error occured.'

# endregion
