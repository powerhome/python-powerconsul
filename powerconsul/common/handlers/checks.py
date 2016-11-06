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
        },
        {
            "short": "n",
            "long": "standbynodes",
            "help": "A list of standby node hostnames: i.e., node1,node2",
            "action": "store"
        },
        {
            "short": "N",
            "long": "activenodes",
            "help": "A list of active node hostnames: i.e., node3,node4",
            "action": "store"
        },
        {
            "short": "A",
            "long": "datacenters",
            "help": "A list of all available datacenters.",
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

        # A list of all available datacenters
        self.datacenters = self._getDatacenters()

    def _getDatacenters(self):
        """
        Get a list of all datacenters if provided.
        """
        dcArg = POWERCONSUL.ARGS.get('datacenters')
        if dcArg:
            return dcArg.split(',')
        return None

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

        # Unrecognized service
        if proc.returncode != 0:
            POWERCONSUL.die('Failed to determine status for [{0}]: {1}'.format(service, err.rstrip()))

        # Service is running
        for runningStr in ['is running', 'start/running']:
            if runningStr in out.rstrip():
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

    def checkConsulServices(self, consulservice, datacenters=None, nodes=None):
        """
        Check if any Consul services are passing.
        """
        statusList = []
        services   = []

        # Generate a list of Consul services from the API
        if datacenters:
            for dc in datacenters:
                services + POWERCONSUL.API.health.service(consulservice, dc=dc)[1]
        else:
            services = POWERCONSUL.API.health.service(consulservice)[1]

        # Process services
        for service in services:

            # Node / environment / role
            node     = service['Node']['Node']
            nodeEnv  = POWERCONSUL.getEnv(hostname=node)
            nodeRole = POWERCONSUL.getRole(hostname=node)
            checks   = service['Checks'][1]

            # If provided a node filter list
            if nodes and not node in nodes:
                continue

            # Node must be in the same environment/role
            if (nodeEnv == POWERCONSUL.ENV) and (nodeRole == POWERCONSUL.ROLE):
                statusList.append(True if checks['Status'] == 'passing' else False)

        # Return the status list
        return statusList

    def activePassing(self, service, objects):
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

        # Objects is a string, assume datacenter
        if isinstance(objects, str):
            datacenter = objects

            # Get active datacenter services
            for status in self.checkConsulServices(consulService, dc=[datacenters]):
                if anyPassing:
                    continue
                anyPassing = status

        # Objects is a list, assume nodes
        if isinstance(objects, list):
            for status in self.checkConsulServices(consulService, dc=self.datacenters, nodes=objects):
                if anyPassing:
                    continue
                anyPassing = status

        # Return the flag that shows in any active services are passing
        return anyPassing

    def service(self):
        """
        Check a service state.
        """
        service = POWERCONSUL.ARGS.get('service')

        # Service name required
        if not service:
            POWERCONSUL.die('Must specify a service name: powerconsul check service -s <name>')

        """ STANDALONE """

        # Standalone service
        if not POWERCONSUL.ARGS.get('clustered'):
            self.checkRunning(service)

        """ CLUSTERED """

        # Active/standby nodes
        activeNodes  = POWERCONSUL.ARGS.get('activenodes', default='').split(',')
        standbyNodes = POWERCONSUL.ARGS.get('standbynodes', default='').split(',')
        localNode    = POWERCONSUL.HOST

        # Active/standby datacenters
        activeDC     = POWERCONSUL.ARGS.get('activedc')
        standbyDC    = POWERCONSUL.ARGS.get('standbydc')
        localDC      = POWERCONSUL.CONFIG['datacenter']

        # All services active
        if not (activeDC and not standbyDC) and not (activeNodes and not standbyNodes):
            self.checkRunning(service, clustered=True)

        """ ACTIVE/STANDBY """

        # Active/standby datacenter and node options mutually exclusive
        if (activeDC or standbyDC) and (activeNodes or standbyNodes):
            POWERCONSUL.die('Active/standby datacenter and node options are mutually exclusive!')

        # Active/standby nodes or datacenters
        checkDC   = True if (activeDC and standbyDC) else False
        checkNode = True if (activeNodes and standbyNodes) else False

        # Both options must be set for either node or datacenter checks
        if not checkDC and not checkNode:
            POWERCONSUL.die('Must supply both active/standby datacenter(s)/node(s) if specifying either!')

        """ DATACENTER CHECK """
        if checkDC:

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

        """ NODE CHECK """
        if checkNode:
            allNodes = activeNodes + standbyNodes

            # Local node must be in either active or standby nodes list
            if not localNode in allNodes:
                POWERCONSUL.die('Local node address [{0}] must be in either active {1} or standby {2} node list!'.format(
                    localNode,
                    activeNodes,
                    standbyNodes
                ))

            """ NODE == ACTIVE """
            if localNode in activeNodes:

                # Active datacenter nodes should always have the service runnnig
                self.checkRunning(service, clustered=True)

            """ NODE == STANDBY """
            if localNode in standbyNodes:

                """ ACTIVE_DC == PASSING """
                if self.activePassing(service, activeNodes):
                    self.checkRunning(service, expects=False, clustered=True, active=False)

                """ ACTIVE_DC == CRITICAL """
                self.checkRunning(service, expects=True, clustered=True, active=False)
