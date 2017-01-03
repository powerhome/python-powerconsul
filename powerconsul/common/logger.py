import logging
from os import makedirs
from time import strftime
from os.path import isdir, dirname
from json import dumps as json_dumps
from logging import handlers, getLogger, Formatter

class LogFormat(Formatter):
    """
    Custom log format object to use with the Python logging module. Used
    to log the message and return the message string for further use.
    """
    def formatTime(self, record, datefmt):
        """
        Format the record to use a datetime prefix.

        :param record: The log message
        :type record: str
        :param datefmt: The timestamp format
        :type datefmt: str
        :rtype: str
        """
        ct = self.converter(record.created)
        s  = strftime(datefmt, ct)
        return s

class Logger:
    """
    Client logging class. Static constructor is called by the factory method 'create'.
    The log formatter returns the log message as a string value.
    """
    @ staticmethod
    def construct(name, log_file, log_level):
        """
        Construct the logging object. If the log handle already exists don't create
        anything so we don't get duplicated log messages.

        :param name: The class or module name to use in the log message
        :type name: str
        :param log_file: Where to write log messages to
        :type log_file: str
        :rtype: logger
        """

        # Make sure the log directory exists
        log_dir = dirname(log_file)
        if not isdir(log_dir):
            makedirs(log_dir, 0755)

        # Set the logger module name
        logger = getLogger(name)

        # Set the log level
        logger.setLevel(getattr(logging, log_level, 'INFO'))

        # Set the file handler
        lfh = handlers.RotatingFileHandler(log_file, mode='a', maxBytes=10*1024*1024, backupCount=1)
        logger.addHandler(lfh)

        # Set the format
        lfm = LogFormat(fmt='%(asctime)s %(name)s - %(levelname)s: %(message)s', datefmt='%d-%m-%Y %I:%M:%S')
        lfh.setFormatter(lfm)

        # Return the logger
        return getLogger(name)

class PowerConsul_Logger(object):
    """
    Class wrapper for doing preformatted logging.
    """
    def __init__(self, name, service, log_file, log_level):
        self.logger  = Logger.construct(name, log_file, log_level)
        self.service = service

    def _format(self, message, **kwargs):
        if self.service:
            methodStr = '.{0}'.format(kwargs.get('method')) if ('method' in kwargs) else ''
            return 'ConsulService[{0}]{1}: {2}'.format(self.service, methodStr, message)
        return message

    def info(self, message, **kwargs):
        self.logger.info(self._format(message, **kwargs))

    def debug(self, message, **kwargs):
        self.logger.debug(self._format(message, **kwargs))

    def error(self, message, **kwargs):
        self.logger.error(self._format(message, **kwargs))

    def warning(self, message, **kwargs):
        self.logger.warning(self._format(message, **kwargs))

    def critical(self, message, **kwargs):
        self.logger.critical(self._format(message, **kwargs))

        # Optionally abort
        if kwargs.get('die'):
            POWERCONSUL.die(message)

    def exception(self, message, **kwargs):
        self.logger.exception(self._format(message, **kwargs))

        # Optionally abort
        if kwargs.get('die'):
            POWERCONSUL.die(message)

def create(name, service=None, log_file='/var/log/powerconsul.log', log_level='INFO'):
    """
    Factory method used to construct and return a Python logging object.
    """
    return PowerConsul_Logger('powerconsul.{0}'.format(name), service, log_file, log_level)
