import json
from sys import stdout, exit

class PowerConsul_Output(object):
    """
    Static methods for writing output and exit codes.
    """
    @staticmethod
    def passing(message):
        try:
            message['state'] = 'passing'
            message['code']  = 0
            stdout.write('{0}\n'.format(json.dumps(message)))
        except:
            stdout.write('{0}\n'.format(message))
        POWERCONSUL.LOG.info(message, method='ensure.passing')
        exit(0)

    @staticmethod
    def warning(message):
        """
        Show a warning message and exit 1.
        """
        try:
            message['state'] = 'warning'
            message['code']  = 1
            stdout.write('{0}\n'.format(json.dumps(message)))
        except:
            stdout.write('{0}\n'.format(message))
        POWERCONSUL.LOG.warning(message, method='ensure.warning')
        exit(1)

    @staticmethod
    def critical(message, code=2):
        """
        Show a critical message and exit 2.
        """
        try:
            message['state'] = 'critical'
            message['code']  = code
            stdout.write('{0}\n'.format(json.dumps(message)))
        except:
            stdout.write('{0}\n'.format(message))
        POWERCONSUL.LOG.critical(message, method='ensure.critical')
        exit(code)
