"""Handler for Spotify Authorization Flow Callback Requests"""

__author__ = 'N Nemakhavhani'
__all__ = ['AuthorizerService', 'AuthEvent']

import traceback
from datetime import datetime
from enum import Enum

from flask import Flask, Request, request


class AuthEvent(Enum):
    AUTH_SUCCESS = 'AUTH_SUCCESS'
    AUTH_FAILED = 'AUTH_FAILED'
    AUTH_STARTED = 'AUTH_STARTED'


app = Flask(__name__)
HOST_IP = '127.0.0.1'
HOST_PORT = 6949


@app.route('/')
def index():
    return 'You"ve reached a dead-end'


@app.route('/authcallback/')
def on_auth_callback():
    req_object = request  # type: Request
    try:
        print(req_object)
        print('Access token', req_object.args.get('access_token'))
        print('Token type', req_object.args.get('token_type'))
        print('Expires in', req_object.args.get('expires_in'))
        return 'Auth completed!'
    except:
        traceback.print_exc()
        return 'Not authenticated, unexpected error occured.'


class AuthorizerService:
    __status = 'STOPPED'
    __subscribers = {}

    @staticmethod
    def get_status():
        return AuthorizerService.__status

    @staticmethod
    def get_subscribers():
        return AuthorizerService.__subscribers

    @staticmethod
    def add_subscriber(event_id, func):
        if not callable(func):
            raise ValueError('Func must be callable.')
        if func.__name__ not in AuthorizerService.__subscribers:
            AuthorizerService.__subscribers[func.__name__] = func
        return func.__name__

    @staticmethod
    def remove_subscriber(func):
        if func.__name__ in AuthorizerService.__subscribers:
            AuthorizerService.__subscribers[func.__name__] = func
        return func.__name__

    @staticmethod
    def shutdown_dev_server():
        func = request.environ.get('werkzeug.server.shutdown')
        if func is None:
            raise RuntimeError('Not running with the Werkzeug Server')
        func()

    @staticmethod
    def start():
        app.run(HOST_IP, HOST_PORT)
        print('Authorizer service started at %s' % datetime.now())
        AuthorizerService.__status = 'RUNNING'
        return AuthorizerService.__status

    @staticmethod
    def stop():
        AuthorizerService.shutdown_dev_server()
        AuthorizerService.__status = 'STOPPED'
        return AuthorizerService.__status
