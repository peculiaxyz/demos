import configparser
import os

import _shared_mod


class GlobalConfiguration:
    __config_store = os.getenv('SPT_CONFIG_STORE') or 'config/appconfig.ini'
    __config = None
    AppSettings = {}
    LogSettings = {}

    # region Intrinsic methos

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
    def save_configuration():
        config = GlobalConfiguration.get_configuration()
        with open(GlobalConfiguration.__config_store, 'w') as configfl:
            config.write(configfl)
            return config

    # endregion

    # region Convenience methoss
    @staticmethod
    def get_app_name():
        config = GlobalConfiguration.get_configuration()
        return config.get('APP_SETTINGS', 'APP_NAME')

    # endregion
