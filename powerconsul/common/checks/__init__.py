class Check_Base(object):
    """
    Base class for a checked resource.
    """
    def __init__(self):
        self.datacenters = None
        self.nodes       = None
        self.allActive   = False
        self.clustered   = self.setCluster(POWERCONSUL.ARGS.get('clustered'))
        self.filterStr   = ''

    def setGroup(self, group, label):
        """
        Require the presence of both active/standby attributes.
        """
        if not group['active'] and not group['standby']:
            return group
        group['enabled'] = True

        # Active/standby attributes required if either are set
        if not group['active'] or not group['standby']:
            POWERCONSUL.die('Must specify both active/standby {0} attributes'.format(label))
        return group

    def setCluster(self, state):
        """
        Set cluster attributes.
        """
        if not state:
            return False

        # Cluster by node
        self.nodes   = self.setGroup({
            'active': POWERCONSUL.ARGS.get('activenodes', default='').split(','),
            'standby': POWERCONSUL.ARGS.get('standbynodes', default='').split(','),
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
                if not self.datacenters[dcType] in self.datacenters.all:
                    POWERCONSUL.die('{0} datacenter [{1}] not valid, available datacenters: {1}'.format(
                        dcType.capitalize(),
                        self.datacenters[dcType],
                        self.datacenters.all
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
                    self.nodes.active,
                    self.nodes.standby
                ))

        # Assume all active in cluster
        if not self.datacenters.enabled and not self.nodes.enabled:
            self.allActive = True
        return True

    def checkConsul(self, service, datacenters=None, nodes=None):
        """
        Check if any Consul services are passing.
        """
        statusList = []
        services   = []

        # Generate a list of Consul services from the API
        if datacenters:
            for dc in datacenters:
                services + POWERCONSUL.API.health.service(service, dc=dc)[1]
        else:
            services = POWERCONSUL.API.health.service(service)[1]

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
                    node, nodeEnv, nodeRole, service, checks['Status']
                ))

        # Return the status list
        return statusList

    def activePassing(self, datacenters=None, nodes=None):
        """
        If the node is a standby, use this to check if the nodes in the active
        datacenter for this service are passing/healthy.
        """
        consulService = POWERCONSUL.ARGS.get('consulservice', required='Consul service name required for clustered active/standby checks!')

        # Store flag if any active services are passing
        anyPassing = False

        # By datacenter
        if datacenters:
            for status in self.checkConsul(consulService, datacenters=datacenters):
                if anyPassing:
                    continue
                anyPassing = status

        # By nodes
        if nodes:
            for status in self.checkConsul(consulService, datacenters=self.datacenters.all, nodes=objects):
                if anyPassing:
                    continue
                anyPassing = status

        # Return the flag that shows in any active services are passing
        return anyPassing
