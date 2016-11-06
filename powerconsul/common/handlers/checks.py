import json
from sys import stdout, exit
from subprocess import Popen, PIPE

# Power Consul modules
from powerconsul.common.args.options import OPTIONS
from powerconsul.common.handlers.base import PowerConsulHandler_Base

class Service(object):
    def __init__(self, nameLocal=None, nameConsul=None):
        self.name        = nameLocal
        self.consulName  = nameConsul

        # Cluster nodes/datacenters
        self.nodes       = None
        self.datacenters = None
        self.allDCs      = POWERCONSUL.API.catalog.datacenters()

        # Should all services in cluster be active
        self.allActive   = False

        # Service attributes
        self.clustered   = self._setCluster(POWERCONSUL.ARGS.get('clustered'))

        # Name local required
        if not self.name:
            POWERCONSUL.die('Local service name requird: powerconsul check service -s <name>')
        self.filterBy    = ''

    def _setGroup(self, group, label):
        """
        Require the presence of both active/standby attributes.
        """
        if not group['active'] or group['standby']:
            return None

        if not group['active'] and group['standby']:
            POWERCONSUL.die('Must specify both active/standby {0} attributes'.format(label))
        return group

    def checkConsul(self, datacenters=None, nodes=None):
        """
        Check if any Consul services are passing.
        """
        statusList = []
        services   = []

        # Generate a list of Consul services from the API
        if datacenters:
            for dc in datacenters:
                services + POWERCONSUL.API.health.service(self.consulName, dc=dc)[1]
        else:
            services = POWERCONSUL.API.health.service(self.consulName)[1]

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
                POWERCONSUL.LOG.info('Discovered cluster node [{0}]: env={1}, role={2}, service={3}, status={4}'.format(
                    node, nodeEnv, nodeRole, self.consulName, checks['Status']
                ))

        # Return the status list
        return statusList

    def activePassing(self):
        """
        If the node is a standby, use this to check if the nodes in the active
        datacenter for this service are passing/healthy.
        """
        consulService = POWERCONSUL.ARGS.get('consulservice')

        # Consul service name required
        if not self.consulName:
            POWERCONSUL.die('Consul service name required for clustered active/standby checks!')

        # Store flag if any active services are passing
        anyPassing = False

        # By datacenter
        if self.datacenters:
            for status in self.checkConsul(datacenters=self.allDCs):
                if anyPassing:
                    continue
                anyPassing = status

        # By nodes
        if self.nodes:
            for status in self.checkConsul(consulService, datacenters=self.allDCs, nodes=objects):
                if anyPassing:
                    continue
                anyPassing = status

        # Return the flag that shows in any active services are passing
        return anyPassing

    def _setCluster(self, state):
        """
        Set cluster attributes.
        """
        if not state:
            return False

        # Cluster by node
        self.nodes   = self._setGroup({
            'active': POWERCONSUL.ARGS.get('activenodes', default='').split(','),
            'standby': POWERCONSUL.ARGS.get('standbynodes', default='').split(','),
            'local': POWERCONSUL.HOST
        }, 'nodes')

        # Cluster by datacenter
        self.datacenters = self._setGroup({
            'active': POWERCONSUL.ARGS.get('activedc'),
            'standby': POWERCONSUL.ARGS.get('standbydc'),
            'local': POWERCONSUL.CONFIG['datacenter']
        }, 'datacenters')

        # Cannot cluster by both
        if self.datacenters and self.nodes:
            POWERCONSUL.die('Active/standby datacenters and nodes options are mutually exclusive!')

        # Assume all active in cluster
        if not self.datacenters and not self.nodes:
            self.allActive = True

    def byDatacenter(self):
        """
        Ensure a clustered service state by datacenter.
        """
        if not self.datacenters:
            return None
        self.filterBy = '_dc'

        # Local server's datacenter must match either active or standby
        if not self.datacenters.local in [self.datacenters.active, self.datacenters.standby]:
            POWERCONSUL.die('Local server\'s datacenter [{0}] must be either the active [{1}] or standby [{2}] datacenter!'.format(
                self.datacenters.local,
                self.datacenters.active,
                self.datacenters.standby
            ))

        # Log the service check
        POWERCONSUL.LOG.info('Clustered service [{0}@{1}]: active[{2}]/standby[{3}] datacenters'.format(
            self.name,
            self.datacenters.local,
            self.datacenters.active,
            self.datacenters.standby
        ))

        """ NODE == ACTIVE """
        if self.datacenters.local == self.datacenters.active:
            self.ensure(service, clustered=True)

        """ NODE == STANDBY """
        if self.datacenters.local == self.datacenters.standby:

            """ ACTIVE_DC == PASSING """
            if self.activePassing():
                self.ensure(expects=False, clustered=True, active=False)

            """ ACTIVE_DC == CRITICAL """
            self.ensure(service, expects=True, clustered=True, active=False)

    def byNodes(self):
        """
        Ensure a clustered service state by nodes.
        """
        if not self.nodes:
            return False
        self.filterBy = '_node'

        # Local node must be in either active or standby nodes list
        if not self.nodes.local in (self.nodes.active + self.nodes.standby):
            POWERCONSUL.die('Local node address [{0}] must be in either active {1} or standby {2} node list!'.format(
                self.nodes.local,
                self.nodes.active,
                self.nodes.standby
            ))

        # Log the service check
        POWERCONSUL.LOG.info('Clustered service [{0}]: active[{1}]/standby[{2}] nodes'.format(
            self.name,
            ','.join(self.nodes.active),
            ','.join(self.nodes.standby)
        ))

        """ NODE == ACTIVE """
        if self.nodes.local in self.nodes.active:
            self.ensure(service, clustered=True)

        """ NODE == STANDBY """
        if self.nodes.local in self.nodes.standby:

            """ ACTIVE_DC == PASSING """
            if self.activePassing():
                self.ensure(expects=False, clustered=True, active=False)

            """ ACTIVE_DC == CRITICAL """
            self.ensure(expects=True, clustered=True, active=False)

    def running(self):
        """
        Check if a service is running or not.
        """
        proc     = Popen(['/usr/bin/env', 'service', self.name, 'status'], stdout=PIPE, stderr=PIPE)
        out, err = proc.communicate()

        # Failed to get status
        if proc.returncode != 0:
            POWERCONSUL.die('Failed to determine status for [{0}]: {1}'.format(self.name, err.rstrip()))

        # Service is running
        for rstr in ['is running', 'start/running']:
            if rstr in out.rstrip():
                return True
        return False

    def ensure(self, expects=True, clustered=False, active=True):
        """
        Ensure a specific service state.
        """
        running  = self.running()
        msgAttrs = [
            'service={0}'.format(self.name),
            'running={0}'.format('yes' if running else 'no'),
            'expects={0}'.format('running' if expects else 'stopped'),
            'clustered={0}'.format('yes' if clustered else 'no')
        ]

        # If running in a cluster, append datacenter attribute to message
        if clustered:
            msgAttrs.append('active{0}={1}'.format(self.filterBy, 'yes' if active else 'no'))

        # Service should be running
        if expects == True:
            if running:
                POWERCONSUL.SHOW.passing('SERVICE OK: {0}'.format(', '.join(msgAttrs)))
            POWERCONSUL.SHOW.critical('SERVICE CRITICAL: {0}'.format(', '.join(msgAttrs)))

        # Service should be stopped
        if expects == False:
            if not running:
                POWERCONSUL.SHOW.passing('SERVICE OK: {0}'.format(', '.join(msgAttrs)))
            POWERCONSUL.SHOW.critical('SERVICE CRITICAL: {0}'.format(', '.join(msgAttrs)))

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

    def service(self):
        """
        Check a service state.
        """
        service = Service(POWERCONSUL.ARGS.get('service'), POWERCONSUL.ARGS.get('consulservice'))

        """ STANDALONE """
        if not service.clustered:
            service.ensure()

        """ CLUSTERED """

        # All services active
        if service.allActive:
            service.ensure(clustered=True)

        """ ACTIVE/STANDBY """
        service.byDatacenter()
        service.byNodes()
