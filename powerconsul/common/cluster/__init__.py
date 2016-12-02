import re
import json

from powerconsul.common.cluster.data import PowerConsul_ClusterData

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

        # Cluster data key / cluster data
        self.data        = PowerConsul_ClusterData()

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
            POWERCONSUL.LOG.critical('Must specify both active/standby {0} attributes'.format(label), method='cluster._setGroup', die=True)

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
        datacenters['local'] = POWERCONSUL.CONFIG.get('consul', 'datacenter')
        datacenters['all']   = POWERCONSUL.datacenters

        # Return the datacenters collection
        return self._setGroup(datacenters, 'datacenters')

    def _process(self, clusterAttrs):
        """
        Process cluster data.
        """
        POWERCONSUL.LOG.info('clusterAttributes={0}'.format(json.dumps(clusterAttrs)), method='cluster._process')

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
            POWERCONSUL.LOG.critical('Active/standby datacenters and nodes options are mutually exclusive!', method='cluster._process', die=True)

        # Datacenter validation
        if self.datacenters.enabled:

            # Supplied datacenters must be valid
            for dcType in ['active', 'standby', 'local']:
                if not getattr(self.datacenters, dcType) in self.datacenters.all:
                    POWERCONSUL.LOG.critical('{0} datacenter [{1}] not valid, available datacenters: {2}'.format(
                        dcType.capitalize(),
                        getattr(self.datacenters, dcType),
                        json.dumps(self.datacenters.all)
                    ), method='cluster._process', die=True)

            # Local server's datacenter must match either active or standby
            if not self.datacenters.local in [self.datacenters.active, self.datacenters.standby]:
                POWERCONSUL.LOG.critical('Local server\'s datacenter [{0}] must be either the active [{1}] or standby [{2}] datacenter!'.format(
                    self.datacenters.local,
                    self.datacenters.active,
                    self.datacenters.standby
                ), method='cluster._process', die=True)

            # Set the cluster role
            self.role = self.roles.primary if (self.datacenters.local in self.datacenters.active) else self.roles.secondary

        # Nodes validation
        if self.nodes.enabled:

            # Local node must be in either active or standby nodes list
            if not self.nodes.local in (self.nodes.active + self.nodes.standby):
                POWERCONSUL.LOG.critical('Local node address [{0}] must be in either active {1} or standby {2} node list!'.format(
                    self.nodes.local,
                    json.dumps(self.nodes.active),
                    json.dumps(self.nodes.standby)
                ), method='cluster._process', die=True)

            # Set the cluster role
            self.role = self.roles.primary if (self.nodes.local in self.nodes.active) else self.roles.secondary

        # Assume all active in cluster / no standby nodes
        if not self.datacenters.enabled and not self.nodes.enabled:
            self.hasStandby = False

    def _bootstrap(self):
        """
        Bootstrap the cluster object.
        """

        # Service is not clustered
        if not self.data.defined:
            self.active = False
            self.role   = self.roles.standalone

        # Cluster data found
        else:
            self.active = True

            # Process cluster data
            self._process(self.data.get())

        # Log the bootstrap process results
        POWERCONSUL.LOG.info('active={0}, role={1}, hasStandby={2}'.format(self.active, self.role, self.hasStandby), method='cluster._bootstrap')

    def _checkStatus(self, node, status):
        """
        Return a boolean depending on the status string.
        """
        POWERCONSUL.LOG.info('node={0}, status={1}'.format(node, status), method='cluster._checkStatus')
        return True if status == 'passing' else False

    def checkService(self, datacenters=None, nodes=None):
        """
        Check the state of a Consul service.
        """
        statusList = []
        services   = POWERCONSUL.getServiceHealth(datacenters=datacenters)

        # Process services
        for service in services:
            node   = service['node']
            status = service['status']

            # If provided a node filter list
            if nodes and not node in nodes:
                continue

            # Store the status for the node
            statusList.append(self._checkStatus(node, status))

        # Return the status list
        return statusList

    def activePassing(self, datacenters=None, nodes=None):
        """
        Check if a Consul service has any active nodes in a passing state.
        """
        anyPassing = False

        # Can only filter by datacenters or nodes
        if datacenters and nodes:
            POWERCONSUL.LOG.critical('Cannot check for active/passing services by datacenters/nodes at the same time!', method='cluster.activePassing', die=True)

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
        POWERCONSUL.LOG.info('by_nodes={0}, by_datacenters={1}, any_passing={2}, role={3}'.format(
            ('yes' if nodes else 'no'),
            ('yes' if datacenters else 'no'),
            ('yes' if anyPassing else 'no'),
            self.role
        ), method='cluster.activePassing')

        # Return the flag that shows in any active services are passing
        return anyPassing

    @classmethod
    def bootstrap(cls):
        try:
            POWERCONSUL.CLUSTER = cls()
        except Exception as e:
            POWERCONSUL.LOG.exception('Failed to bootstrap cluster state: {0}'.format(str(e)), method='cluster.bootstrap', die=True)
