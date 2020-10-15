""""Helper module to read and set environment variable from the .env file"""
import os
import typing


class MissingEnvSettingsError(Exception):
    def __init__(self, missing_settings: typing.List[str]):
        self.missing_settings = missing_settings

    def __str__(self):
        error = "The following Environment Variables Are Missing.\n"
        error += "%s\n" % self.missing_settings
        error += "Use export <setting-name> for unix or set <setting-name> for windows"
        return error


class InvalidEnvSettingsError(Exception):
    def __init__(self, invalid_settings: typing.List[str]):
        self.invalid_settings = invalid_settings

    def __str__(self):
        error = "The following Environment Settings Are Invalid, Please Correct.\n"
        error += "%s\n" % self.invalid_settings
        return error


class EnvironmentManager:
    __env_location = 'config/.env'
    __required_settings = ['SPT_CLIENT_ID', 'SPT_CLIENT_SECRET', 'SPT_REDIRECT_URI', 'SPT_HOST_IP', 'SPT_HOST_PORT']
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
        return EnvironmentManager.Settings

    @staticmethod
    def _verify_settings():
        required_set = set(EnvironmentManager.__required_settings)
        configured_set = set(EnvironmentManager.Settings)
        missing_settings = list(required_set.difference(configured_set))
        if missing_settings:
            raise MissingEnvSettingsError(missing_settings)

        invalid_settings = []
        for setting in EnvironmentManager.__required_settings:
            if os.getenv(setting) in (None, ''):
                invalid_settings.append(setting)
        if invalid_settings:
            raise InvalidEnvSettingsError(invalid_settings)

    @staticmethod
    def initialise():
        environment_file_settings = EnvironmentManager._load_env_file()
        EnvironmentManager._set_environment_variables(settings=environment_file_settings)
        return EnvironmentManager.Settings
