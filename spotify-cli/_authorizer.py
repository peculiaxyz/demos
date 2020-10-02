"""Handler for Spotify Authorization Flow Callback Requests"""

__author__ = 'N Nemakhavhani'
__all__ = ['AuthorizerService', 'AuthEvent']

import json
import threading
import traceback
import urllib.parse as urllib
import webbrowser
from datetime import datetime
from enum import Enum

import requests
from flask import Flask, Request, request

app = Flask(__name__)
HOST_IP = '127.0.0.1'
HOST_PORT = 6949
CREDENTIALS_STORE = '.creds.json'  # TODO: must be an environment variable
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
    def stop():
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

def _save_access_token(request_object: Request):
    credentials = {
        "access_token": request_object.args.get('access_token'),
        "token_type": request_object.args.get('token_type'),
        "expires_in": request_object.args.get('expires_in')
    }
    with open(CREDENTIALS_STORE, 'w') as json_file:
        json.dump(credentials, json_file, indent=4)


def _notify_auth_started(req: Request):
    pass


def _notify_auth_success(req: Request):
    print('Raise %s event' % AuthEvent.AUTH_SUCCESS)
    if not _auth_subscribers:
        return

    subscriber_list = _auth_subscribers.get(AuthEvent.AUTH_SUCCESS)
    for sub in subscriber_list:
        sub()


def _notify_auth_failed(req: Request):
    pass


def _on_auth_code_received():
    """Going to use the code we received to get an Access + Refresh token"""
    code = request.args.get('code')
    print("ASK FOR TOKEN WITH CODE", code)
    request_params = {
        'client_id': CLIENT_ID,
        'client_secret': CLIENT_SECRET
    }
    body = {'grant_type': 'authorization_code',
            'code': code,
            'client_id': CLIENT_ID,
            'client_secret': CLIENT_SECRET,
            'redirect_uri': REDIRECT_URI
            }
    req_url = TOKEN_EXCHANGE_URL

    response = requests.post(req_url, data=body)
    json_response = response.json()
    print('Access token', json_response['access_token'])
    print(response.status_code)
    print(response.text)
    print(response.headers)
    print(response)


def _on_access_tokens_received():
    _save_access_token(request)
    _notify_auth_success(request)


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

        _on_access_tokens_received()
        return 'Authentication successfull'
    except Exception as e:
        traceback.print_exc()
        return 'Not authenticated, unexpected error occured.'

# endregion
