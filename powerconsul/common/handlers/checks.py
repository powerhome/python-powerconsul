import json
from sys import stdout, exit
from subprocess import Popen, PIPE

# Power Consul modules
from powerconsul.common.args.options import OPTIONS
from powerconsul.common.handlers.base import PowerConsulHandler_Base

class PowerConsulHandler_Checks(PowerConsulHandler_Base):
    """
    Class object for managing custom Consul checks.
    """
    id      = 'check'

    # Command description
    desc    = {
        "title": "Power Consul Triggers",
        "summary": "Trigger events on service state changes.",
        "usage": "powerconsul trigger [action] [options]"
    }

    # Supported options
    options = [
        {
            "short": "s",
            "long": "service",
            "help": "The name of the local service to check the status of.",
            "action": "store",
            "required": True
        },
        {
            "short": "S",
            "long": "consulservice",
            "help": "The name of the Consul service to check against.",
            "action": "store"
        },
        {
            "short": "c",
            "long": "clustered",
            "help": "Is this service part of a cluster or not (default=False)?",
            "action": "store_true"
        },
        {
            "short": "d",
            "long": "standbydc",
            "help": "The standby datacenter for this service.",
            "action": "store"
        },
        {
            "short": "D",
            "long": "activedc",
            "help": "The active datacenter for this service.",
            "action": "store"
        }
    ] + OPTIONS

    # Supported actions
    commands = {
        "service": {
            "help": "Check a service running on the system."
        }
    }

    def __init__(self):
        super(PowerConsulHandler_Checks, self).__init__(self.id)

    def isPassing(self, message):
        """
        Show a passing message and exit 0.
        """
        stdout.write('{0}\n'.format(message))
        exit(0)

    def isWarning(self, message):
        """
        Show a warning message and exit 1.
        """
        stdout.write('{0}\n'.format(message))
        exit(1)

    def isCritical(self, message):
        """
        Show a critical message and exit 2.
        """
        stdout.write('{0}\n'.format(message))
        exit(2)

    def isRunning(self, service):
        """
        Check if a service is running or not.
        """
        proc     = Popen(['/usr/bin/env', 'service', service, 'status'], stdout=PIPE, stderr=PIPE)
        out, err = proc.communicate()
        status   = out[0]

        # Unrecognized service
        if proc.returncode != 0:
            POWERCONSUL.die('Failed to determine status for [{0}]: {1}'.format(service, err.rstrip()))

        # Service is running
        for runningStr in ['is running', 'start/running']:
            if runningStr in status:
                return True
        return False

    def checkRunning(self, service, expects=True, clustered=False, active=True):
        """
        Check if the service is running
        """
        running  = self.isRunning(service)
        msgAttrs = [
            'service={0}'.format(service),
            'running={0}'.format('yes' if running else 'no'),
            'expects={0}'.format('running' if expects else 'stopped'),
            'clustered={0}'.format('yes' if clustered else 'no')
        ]

        # If running in a cluster, append datacenter attribute to message
        if clustered:
            msgAttrs.append('active_dc={0}'.format('yes' if active else 'no'))

        # Service should be running
        if expects == True:
            if running:
                self.isPassing('SERVICE OK: {0}'.format(', '.join(msgAttrs)))
            self.isCritical('SERVICE CRITICAL: {0}'.format(', '.join(msgAttrs)))

        # Service should be stopped
        if expects == False:
            if not running:
                self.isPassing('SERVICE OK: {0}'.format(', '.join(msgAttrs)))
            self.isCritical('SERVICE CRITICAL: {0}'.format(', '.join(msgAttrs)))

    def activePassing(self, service, datacenter):
        """
        If the node is a standby, use this to check if the nodes in the active
        datacenter for this service are passing/healthy.
        """
        consulService = POWERCONSUL.ARGS.get('consulservice')

        # Consul service name required
        if not consulService:
            POWERCONSUL.die('Consul service name required for clustered active/standby checks!')

        # Store flag if any active services are passing
        anyPassing = False

        # Get active datacenter services
        for serviceActive in POWERCONSUL.API.health.service(consulService, dc=datacenter)[1]:

            # Node / environment / role
            node     = service['Node']
            nodeEnv  = POWERCONSUL.getEnv(hostname=node)
            nodeRole = POWERCONSUL.getRole(hostname=node)
            checks   = service['Checks'][1]

            # Node must be in the same environment/role
            if (nodeEnv == POWERCONSUL.ENV) and (nodeRole == POWERCONSUL.ROLE):
                anyPassing = True if checks['Status'] == 'passing' else False

        # Return the flag that shows in any active services are passing
        return anyPassing

    def service(self):
        """
        Check a service state.
        """
        service = POWERCONSUL.ARGS.get('service')

        """ STANDALONE """

        # Standalone service
        if not POWERCONSUL.ARGS.get('clustered'):
            self.checkRunning(service)

        """ CLUSTERED """

        # Active/standby datacenters
        activeDC  = POWERCONSUL.ARGS.get('activedc')
        standbyDC = POWERCONSUL.ARGS.get('standbydc')
        localDC   = POWERCONSUL.CONFIG['datacenter']

        # All services active
        if not activeDC and not standbyDC:
            self.checkRunning(service, clustered=True)

        """ ACTIVE/STANDBY """

        # Both active/standby datacenters must be set
        if not activeDC or not standbyDC:
            POWERCONSUL.die('Must supply both active/standby datacenter(s) if specifying either!')

        # Local server's datacenter must match either active or standby
        if not localDC in [activeDC, standbyDC]:
            POWERCONSUL.die('Local server\'s datacenter [{0}] must be either the active [{1}] or standby [{2}] datacenter!'.format(
                localDC,
                activeDC,
                standbyDC
            ))

        """ NODE == ACTIVE """
        if localDC == activeDC:

            # Active datacenter nodes should always have the service runnnig
            self.checkRunning(service, clustered=True)

        """ NODE == STANDBY """
        if localDC == standbyDC:

            """ ACTIVE_DC == PASSING """
            if self.activePassing(service, activeDC):
                self.checkRunning(service, expects=False, clustered=True, active=False)

            """ ACTIVE_DC == CRITICAL """
            self.checkRunning(service, expects=True, clustered=True, active=False)
