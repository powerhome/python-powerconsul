import re
import json
from consul import Consul
from termcolor import colored
from socket import gethostname
from sys import stderr, stdout, exit
from powerconsul.common.config import PowerConsul_Config

class PowerConsul_ServiceBase(object):
    """
    Base object for a Linux service interface.
    """
    def __init__(self):

        # Consul API and PowerConsul configuration
        self.API     = Consul()
        self.CONF    = PowerConsul_Config.parseStatic()

        # All datacenters
        self.dcs     = self.API.catalog.datacenters()

        # Local machine name
        self.host    = gethostname()

        # Module instances
        self.json    = json
        self.re      = re
        self.colored = colored

        # Test API connection
        self._test_api()

    def _test_api(self):
        """
        Make sure API connectivity is healthy.
        """
        try:
            self.API.catalog.datacenters()
        except:
            self.die('Consul API error! Consul agent must be running...')

    def bold(self, message):
        """
        Format a string into bold text.
        """
        return '\033[1m{0}\033[0m'.format(message)

    def status_title(self, title):
        """
        Format a string into bold text.
        """
        return '\n{0}'.format(self.bold(title))

    def exit(self, message):
        """
        Print a message and exit with code 0.
        """
        stdout.write('{0}\n'.format(message))
        exit(0)

    def die(self, message, code=1):
        """
        Print a message and quit the process with an optional exit code.
        """
        stderr.write('{0}\n'.format(message))
        exit(code)
