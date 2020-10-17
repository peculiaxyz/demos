""""Helper module to read and set environment variable from the .env file"""
import os
import pathlib
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
        env_path = os.getenv('SPT_ENV_PATH', '.env')
        if not pathlib.Path(env_path).exists():
            return False, ''

        with open(env_path, 'r') as envfile:
            contents = envfile.readlines()
            contents = [item for item in contents if str(item).strip() not in (None, '')]
            return True, contents

    @staticmethod
    def _set_from_env_file(settings: typing.List[str]):
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
        invalid_settings = []
        for setting in EnvironmentManager.__required_settings:
            if os.getenv(setting) in (None, ''):
                invalid_settings.append(setting)
        if invalid_settings:
            raise InvalidEnvSettingsError(invalid_settings)

    @staticmethod
    def get_app_data_dir():
        if os.name == 'nt':  # Windows
            app_data_dir = os.getenv('LOCALAPPDATA')
            local_appdata_path = os.path.join(app_data_dir, 'Spt')
            pathlib.Path(local_appdata_path).mkdir(parents=True, exist_ok=True)
            return local_appdata_path

        # Linux, Mac etc
        app_data_dir = os.getenv('HOME')
        local_appdata_path = os.path.join(app_data_dir, 'Spt')
        pathlib.Path(local_appdata_path).mkdir(parents=True, exist_ok=True)
        return local_appdata_path

    @staticmethod
    def is_production():
        EnvironmentManager.Settings = EnvironmentManager.Settings if EnvironmentManager.Settings \
            else EnvironmentManager.initialise()

        is_prod = os.getenv('SPT_PRODUCTION') in ('True', 'TRUE', 'true', '1')
        return is_prod

    @staticmethod
    def initialise():
        env_file_exists, environment_file_settings = EnvironmentManager._load_env_file()
        if env_file_exists:
            EnvironmentManager._set_from_env_file(settings=environment_file_settings)
            EnvironmentManager._verify_settings()
            return EnvironmentManager.Settings

        # Else assume already set , only verify .
        EnvironmentManager._verify_settings()
        return EnvironmentManager.Settings
