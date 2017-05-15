try:
    import __builtin__ as builtins
except:
    import builtins

import re
import json
from os import geteuid
from consul import Consul
from socket import gethostname
from traceback import print_exc
from importlib import import_module
from sys import stderr, exit, stdout

# Power Consul modules
from powerconsul.kvdb import PowerConsul_KVDB
from powerconsul.common.output import PowerConsul_Output
from powerconsul.common.collection import PowerConsul_Collection
from powerconsul.common.action import PowerConsul_Action
from powerconsul.common.cluster import PowerConsul_Cluster
from powerconsul.common.config import PowerConsul_Config

class PowerConsulCommon(object):
    """
    Common class object for shared methods and attributes.
    """
    def __init__(self, args):

        # Power Consul Extended Objects
        self.HANDLERS    = None
        self.ARGS        = None
        self._args       = args

        # Consul API / KV database / configuration
        self.API         = Consul()
        self.KV          = PowerConsul_KVDB(put_local=False)
        self.CONFIG      = PowerConsul_Config

        # Store the host name
        self.HOST        = gethostname()

        # Consul service
        self.service     = None

        # Logger
        self.LOG         = None

        # Output / collection generators / action handler / cluster object
        self.OUTPUT      = PowerConsul_Output
        self.COLLECTION  = PowerConsul_Collection
        self.ACTION      = PowerConsul_Action
        self.CLUSTER     = PowerConsul_Cluster

        # Consul attribute shortcuts
        self.datacenters = self.API.catalog.datacenters()

    def getKV(self, key, default=None):
        """
        Perform a key/value lookup.
        """
        index, data = self.API.kv.get(key)

        # Return any value if found or default
        return default if not data else data['Value']

    def putKV(self, key, value, all_dcs=False):
        """
        Create or update a KV datastore value.
        """
        try:
            data = value if not isinstance(value, (dict, list)) else json.dumps(value)

            # Post to all datacenters
            if all_dcs:
                self.KV.put(key, data)

            # Local datacenter only
            else:
                if not self.API.kv.put(key, data):
                    POWERCONSUL.LOG.critical('Failed to create update KV for "{0}": API call failed!'.format(key), die=True)
                POWERCONSUL.LOG.info('Updated KV data for "{0}" -> {1}'.format(key, str(data)))
        except Exception as e:
            POWERCONSUL.LOG.critical('Failed to create update KV for "{0}": {1}'.format(key, str(e)), die=True)

    def getServiceHealth(self, **kwargs):
        """
        Get service health from Consul API.
        """
        services    = []
        service     = kwargs.get('service', self.service)
        datacenters = kwargs.get('datacenters')
        srvFilter   = POWERCONSUL.CONFIG.get('local', 'serviceFilter')

        # Generate a list of Consul services from the API
        if datacenters:
            for dc in datacenters:
                services = services + self.API.health.service(service, dc=dc)[1]
        else:
            services = self.API.health.service(service)[1]

        # Mapped services
        mappedServices = []

        # Process raw services
        for srv in services:
            node   = srv['Node']['Node']
            checks = srv['Checks'][1]

            # Service regex filter
            if srvFilter and not re.compile(srvFilter).match(node):
                POWERCONSUL.LOG.debug('skip -> {0} != \'{1}\''.format(node, srvFilter), method='getServiceHealth')
                continue

            # Map the service
            mappedServices.append({
                'node': node,
                'status': checks['Status']
            })

        # Log service map
        POWERCONSUL.LOG.info('mappedServices={0}'.format(json.dumps(mappedServices)), method='getServiceHealth')

        # Return mapped services
        return mappedServices

    def parseJSON(self, data, error='Failed to parse JSON'):
        """
        Parse a JSON string.
        """
        try:
            return json.loads(data)
        except Exception as e:
            POWERCONSUL.die('{0}: {1}'.format(error, str(e)))

    def bootstrap(self):
        """
        Post initialization bootstrap method.
        """
        self.HANDLERS = import_class('PowerConsulHandlers', 'powerconsul.common.handlers')
        self.ARGS     = import_class('PowerConsulArgs', 'powerconsul.common.args', init=False)

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

def iterateDict(dictObject):
    """
    Wrapper method for iterating a dictionary for Python 2/3 compatibility.
    """

    # Python 2.x
    if hasattr(dictObject, 'iteritems'):
        return dictObject.iteritems()

    # Python 3.x
    else:
        return dictObject.items()

def init_powerconsul(args):
    """
    Method for initializing Power Consul commons.
    """
    if hasattr(builtins, 'POWERCONSUL'):
        raise Exception('Power Consul commons already intialized')

    # Iterate dictionary method for Python2/3 compatibility
    setattr(builtins, 'iterdict', iterateDict)

    # Set up Power Consul commons
    setattr(builtins, 'POWERCONSUL', PowerConsulCommon(args))

    # Post initialization bootstrap method
    POWERCONSUL.bootstrap()
