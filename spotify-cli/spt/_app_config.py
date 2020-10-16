import configparser
import os

import pkg_resources

import _shared_mod
from _env_manager import EnvironmentManager

PROD_DATA_PATH = pkg_resources.resource_filename('spt', 'config/')
PROD_CONFIG_FILE = os.path.join(PROD_DATA_PATH, 'sptconfig.ini')


class GlobalConfiguration:
    __config_store = 'config/sptconfig.ini' if not EnvironmentManager.is_production() else PROD_CONFIG_FILE
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
