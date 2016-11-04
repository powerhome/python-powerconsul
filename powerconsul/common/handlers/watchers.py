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

    def _get_services(self):
        """
        Parse incoming Consul JSON data from stdin and extract node services.
        """

        # Must have stdin data
        if not select([stdin,],[],[],0.0)[0]:
            POWERCONSUL.die('Command "powerconsul watch" requires data from STDIN!')

        try:
            consulInput = json.loads(''.join(stdin.readlines()))
            POWERCONSUL.LOG.info(json.dumps(consulInput))

            # Extract node services
            nodeJSON    = []
            for service in consulInput:
                if service['Node'] == POWERCONSUL.HOST:
                    nodeJSON.append(service)
            return nodeJSON

        # Failed to retrieve stdin
        except Exception as e:
            POWERCONSUL.die('Failed to parse Consul input: {0}'.format(str(e)))

    def _trigger(self, state, service):
        """
        Parent method for running a trigger script.
        """
        proc = Popen(['/usr/bin/env', 'powerconsul', 'trigger', state, '-s', '{0}'.format(json.dumps(service))])
        proc.communicate()

    def _put(self, state):
        """
        Private method for putting service states.
        """
        services = self._get_services()

        # Trigger the service actions
        for service in services:
            POWERCONSUL.LOG.info('Service action triggered: {0}'.format(str(service)))
            self._trigger(state, service)

    def critical(self):
        """
        Return a listing of datastores.
        """
        self._put('critical')

    def warning(self):
        """
        Return a listing of virtual machines.
        """
        self._put('warning')
