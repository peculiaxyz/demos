"""Handles Spotify Authorization Code Flow"""

__all__ = ['AuthorizerService', 'AuthorizationServer', 'AuthEvent', 'AuthServerStatus']

import json
import os
import threading
import traceback
import typing
import urllib.parse as urllib
import uuid
import webbrowser
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from http import HTTPStatus

import flask
import requests

import _app_config as cfg
import _shared_mod
from _logger import default_logger as log

DEFAULT_SCOPES = ' '.join([_shared_mod.SpotifyScope.READ_PRIVATE.value,
                           _shared_mod.SpotifyScope.READ_EMAIL.value,
                           _shared_mod.SpotifyScope.READ_LIBRARY.value])
STD_DATETIME_FMT = '%Y%m%d_%H:%M:%S'
AUTHENTICATION_ERROR = 'Authorization code not received.\nError Code: Http %s.\nError Message: %s'
TOKEN_REFRESH_ERROR = 'Token refresh request failed.\nError Code: Http %s.\nError Message: %s'


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
        elapsed_seconds = (datetime.now() - self.last_refreshed).total_seconds()
        is_token_expired = round(elapsed_seconds) >= self.expires_in
        return is_token_expired

    @property
    def has_refresh_token(self):
        return self.refresh_token not in (None, '')

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
    __default_security_store = '.credentials.json'
    __current_user_email = 'todo@spotify.com'
    __auth_subscribers = {}
    __credentials = None
    __state_key = ''

    @staticmethod
    def _load_saved_credentials():
        credpath = os.getenv('SPT_SECURITY_STORE', default=AuthorizerService.__default_security_store)
        if not os.path.exists(credpath):
            return None

        with open(credpath) as json_file:
            credentials = json.load(json_file)
            last_refreshed = datetime.strptime(credentials['last_refreshed'], STD_DATETIME_FMT)
            AuthorizerService.__credentials = SpotifyToken.from_json_response(credentials)
            AuthorizerService.__credentials.last_refreshed = last_refreshed
            return AuthorizerService.__credentials

    # region Event handlers

    @staticmethod
    def add_auth_subsciber(event_id: AuthEvent, event_handler: typing.Callable):
        log.debug(f'Register subscriber {event_handler.__name__} for {event_id}')

        if event_id in AuthorizerService.__auth_subscribers:
            AuthorizerService.__auth_subscribers[event_id].append(event_handler)
            return
        AuthorizerService.__auth_subscribers[event_id] = [event_handler]

    @staticmethod
    def notify_auth_completed(has_error: bool):
        subscriber_list = AuthorizerService.__auth_subscribers.get(AuthEvent.AUTH_COMPLETED)
        if not subscriber_list:
            log.debug(f'No subscriibers registered for {AuthEvent.AUTH_COMPLETED} event')
            return

        if not has_error:
            AuthorizationServer.shutdown()

        log.debug(f'Raise {AuthEvent.AUTH_COMPLETED} event. Subscribers {subscriber_list}')
        for event_handler in subscriber_list:
            event_handler(has_error)

    # endregion

    # region Authorization code flow handlers
    @staticmethod
    def _save_credentials(json_response):
        token_object = SpotifyToken.from_json_response(json_response)
        with open(os.getenv('SPT_SECURITY_STORE', default=AuthorizerService.__default_security_store),
                  'w') as json_file:
            json.dump(token_object.to_dict(), json_file, indent=4)
            log.debug('Security info succcessfully stored.')
            return token_object  # TODO: Is this secure?

    @staticmethod
    def on_auth_code_received(request_object: flask.Request):
        """Going to use the  authoization code we received to reuqest  an Access/Refresh token from Spotify"""

        code = request_object.args.get('code')
        body = {'grant_type': 'authorization_code',
                'code': code,
                'client_id': os.getenv('SPT_CLIENT_ID'),
                'client_secret': os.getenv('SPT_CLIENT_SECRET'),
                'redirect_uri': os.getenv('SPT_REDIRECT_URI')
                }
        response: requests.Response = requests.post(_shared_mod.SpotifyEndPoints.TOKEN_EXCHANGE_URL.value, data=body)
        if response.status_code == HTTPStatus.OK:
            saved_credentials = AuthorizerService._save_credentials(response.json())
            AuthorizerService.__credentials = saved_credentials
            AuthorizerService.notify_auth_completed(has_error=False)
            return 0
        raise _shared_mod.SpotifyAuthenticationError(AUTHENTICATION_ERROR % (response.status_code, response.text))

    # endregion

    # region Accessor methods

    @staticmethod
    def get_user_credentials():
        if AuthorizerService.__credentials is not None:
            return AuthorizerService.__credentials
        return AuthorizerService._load_saved_credentials()

    @staticmethod
    def get_access_token():
        credentials = AuthorizerService.get_user_credentials()
        return credentials.access_token if credentials is not None else ''

    @staticmethod
    def is_logged_in():
        if AuthorizerService.get_user_credentials() is None:
            return False
        is_authenticated = AuthorizerService.get_user_credentials().is_authenticated
        if not is_authenticated and AuthorizerService.get_user_credentials().has_expired and \
                AuthorizerService.get_user_credentials().has_refresh_token:
            AuthorizerService.refresh_access_token(credentials=AuthorizerService.get_user_credentials())
            return True
        return is_authenticated

    @staticmethod
    def check_scopes(scopes, request_required_scope=True):
        """Check if the required scopes are already granted, else request the scopes from auth server"""
        if isinstance(scopes, list):
            scopes = ' '.join(scopes).strip()
        has_scopes = AuthorizerService.get_user_credentials().has_scopes(scopes)
        if has_scopes is False and request_required_scope:
            pass
        return has_scopes

    # endregion

    @staticmethod
    def login(scopes=DEFAULT_SCOPES):
        if AuthorizerService.is_logged_in():
            log.info(f'Abort. Already logged in as..{AuthorizerService.__current_user_email}')
            AuthorizerService.notify_auth_completed(has_error=False)
            return False
        AuthorizerService.__state_key = uuid.uuid4()
        auth_req_params = {'response_type': 'code',
                           'client_id': os.getenv('SPT_CLIENT_ID'),
                           'redirect_uri': os.getenv('SPT_REDIRECT_URI'),
                           'scope': scopes,
                           'state': str(AuthorizerService.__state_key),
                           'show_dialog': 'true'}
        auth_url = _shared_mod.SpotifyEndPoints.AUTHORIZE_URL.value + urllib.urlencode(auth_req_params)
        log.debug(f'Sending Authentication request to..{auth_url}')
        webbrowser.open_new_tab(auth_url)
        AuthorizationServer.start()
        return True

    @staticmethod
    def get_more_scopes(new_scopes: str):
        if AuthorizerService.is_logged_in() is False:
            raise _shared_mod.InvalidOperationError('You must be logged-in in order to request more scopes. ')

        existing_scopes = AuthorizerService.get_user_credentials().scopes
        scopes = f'{existing_scopes.strip()} {new_scopes.strip()}'
        AuthorizerService.__state_key = uuid.uuid4()

        auth_req_params = {'response_type': 'code',
                           'client_id': os.getenv('SPT_CLIENT_ID'),
                           'redirect_uri': os.getenv('SPT_REDIRECT_URI'),
                           'scope': scopes,
                           'state': str(AuthorizerService.__state_key),
                           'show_dialog': 'true'}
        auth_url = _shared_mod.SpotifyEndPoints.AUTHORIZE_URL.value + urllib.urlencode(auth_req_params)
        log.debug(f'Sending Authentication request to..{auth_url}')
        webbrowser.open_new_tab(auth_url)
        AuthorizationServer.start()

    @staticmethod
    def refresh_access_token(credentials: SpotifyToken):
        log.debug('Refreshing access token')
        body = {'grant_type': 'refresh_token',
                'refresh_token': credentials.refresh_token,
                'client_id': os.getenv('SPT_CLIENT_ID'),
                'client_secret': os.getenv('SPT_CLIENT_SECRET'),
                'redirect_uri': os.getenv('SPT_REDIRECT_URI')
                }
        response: requests.Response = requests.post(_shared_mod.SpotifyEndPoints.TOKEN_EXCHANGE_URL.value, data=body)
        if response.status_code == HTTPStatus.OK:
            log.debug('Access token successfully refreshed')
            json_res = response.json()
            json_res['refresh_token'] = credentials.refresh_token  # Spotify doesnt send back refresh token
            saved_credentials = AuthorizerService._save_credentials(json_res)
            AuthorizerService.__credentials = saved_credentials
            return AuthorizerService.__credentials
        raise _shared_mod.SpotifyAuthenticationError(TOKEN_REFRESH_ERROR % (response.status_code, response.text))


class AuthorizationServer:
    app = flask.Flask(cfg.GlobalConfiguration.get_app_name())
    __status = AuthServerStatus.STOPPED

    # region Attribute accessors

    @staticmethod
    def get_server_status():
        return AuthorizationServer.__status

    # endregion

    # region Helper methods
    @staticmethod
    def _shutdown_dev_server():
        func = flask.request.environ.get('werkzeug.server.shutdown')
        if func is None:
            raise RuntimeError('Not running with the Werkzeug Server')
        func()

    @staticmethod
    def _start():
        host_ip, host_port = os.getenv('SPT_HOST_IP'), os.getenv('SPT_HOST_PORT')
        log.debug(f'Starting Authorization Server at {host_ip}:{host_port}')
        AuthorizationServer.app.run(host_ip, host_port)
        AuthorizerService.__status = AuthServerStatus.RUNNING
        return AuthorizationServer.__status

    # endregion

    # region Server routes

    @staticmethod
    @app.route('/')
    def index():
        return 'Nothing to see here'

    @staticmethod
    @app.route('/authcallback')
    def on_auth_callback():
        try:
            code = flask.request.args.get('code')
            if code not in (None, ''):
                AuthorizerService.on_auth_code_received(request_object=flask.request)
                return 'Authorization Code granted'

            raise _shared_mod.SpotifyAuthenticationError(f'Authorization code not granted. {flask.request.args}')
        except Exception as ex:
            log.error(traceback.format_exc())
            AuthorizerService.notify_auth_completed(has_error=True)
            return f'Unexpected authentication error. Please try again later.\n{ex}'

    # endregion

    @staticmethod
    def start():
        try:
            t = threading.Thread(target=AuthorizationServer._start)
            t.start()
            return AuthorizationServer.__status
        except Exception as ex:
            raise _shared_mod.LocalAuthServerStartupError(ex)

    @staticmethod
    def shutdown():
        try:
            log.debug('Shutdown Authorization Sever signal received')
            if AuthorizationServer.__status == AuthServerStatus.STOPPED:
                log.debug('Server not running. Ignoring shutdown signal')
                return AuthorizationServer.__status

            AuthorizationServer._shutdown_dev_server()
            AuthorizationServer.__status = AuthServerStatus.STOPPED
            log.debug('Authorization Sever shutdown successful.')
            return AuthorizationServer.__status
        except Exception as ex:
            raise _shared_mod.LocalAuthServerShutdownError(ex)
