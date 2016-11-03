import json
from sys import stdin
from select import select
from subprocess import Popen

# Power Consul modules
from powerconsul.common.args.options import OPTIONS
from powerconsul.common.handlers.base import PowerConsulHandler_Base

class PowerConsulHandler_Watchers(PowerConsulHandler_Base):
    """
    Class object for managing Consul service state watchers.
    """
    id      = 'watch'

    # Command description
    desc    = {
        "title": "Power Consul Watchers",
        "summary": "Watch Consul health checks",
        "usage": "powerconsul watch [state] [options]"
    }

    # Supported options
    options = [] + OPTIONS

    # Supported states
    commands = {
        "critical": {
            "help": "Watch for services in a critical state."
        },
        "warning": {
            "help": "Watch for services in a warning state."
        }
    }

    def __init__(self):
        super(PowerConsulHandler_Watchers, self).__init__(self.id)

        # Node's services keypath
        self.keypath = 'services/{0}/{1}'.format(POWERCONSUL.HOST, POWERCONSUL.ARGS.get('command'))

    def _get_services(self):
        """
        Parse incoming Consul JSON data from stdin and extract environment services.
        """

        # Must have stdin data
        if not select([stdin,],[],[],0.0)[0]:
            POWERCONSUL.die('Command "powerconsul watch" requires data from STDIN!')

        try:
            consulInput = json.loads(''.join(stdin.readlines()))

            # Extract environment services
            envJSON     = []
            for service in consulInput:
                nodeAttrs = service['Node'].split('-')
                if nodeAttrs[0] == POWERCONSUL.ENV:
                    envJSON.append(service)
            return envJSON

        # Failed to retrieve stdin
        except Exception as e:
            POWERCONSUL.die('Failed to parse Consul input: {0}'.format(str(e)))

    def _trigger(self, action):
        """
        Parent method for running a trigger script.
        """
        proc = Popen(['/usr/bin/env', 'powerconsul', 'trigger', action])
        proc.call()

    def _put(self):
        """
        Private method for putting service states.
        """
        POWERCONSUL.API.kv.put(self.keypath, json.dumps(self._get_services()))

        # Test fire trigger
        self._trigger('start')

    def critical(self):
        """
        Return a listing of datastores.
        """
        self._put()

    def warning(self):
        """
        Return a listing of virtual machines.
        """
        self._put()
