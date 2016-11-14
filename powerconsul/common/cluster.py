import json

class PowerConsul_Cluster(object):
    """
    Class object representating the cluster state of a node.
    """
    def __init__(self):

        # Cluster datacenters/nodes
        self.datacenters = None
        self.nodes       = None

        # Is clustering active / cluster role
        self.active      = False
        self.role        = None

        # Does the cluster have standby nodes
        self.hasStandby  = True

        # Cluster roles
        self.roles       = POWERCONSUL.COLLECTION.create({
            'primary': 'primary',
            'secondary': 'secondary',
            'standalone': 'standalone'
        })

        # Set up and retrieve cluster attributes
        self._bootstrap()

    def _setGroup(self, group, label):
        """
        Require the presence of both active/standby attributes.
        """

        # Group is disabled
        if not group['active'] and not group['standby']:
            group['enabled'] = False
            return POWERCONSUL.COLLECTION.create(group)

        # Active/standby attributes required if either are set
        if not group['active'] or not group['standby']:
            POWERCONSUL.die('Must specify both active/standby {0} attributes'.format(label))

        # Enable the group
        group['enabled'] = True

        # Return the collection
        return POWERCONSUL.COLLECTION.create(group)

    def _setNodes(self, nodes):
        """
        Set cluster nodes.
        """
        nodes['local'] = POWERCONSUL.HOST

        # Return the nodes collection
        return self._setGroup(nodes, 'nodes')

    def _setDatacenters(self, datacenters):
        """
        Set cluster datacenters.
        """
        datacenters['local'] = POWERCONSUL.CONFIG['datacenter']
        datacenters['all']   = POWERCONSUL.API.catalog.datacenters()

        # Return the datacenters collection
        return self._setGroup(datacenters, 'datacenters')

    def _bootstrap(self):
        """
        Bootstrap the cluster object.
        """
        clusterData = POWERCONSUL.getKV('cluster/{0}/{1}'.format(POWERCONSUL.ENV, POWERCONSUL.service))

        # Service is not clustered
        if not clusterData:
            self.active = False
            self.role   = self.roles.standalone

        # Cluster data found
        else:
            self.active = True

            # Parse out cluster information
            try:
                clusterAttrs = json.loads(clusterData)
            except Exception as e:
                POWERCONSUL.die('Failed to parse cluster information, must be JSON string: {0}'.format(str(e)))

            # Cluster by node
            self.nodes = self._setNodes({
                'active': clusterAttrs.get('active_nodes'),
                'standby': clusterAttrs.get('standby_nodes')
            })

            # Cluster by datacenter
            self.datacenters = self._setDatacenters({
                'active': clusterAttrs.get('active_datacenter'),
                'standby': clusterAttrs.get('standby_datacenter')
            })

            # Cannot cluster by both
            if self.datacenters.enabled and self.nodes.enabled:
                POWERCONSUL.die('Active/standby datacenters and nodes options are mutually exclusive!')

            # Datacenter validation
            if self.datacenters.enabled:

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

                # Set the cluster role
                self.role = self.roles.primary if (self.datacenters.local in self.datacenters.active) else self.roles.secondary

            # Nodes validation
            if self.nodes.enabled:

                # Local node must be in either active or standby nodes list
                if not self.nodes.local in (self.nodes.active + self.nodes.standby):
                    POWERCONSUL.die('Local node address [{0}] must be in either active {1} or standby {2} node list!'.format(
                        self.nodes.local,
                        json.dumps(self.nodes.active),
                        json.dumps(self.nodes.standby)
                    ))

                # Set the cluster role
                self.role = self.roles.primary if (self.nodes.local in self.nodes.active) else self.roles.secondary

            # Assume all active in cluster / no standby nodes
            if not self.datacenters.enabled and not self.nodes.enabled:
                self.hasStandby = False

        # Log the bootstrap process results
        POWERCONSUL.LOG.info('ConsulService[{0}].CLUSTER: active={1}, role={2}, hasStandby={3}'.format(
            POWERCONSUL.service, self.active, self.role, self.hasStandby
        ))

    def checkService(self, datacenters=None, nodes=None):
        """
        Check the state of a Consul service.
        """
        statusList = []
        services   = []

        # Generate a list of Consul services from the API
        if datacenters:
            for dc in datacenters:
                dcServices = POWERCONSUL.API.health.service(POWERCONSUL.service, dc=dc)[1]
                services = services + dcServices
        else:
            services = POWERCONSUL.API.health.service(POWERCONSUL.service)[1]

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

    def activePassing(self, datacenters=None, nodes=None):
        """
        Check if a Consul service has any active nodes in a passing state.
        """
        anyPassing = False

        # Can only filter by datacenters or nodes
        if datacenters and nodes:
            POWERCONSUL.die('Cannot check for active/passing services by datacenters/nodes at the same time!')

        # By datacenter
        if datacenters:
            for status in self.checkService(datacenters=datacenters):
                if anyPassing:
                    continue
                anyPassing = status

        # By nodes
        if nodes:
            for status in self.checkService(datacenters=self.datacenters.all, nodes=nodes):
                if anyPassing:
                    continue
                anyPassing = status

        # Log the results
        POWERCONSUL.LOG.info('ConsulService[{0}].CLUSTER.activePassing: by_nodes={1}, by_datacenters={2}, any_passing={3}, role={4}'.format(
            POWERCONSUL.service,
            ('yes' if nodes else 'no'),
            ('yes' if datacenters else 'no'),
            ('yes' if anyPassing else 'no'),
            self.role
        ))

        # Return the flag that shows in any active services are passing
        return anyPassing

    @classmethod
    def bootstrap(cls):
        POWERCONSUL.CLUSTER = cls()
