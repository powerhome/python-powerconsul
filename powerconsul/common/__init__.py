import __builtin__
import re
import json
from os import geteuid
from consul import Consul
from socket import gethostname
from traceback import print_exc
from importlib import import_module
from sys import stderr, exit, exc_info, stdout

# Power Consul modules
from powerconsul.common.output import PowerConsul_Output
from powerconsul.common.collection import PowerConsul_Collection
from powerconsul.common.action import PowerConsul_Action
from powerconsul.common.cluster import PowerConsul_Cluster

class PowerConsulCommon(object):
    """
    Common class object for shared methods and attributes.
    """
    def __init__(self):

        # Power Consul Extended Objects
        self.HANDLERS   = None
        self.ARGS       = None

        # Consul API / configuration
        self.API        = Consul()
        self.CONFIG     = self._getConfig()

        # PowerHRG environment
        self.ENV        = self.getEnv()
        self.ROLE       = self.getRole()
        self.HOST       = gethostname()

        # Consul service
        self.service    = None

        # Logger
        self.LOG        = None

        # Output / collection generators / action handler / cluster object
        self.OUTPUT     = PowerConsul_Output
        self.COLLECTION = PowerConsul_Collection
        self.ACTION     = PowerConsul_Action
        self.CLUSTER    = PowerConsul_Cluster

    def _getConfig(self):
        """
        Parse the main Consul agent configuration.
        """
        try:
            return json.loads(open('/etc/consul/config.json', 'r').read())
        except Exception as e:
            self.die('Failed to load Consul configuration: {0}'.format(str(e)))

    def getRole(self, hostname=False):
        """
        Extract the server role from the hostname.
        """
        hostname = hostname if hostname else gethostname()
        return re.compile(r'(^[^0-9]*)[0-9]*$').sub(r'\g<1>', hostname.replace('{0}-'.format(self.ENV), ''))

    def getEnv(self, hostname=False):
        """
        Extract the PowerHRG environment from the hostname.
        """
        hostname = hostname if hostname else gethostname()
        return re.compile(r'(^[^-]*)-.*$').sub(r'\g<1>', hostname)

    def getKV(self, key, default=None):
        """
        Perform a key/value lookup.
        """
        index, data = self.API.kv.get(key)

        # Return any value if found or default
        return default if not data else data['Value']

    def bootstrap(self):
        """
        Post initialization bootstrap method.
        """
        self.HANDLERS = import_class('PowerConsulHandlers', 'powerconsul.common.handlers')
        self.ARGS     = import_class('PowerConsulArgs', 'powerconsul.common.args', init=False)

    def ensure_root(self):
        """
        Make sure the current process is being run as root or with sudo privileges.
        """
        if not geteuid() == 0:
            self.die('Power Consul must be run as root or with sudo privileges')

    def extract_attr(self, obj, attrs):
        """
        Extract an attribute from an object by string search filter.
        """
        for k in attrs:
            if hasattr(obj, k):
                if len(attrs) == 1:
                    return getattr(obj, k)
                else:
                    attrs.pop(0)
                    return self.extract_attr(getattr(obj, k), attrs)

    def ensure(self, result, **kwargs):
        """
        Ensure a result is equal to 'value' or is not equal to 'isnot'. Raise an EnsureError otherwise.

        :param result: The result to check
        :type  result: mixed
        :param  value: The value to ensure (equal to)
        :type   value: mixed
        :param  isnot: The value to ensure (not equal to)
        :type   isnot: mixed
        :param  error: The error message to display
        :type   error: str
        :param   code: The exit code to return if error
        :type    code: int
        :rtype: result
        """

        # Code / error / call / log / debug / exception
        code  = kwargs.get('code', 1)
        error = kwargs.get('error', 'An unknown request error has occurred')

        # Cannot specify both value/isnot at the same time
        if ('value' in kwargs) and ('isnot' in kwargs):
            raise Exception('Cannot supply both "value" and "isnot" arguments at the same time')

        # Equal to / not equal to
        value = kwargs.get('value', None)
        isnot = kwargs.get('isnot', None)

        # Negative check (not equal to)
        if 'isnot' in kwargs:
            if result == isnot:
                self.die(error, code)

        # Positive check (equal to)
        if 'value' in kwargs:
            if result != value:
                self.die(error, code)

        # Return the result
        return result

    def die(self, message, code=1):
        """
        Print error message and die.
        """
        stderr.write('{0}\n'.format(message))
        exit(code)

def import_class(cls, mod, init=True, ensure=True, args=[], kwargs={}):
    """
    Import a module, create an instance of a class, and pass optional arguments.

    :param cls:    Class name to import
    :type  cls:    str
    :param module: Class module source
    :type  module: str
    :param init:   Initialize the class object or not
    :type  init:   bool
    :rtype: object
    """
    try:
        if not ensure:
            return None

        # Import the module and class pointer
        mod_obj = import_module(mod)
        mod_cls = getattr(mod_obj, cls)

        # Create the class
        try:
            if init:
                return mod_cls(*args, **kwargs)
            return mod_cls

        # Class creation failed
        except Exception as e:
            stderr.write('Failed to create <{0}>: {1}\n'.format(cls, str(e)))
            print_exc()
            exit(1)

    except Exception as e:
        stderr.write('Failed to import <{0}> from <{1}>: {2}\n'.format(cls, mod, str(e)))
        print_exc()
        exit(1)

def init_powerconsul():
    """
    Method for initializing Power Consul commons.
    """
    if hasattr(__builtin__, 'POWERCONSUL'):
        raise Exception('Power Consul commons already intialized')

    # Set up Power Consul commons
    setattr(__builtin__, 'POWERCONSUL', PowerConsulCommon())

    # Post initialization bootstrap method
    POWERCONSUL.bootstrap()
