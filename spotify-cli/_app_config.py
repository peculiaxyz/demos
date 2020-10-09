import json
import os


class GlobalConfiguration:
    __config_store = 'appconfig.json'
    __json_config = {}

    @staticmethod
    def initialise():
        with open(os.getenv('GLOBAL_CONFIGURATION', GlobalConfiguration.__config_store)) as config:
            GlobalConfiguration.__json_config = json.load(config)
            return GlobalConfiguration.__json_config

    @staticmethod
    def get_configuration():
        if GlobalConfiguration.__json_config:
            return GlobalConfiguration.__json_config
        return GlobalConfiguration.initialise()

    @staticmethod
    def get_app_name():
        config = GlobalConfiguration.get_configuration()
        return config['APP_NAME']
