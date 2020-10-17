import configparser
import os
import pathlib
import shutil

import pkg_resources

import _shared_mod
from _env_manager import EnvironmentManager


class GlobalConfiguration:
    __config_store = 'config/sptconfig.ini'
    __config = None
    AppSettings = {}
    LogSettings = {}

    @staticmethod
    def _copy_config_to_app_data_path():
        _ = pkg_resources.resource_filename('spt', 'config/sptconfig.ini')
        pathlib.Path(os.path.join(EnvironmentManager.get_app_data_dir(), 'config')).mkdir(parents=True, exist_ok=True)
        destination = os.path.join(EnvironmentManager.get_app_data_dir(), 'config', 'sptconfig.ini')
        if not os.path.exists(destination):
            shutil.copyfile('config/sptconfig.ini', destination)
            shutil.rmtree('config/', ignore_errors=True)
        return destination

    @staticmethod
    def _read_configuration(parser: configparser.ConfigParser):
        if not EnvironmentManager.is_production():
            GlobalConfiguration.__config_store = 'config/sptconfig.ini'
            if not os.path.exists(GlobalConfiguration.__config_store):
                raise _shared_mod.GlobalConfigurationError(GlobalConfiguration.__config_store)

            parser.read(GlobalConfiguration.__config_store)
            return parser

        GlobalConfiguration.__config_store = GlobalConfiguration._copy_config_to_app_data_path()
        if not os.path.exists(GlobalConfiguration.__config_store):
            raise _shared_mod.GlobalConfigurationError(GlobalConfiguration.__config_store)

        parser.read(GlobalConfiguration.__config_store)
        return parser

    # region Intrinsic methos

    @staticmethod
    def initialise():
        config = configparser.ConfigParser()
        config = GlobalConfiguration._read_configuration(config)
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
