import configparser
import os

import _shared_mod


class GlobalConfiguration:
    __config_store = 'appconfig.ini'
    __config = None
    AppSettings = {}
    LogSettings = {}

    @staticmethod
    def initialise():
        if not os.path.exists(GlobalConfiguration.__config_store):
            raise _shared_mod.GlobalConfigurationError(GlobalConfiguration.__config_store)

        config = configparser.ConfigParser()
        config.read(GlobalConfiguration.__config_store)
        GlobalConfiguration.__config = config
        GlobalConfiguration.AppSettings = config['APP_SETTINGS']
        GlobalConfiguration.AppSettings = config['LOG_SETTINGS']
        return GlobalConfiguration.__config

    @staticmethod
    def get_configuration():
        if GlobalConfiguration.__config:
            return GlobalConfiguration.__config
        return GlobalConfiguration.initialise()

    @staticmethod
    def get_app_name():
        return GlobalConfiguration.AppSettings.get('APP_NAME')
