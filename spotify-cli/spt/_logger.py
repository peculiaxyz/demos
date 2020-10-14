"""Handlers logging to console, logfiles etc."""
__all__ = ['default_logger', 'ConsoleColorsEnum']

import logging
import os
import pathlib
import sys
import traceback
from datetime import datetime
from logging import DEBUG, FileHandler, INFO, StreamHandler


class ConsoleColorsEnum:
    PURPLE = '\033[95m'
    BLUE = '\033[94m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    RICH_TEXT_END = '\033[0m'


# region Logging Configuration

def _get_log_file():
    """Cretae the logfile if it does not exist already"""
    pathlib.Path('logs').mkdir(parents=True, exist_ok=True)

    todays_date = datetime.today().strftime("%Y_%m_%d")
    logfilename = 'spt_%s.log' % todays_date
    logfilepath = os.path.join('logs', logfilename)

    if not os.path.exists(logfilepath):
        with open(logfilepath, 'w') as logfl:
            pass
    return logfilepath


default_formatter = logging.Formatter('%(asctime)s - [ %(levelname)s ]:  %(message)s')
detailed_formatter = \
    logging.Formatter('%(asctime)s - %(levelname)s [ %(module)s.%(funcName)s ] %(lineno)d:  %(message)s')
server_formatter = \
    logging.Formatter('%(asctime)s | %(processName)s {%(process)d} | | %(threadName)s {%(thread)d} | -'
                      ' %(levelname)s [ %(module)s.%(funcName)s ] %(lineno)d:  %(message)s')

default_logger = logging.getLogger('Spotify Logger')
default_logger.setLevel(logging.DEBUG)

# Create console handler for logging for minimal app info logs
console_handler = StreamHandler(sys.stdout)
console_handler.setLevel(INFO)
console_handler.setFormatter(default_formatter)
default_logger.addHandler(console_handler)

# Create a file handler for to store more detailed logs
filehandler = FileHandler(filename=_get_log_file())
filehandler.setLevel(DEBUG)
filehandler.setFormatter(detailed_formatter)
default_logger.addHandler(filehandler)


def loginfo(message, *args, **kwargs):
    print(ConsoleColorsEnum.GREEN)
    default_logger.info(message, *args, **kwargs)
    print(ConsoleColorsEnum.RICH_TEXT_END)


def logdebug(message):
    default_logger.debug(message)


def log_debug(message, color=ConsoleColorsEnum.PURPLE):
    print(color)
    logdebug(message)
    print(ConsoleColorsEnum.RICH_TEXT_END)


def logwarn(message):
    print(ConsoleColorsEnum.YELLOW)
    default_logger.warning(message)
    print(ConsoleColorsEnum.RICH_TEXT_END)


def logerror(message):
    print(ConsoleColorsEnum.RED)
    default_logger.error(message)
    print(ConsoleColorsEnum.RICH_TEXT_END)


def logcritical(message):
    print(ConsoleColorsEnum.RED)
    default_logger.error(message)
    print(ConsoleColorsEnum.RICH_TEXT_END)


# endregion


# region Logging Decorators

def catch_errors(func):
    def wrapper(*args, **kwargs):
        has_errors = False
        try:
            logdebug('\n%s called with args=%s, kwargs=%s' % (func.__name__, args, kwargs))
            result = func(*args, **kwargs)
            logdebug('%s done. Return value=%s' % (func.__name__, result))
            return result
        except Exception as ex:
            logerror(ex)
            logerror(traceback.format_exc())
            has_errors = True
            return -99
        finally:
            if has_errors:
                logwarn('%s ended unexpectedly. See logs above.' % func.__name__)

    return wrapper


def trace_call(func):
    """Trace a function call"""

    def wrapper(*args, **kwargs):
        logdebug('%s called with args=%s, kwargs=%s' % (func.__name__, args, kwargs))
        result = func(*args, **kwargs)
        logdebug('%s done. Return value=%s' % (func.__name__, result))
        return result

    return wrapper

# endregion)
