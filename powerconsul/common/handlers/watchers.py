import json
from sys import stdin
from select import select
from subprocess import Popen

# Power Consul modules
import powerconsul.common.logger as logger
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

        # Setup the logger
        POWERCONSUL.LOG = logger.create('watch', '/var/log/powerconsul/watch/{0}.log'.format(self.command))

    def _getServices(self):
        """
        Parse incoming Consul JSON data from stdin and extract node services.
        """

        # Must have stdin data
        if not select([stdin,],[],[],0.0)[0]:
            POWERCONSUL.die('Command "powerconsul watch" requires data from STDIN!')

        try:
            consulInput = json.loads(''.join(stdin.readlines()))

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
        services = self._getServices()

        # Trigger the service actions
        for service in services:

            # Service output is empty, so assume this is initial startup
            if service['Output'] == '' or not service['Output']:
                continue
            POWERCONSUL.LOG.info('ConsulService[{0}].trigger: state={1}'.format(service['ServiceID'], state))
            self._trigger(state, service)

    def critical(self):
        """
        Watch services in a critical state.
        """
        self._put('critical')

    def warning(self):
        """
        Watch services in a warning state.
        """
        self._put('warning')
