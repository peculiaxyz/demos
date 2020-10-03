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
        if self._access_token in (None, ''):
            print('Çant read albums, user is not authorized')
            return
        print('Returning all your albumbs...')


IS_AUTHFLOW_COMPLETE = False
API = SpotifyAPIWrapper('')


def on_auth_finished():
    global API, IS_AUTHFLOW_COMPLETE
    print('Print auth finished - should return something to monitor auth state?')
    print('Access token: ', _authorizer.AuthorizerService.get_access_token())
    API = SpotifyAPIWrapper(_authorizer.AuthorizerService.get_access_token())
    IS_AUTHFLOW_COMPLETE = True
    _authorizer.AuthorizerService.shutdown()
    return API


def main():
    _authorizer.add_auth_subsciber(_authorizer.AuthEvent.AUTH_SUCCESS, on_auth_finished)
    _authorizer.AuthorizerService.login()
    while not IS_AUTHFLOW_COMPLETE:
        pass
    print('All good..Running Test Query Now')
    API.get_saved_albums()


# Wait for authorization before continuing
# While true, keep waiting if flow is in progress
# Eslse intiate a new request

if __name__ == '__main__':
    main()
