""""Helper module to read and set environment variable from the .env file"""
import os
import typing


class EnvironmentManager:
    __env_location = '.env'  # Specifies the location of .env file
    Settings = {}

    @staticmethod
    def _remove_export_or_set(setting_name: str):
        """"E.g. If any line in the .env file contains export(for linux) or set(for windows), remove it"""
        parts = setting_name.split(' ')
        if len(parts) == 2:
            return parts[1].strip()
        return parts[0].strip()

    @staticmethod
    def _load_env_file():
        env_path = os.getenv('ENV_PATH') or EnvironmentManager.__env_location
        with open(env_path, 'r') as envfile:
            contents = envfile.readlines()
            contents = [item for item in contents if str(item).strip() not in (None, '')]
            return contents

    @staticmethod
    def _set_environment_variables(settings: typing.List[str]):
        # TODO: what to do if env values are set with qoutes??
        for setting in settings:
            setting_name = setting.split("=")[0].strip()
            setting_name = EnvironmentManager._remove_export_or_set(setting_name)
            setting_value = setting.split("=")[1].strip()
            os.environ[setting_name] = setting_value
            EnvironmentManager.Settings[setting_name] = setting_value

    @staticmethod
    def initialise():
        environment_file_settings = EnvironmentManager._load_env_file()
        EnvironmentManager._set_environment_variables(settings=environment_file_settings)
        return EnvironmentManager.Settings
