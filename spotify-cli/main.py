import dotenv
import requests
from flask import Flask

import _authorizer


class SpotifyAPIWrapper:
    def __init__(self, access_token):
        self._access_token = access_token

    @staticmethod
    def _check_authentication():
        if not _authorizer.AuthorizerService.is_logged_in():
            _authorizer.AuthorizerService.login()
            return False
        return True

    def get_saved_albums(self):
        req_url = 'https://api.spotify.com/v1/me/albums'
        required_scope = ['user-library-read']
        if self._access_token in (None, ''):
            print('Çant read albums, user is not authorized')
            return
        params = {
            'limit': 50,
        }
        request_header = {'Authorization': f'Bearer {self._access_token}'}
        response = requests.get(req_url, params=params, headers=request_header)
        if response.status_code == 200:
            print('Returning all your albumbs...')
            print(response.json())
        else:
            raise ValueError('Albums not found. Response code: %s' % response.status_code)


IS_AUTHFLOW_COMPLETE = False
API = SpotifyAPIWrapper('')


def on_auth_finished():
    global API, IS_AUTHFLOW_COMPLETE
    print('Print auth finished - should return something to monitor auth state?')
    print('Access token: ', _authorizer.AuthorizerService.get_access_token())
    API = SpotifyAPIWrapper(_authorizer.AuthorizerService.get_access_token())
    IS_AUTHFLOW_COMPLETE = True
    _authorizer.AuthorizationServer.shutdown()
    return API


def main():
    dotenv.load_dotenv()
    _authorizer.add_auth_subsciber(_authorizer.AuthEvent.AUTH_SUCCESS, on_auth_finished)
    _authorizer.AuthorizerService.login()
    while not IS_AUTHFLOW_COMPLETE:
        pass
    print('All good..Running Test Query Now')
    API.get_saved_albums()


class TestFlask:
    app = None

    @staticmethod
    @app.route('/')
    def index():
        return 'I am a default route'

    @staticmethod
    def start():
        TestFlask.app = Flask('test')
        TestFlask.app.run()


# Wait for authorization before continuing
# While true, keep waiting if flow is in progress
# Eslse intiate a new request

if __name__ == '__main__':
    print('Before start', TestFlask.app)
    TestFlask.start()
    print('After start', TestFlask.app)
