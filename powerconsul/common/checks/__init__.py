import json

class Check_Base(object):
    """
    Base class for a checked resource.
    """
    def __init__(self, resource):
        self.resource    = None
        self.datacenters = None
        self.nodes       = None
        self.allActive   = False
        self.clustered   = self.setCluster(POWERCONSUL.ARGS.get('clustered'))
        self.filterStr   = ''

        # Resource name
        self.name        = None

    def mapList(self, listStr):
        if not listStr:
            return None
        return listStr.split(',')

    def setGroup(self, group, label):
        """
        Require the presence of both active/standby attributes.
        """

        # Cluster group mapping
        class Group(object):
            def __init__(self, **kwargs):
                for k,v in kwargs.iteritems():
                    setattr(self, k, v)

        # Group is disabled
        if not group['active'] and not group['standby']:
            return Group(**group)

        # Active/standby attributes required if either are set
        if not group['active'] or not group['standby']:
            POWERCONSUL.die('Must specify both active/standby {0} attributes'.format(label))

        # Enabled group
        group = Group(**group)
        group.enabled = True
        return group

    def setCluster(self, state):
        """
        Set cluster attributes.
        """
        if not state:
            return False

        # Cluster by node
        self.nodes   = self.setGroup({
            'active': self.mapList(POWERCONSUL.ARGS.get('activenodes')),
            'standby': self.mapList(POWERCONSUL.ARGS.get('standbynodes')),
            'local': POWERCONSUL.HOST,
            'enabled': False
        }, 'nodes')

        # Cluster by datacenter
        self.datacenters = self.setGroup({
            'active': POWERCONSUL.ARGS.get('activedc'),
            'standby': POWERCONSUL.ARGS.get('standbydc'),
            'local': POWERCONSUL.CONFIG['datacenter'],
            'all': POWERCONSUL.API.catalog.datacenters(),
            'enabled': False
        }, 'datacenters')

        # Cannot cluster by both
        if self.datacenters.enabled and self.nodes.enabled:
            POWERCONSUL.die('Active/standby datacenters and nodes options are mutually exclusive!')

        # Datacenter validation
        if self.datacenters.enabled:
            self.filterStr = '_dc'

            # Supplied datacenters must be valid
            for dcType in ['active', 'standby', 'local']:
                if not getattr(self.datacenters, dcType) in self.datacenters.all:
                    POWERCONSUL.die('{0} datacenter [{1}] not valid, available datacenters: {2}'.format(
                        dcType.capitalize(),
                        getattr(self.datacenters, dcType),
                        json.dumps(self.datacenters.all)
                    ))

            # Local server's datacenter must match either active or standby
            if not self.datacenters.local in [self.datacenters.active, self.datacenters.standby]:
                POWERCONSUL.die('Local server\'s datacenter [{0}] must be either the active [{1}] or standby [{2}] datacenter!'.format(
                    self.datacenters.local,
                    self.datacenters.active,
                    self.datacenters.standby
                ))

        # Nodes validation
        if self.nodes.enabled:
            self.filterStr = '_node'

            # Local node must be in either active or standby nodes list
            if not self.nodes.local in (self.nodes.active + self.nodes.standby):
                POWERCONSUL.die('Local node address [{0}] must be in either active {1} or standby {2} node list!'.format(
                    self.nodes.local,
                    json.dumps(self.nodes.active),
                    json.dumps(self.nodes.standby)
                ))

        # Assume all active in cluster
        if not self.datacenters.enabled and not self.nodes.enabled:
            self.allActive = True
        return True

    def checkConsul(self, consulService, datacenters=None, nodes=None):
        """
        Check if any Consul resources are passing.
        """
        statusList = []
        services   = []

        # Generate a list of Consul services from the API
        if datacenters:
            for dc in datacenters:
                dcServices = POWERCONSUL.API.health.service(consulService, dc=dc)[1]
                POWERCONSUL.LOG.info('Collecting [{0}] Consul [{1}] services in datacenter: {2}'.format(str(len(dcServices)), consulService, dc))
                services = services + dcServices
        else:
            services = POWERCONSUL.API.health.service(consulService)[1]
        POWERCONSUL.LOG.info('Checking against [{0}] Consul [{1}] services'.format(str(len(services)), consulService))

        # Process services
        for service in services:

            # Node / environment / role
            node     = service['Node']['Node']
            nodeEnv  = POWERCONSUL.getEnv(hostname=node)
            nodeRole = POWERCONSUL.getRole(hostname=node)
            checks   = service['Checks'][1]

            # If provided a node filter list
            if nodes and not node in nodes:
                POWERCONSUL.LOG.info('checkConsul -> skipping: {0}'.format(node))
                continue

            # Node must be in the same environment/role
            if (nodeEnv == POWERCONSUL.ENV) and (nodeRole == POWERCONSUL.ROLE):
                statusList.append(True if checks['Status'] == 'passing' else False)
                POWERCONSUL.LOG.info('Discovered cluster node [{0}]: env={1}, role={2}, service={3}, status={4}'.format(
                    node, nodeEnv, nodeRole, consulService, checks['Status']
                ))

        # Return the status list
        return statusList

    def activePassing(self, datacenters=None, nodes=None):
        """
        If the node is a standby, use this to check if the nodes in the active
        datacenter for this resource are passing/healthy.
        """
        consulService = POWERCONSUL.ARGS.get('consulservice', required='Consul service name required for clustered active/standby checks!')

        # Store flag if any active services are passing
        anyPassing = False

        # By datacenter
        if datacenters:
            POWERCONSUL.LOG.info('Looking for healthy/passing active [{0}] {1}s by: datacenters={2}'.format(consulService, self.resource, json.dumps(datacenters)))
            for status in self.checkConsul(consulService, datacenters=datacenters):
                if anyPassing:
                    continue
                anyPassing = status

        # By nodes
        if nodes:
            POWERCONSUL.LOG.info('Looking for healthy/passing active [{0}] {1}s by: nodes={2}'.format(consulService, self.resource, json.dumps(nodes)))
            for status in self.checkConsul(consulService, datacenters=self.datacenters.all, nodes=nodes):
                if anyPassing:
                    continue
                anyPassing = status

        # Return the flag that shows in any active services are passing
        POWERCONSUL.LOG.info('Healthy/passing active {0}s: {1}'.format(self.resource, anyPassing))
        return anyPassing

    def byDatacenter(self):
        """
        Ensure a clustered resource state by datacenter.
        """
        if not self.datacenters.enabled:
            return None

        # Log the service check
        POWERCONSUL.LOG.info('Clustered {0} [{1}@{2}]: active[{3}]/standby[{4}] datacenters'.format(
            self.resource,
            self.name,
            self.datacenters.local,
            self.datacenters.active,
            self.datacenters.standby
        ))

        # Node is active
        if self.datacenters.local == self.datacenters.active:
            self.ensure(service, clustered=True)

        # Node is standby
        if self.datacenters.local == self.datacenters.standby:

            # Active nodes healthy/passing
            if self.activePassing(datacenters=[self.datacenters.active]):
                self.ensure(expects=False, clustered=True, active=False)

            # Active nodes critical
            self.ensure(expects=True, clustered=True, active=False)

    def byNodes(self):
        """
        Ensure a clustered resource state by nodes.
        """
        if not self.nodes:
            return False

        # Log the service check
        POWERCONSUL.LOG.info('Clustered {0} [{1}]: active[{2}]/standby[{3}] nodes'.format(
            self.resource,
            self.name,
            ','.join(self.nodes.active),
            ','.join(self.nodes.standby)
        ))

        # Node is active
        if self.nodes.local in self.nodes.active:
            self.ensure(clustered=True)

        # Node is standby
        if self.nodes.local in self.nodes.standby:

            # Active nodes healthy/passing
            if self.activePassing(nodes=self.nodes.active):
                self.ensure(expects=False, clustered=True, active=False)

            # Active nodes critical
            self.ensure(expects=True, clustered=True, active=False)