from __future__ import print_function
from powerconsul.service.vars import CHROLE
from powerconsul.kvdb import PowerConsul_KVDB as KVDB
from powerconsul.service.base import PowerConsul_ServiceBase
from powerconsul.common.config import PowerConsul_Config

class _KVDB_Mapper(PowerConsul_ServiceBase):
    def __init__(self, consul_service):
        super(_KVDB_Mapper, self).__init__()
        self.cluster = KVDB(base_path=self.CONF.LOCAL.clusterKey, put_local=False)
        self.service = KVDB(base_path='service/{0}'.format(consul_service), put_local=False)

class PowerConsul_ServiceCluster(PowerConsul_ServiceBase):
    """
    Cluster data for a service object.
    """
    def __init__(self, name):
        super(PowerConsul_ServiceCluster, self).__init__()

        # Consul service name / KV database
        self.name          = name
        self.kv            = _KVDB_Mapper(self.name)

        # Load services
        self.services      = self.get_cluster_services()

        # Service data / active / standby nodes / health
        self.data          = self.kv.cluster.get(self.name)
        self.active_nodes  = self.data['active_nodes']
        self.standby_nodes = self.data.get('standby_nodes', None)
        self.health        = self.get_cluster_health()

    def status(self):
        """
        Generate the status message for the clustered service.
        """

        # Active / standby node status
        active_status  = []
        standby_status = []

        # Get the status of active nodes
        for node in self.active_nodes:
            health = self.health[node]

            # Append the health string for this node
            active_status.append('{0}.{1}'.format(node, self.colored(health, 'green' if health == 'passing' else 'red')))

        # Generate the status message
        status_message = [
            '  {0}'.format(self.bold('cluster:')),
            '    nodes.active: {0}'.format(', '.join(active_status))
        ]

        # Get the status of standby nodes
        if self.standby_nodes:
            for node in self.standby_nodes:
                health = self.health[node]

                # Append the status string for this node
                standby_status.append('{0}.{1}'.format(node, self.colored(health, 'green' if health == 'passing' else 'red')))

            # Update the status message with secondary node data
            status_message.append('    nodes.standby: {0}'.format(', '.join(standby_status)))

        # Return the status message
        return '\n'.join(status_message)

    def switch_roles(self):
        """
        Switch roles for existing clustered nodes and lock until service
        checks are back into a passing state for all nodes.
        """
        print('Switching cluster primary/secondary node roles...', end='')
        self.kv.cluster.put(self.name, {
            'active_nodes': self.standby_nodes,
            'standby_nodes': self.active_nodes,
            'lock': True
        })
        print(self.colored('SUCCESS', 'green'))

    def promote_secondary(self):
        """
        Promote the secondary node(s) to primary.
        """
        for node in self.standby_nodes:
            print('Starting promotion for node {0}...'.format(node), end='')

            try:
                self.kv.service.put('{0}/promote'.format(node), CHROLE.START)
            except Exception as e:
                print(self.colored('FAILED', 'red'))
                self.die('Failed to signal promote secondary: {0}'.format(str(e)))
            print(self.colored('SUCCESS', 'green'))

    def demote_primary(self):
        """
        Demote the primary node(s) to secondary.
        """
        for node in self.active_nodes:
            print('Starting demotion for node {0}...'.format(node), end='')

            try:
                self.kv.service.put('{0}/demote'.format(node), CHROLE.START)
            except Exception as e:
                print(self.colored('FAILED', 'red'))
                self.die('Failed to signal demote primary: {0}'.format(str(e)))
            print(self.colored('SUCCESS', 'green'))

    def promote_secondary_wait(self):
        """
        Wait for secondary promotion to complete.
        """
        for node in self.standby_nodes:
            self.kv.service.wait('{0}/promote'.format(node), CHROLE.WAIT,
                message='Promoting secondary node {0}...'.format(node))

    def demote_primary_wait(self):
        """
        Wait for primary demotion to complete.
        """
        for node in self.active_nodes:
            self.kv.service.wait('{0}/demote'.format(node), CHROLE.WAIT,
                message='Demoting primary node {0}...'.format(node))

    def promote_secondary_complete(self):
        """
        Update KV after promotion complete.
        """
        for node in self.standby_nodes:
            print('Clearing promotion trigger for node {0}...'.format(node), end='')

            try:
                self.kv.service.put('{0}/promote'.format(node), CHROLE.NULL)
            except Exception as e:
                print(self.colored('FAILED', 'red'))
                self.die('Failed to clear promotion trigger: {0}'.format(str(e)))
            print(self.colored('SUCCESS', 'green'))

    def demote_primary_complete(self):
        """
        Update KV after demotion is complete.
        """
        for node in self.active_nodes:
            print('Clearing demotion trigger for node {0}...'.format(node), end='')

            try:
                self.kv.service.put('{0}/demote'.format(node), CHROLE.NULL)
            except Exception as e:
                print(self.colored('FAILED', 'red'))
                self.die('Failed to clear demotion trigger: {0}'.format(str(e)))
            print(self.colored('SUCCESS', 'green'))

    def get_cluster_services(self):
        """
        Get all services and health.
        """
        services    = []
        srvFilter   = self.CONF.get('local', 'serviceFilter')

        # Generate a list of Consul services from the API
        for dc in self.dcs:
            services = services + self.API.health.service(self.name, dc=dc)[1]

        # Mapped services
        mappedServices = {}

        # Process raw services
        for srv in services:
            node   = srv['Node']['Node']

            # Get the check status
            try:
                status = srv['Checks'][1]['Status']
            except:
                status = 'critical'

            # Service regex filter
            if srvFilter and not self.re.compile(srvFilter).match(node):
                continue

            # Map the service
            mappedServices[node] = {
                'status': status
            }

        # Return mapped services
        return mappedServices

    def get_cluster_health(self):
        """
        Get service health for all nodes.
        """
        srvHealth = {}

        # Parse active nodes
        for node in self.active_nodes:
            try:
                srvHealth[node] = self.services[node]['status']
            except:
                srvHealth[node] = 'critical'

        # Secondary nodes
        if 'standby_nodes' in self.data:
            for node in self.standby_nodes:
                try:
                    srvHealth[node] = self.services[node]['status']
                except:
                    srvHealth[node] = 'critical'

        # Return service health
        return srvHealth
