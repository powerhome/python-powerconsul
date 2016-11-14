import json

class Check_Base(object):
    """
    Base class for a checked resource.
    """
    def __init__(self, resource):
        self.resource       = resource
        self.name           = None

        # Parse the Consul service name and bootstrap cluster status
        POWERCONSUL.service = POWERCONSUL.ARGS.get('consulservice', required='Must supply a Consul servicename: powerconsul check <resource> -S <serviceName>')
        POWERCONSUL.CLUSTER.bootstrap()

    def setDNS(self, state):
        """
        Disable/enable this service in a DNS prepared query via tags.
        """
        try:
            serviceObj   = POWERCONSUL.API.agent.services()[POWERCONSUL.service]
            applyChanges = False

            # Enable DNS
            if state:
                if 'nodns' in serviceObj['Tags']:
                    POWERCONSUL.LOG.info('Setting DNS state for [{0}] service: enabled=yes'.format(POWERCONSUL.service))
                    applyChanges = True
                    serviceObj['Tags'].remove('nodns')

            # Disable DNS
            else:
                if not 'nodns' in serviceObj['Tags']:
                    POWERCONSUL.LOG.info('Setting DNS state for [{0}] service: enabled=no'.format(POWERCONSUL.service))
                    applyChanges = True
                    serviceObj['Tags'].append('nodns')

            # Re-register the service
            if applyChanges:
                POWERCONSUL.API.agent.service.register(POWERCONSUL.service,
                    service_id = serviceObj['ID'],
                    address    = serviceObj['Address'],
                    port       = serviceObj['Port'],
                    tags       = serviceObj['Tags'],
                    check      = json.loads(open('/etc/consul/service_{0}.json'.format(POWERCONSUL.service)).read())['service']['checks'][0]
                )
        except Exception as e:
            POWERCONSUL.LOG.error('Failed to update DNS tag: {0}'.format(str(e)))

    def byDatacenter(self):
        """
        Ensure a clustered resource state by datacenter.
        """
        if not POWERCONSUL.CLUSTER.datacenters.enabled:
            return None

        # Log the service check
        POWERCONSUL.LOG.info('Clustered {0} [{1}@{2}]: active[{3}]/standby[{4}] datacenters'.format(
            self.resource,
            self.name,
            POWERCONSUL.CLUSTER.datacenters.local,
            POWERCONSUL.CLUSTER.datacenters.active,
            POWERCONSUL.CLUSTER.datacenters.standby
        ))

        # Node is active
        if POWERCONSUL.CLUSTER.datacenters.local == POWERCONSUL.CLUSTER.datacenters.active:
            self.ensure(service, clustered=True)

        # Node is standby
        if POWERCONSUL.CLUSTER.datacenters.local == POWERCONSUL.CLUSTER.datacenters.standby:

            # Active nodes healthy/passing
            if POWERCONSUL.CLUSTER.activePassing(datacenters=[POWERCONSUL.CLUSTER.datacenters.active]):
                self.ensure(expects=False, clustered=True, active=False)

            # Active nodes critical
            self.ensure(expects=True, clustered=True, active=False)

    def byNodes(self):
        """
        Ensure a clustered resource state by nodes.
        """
        if not POWERCONSUL.CLUSTER.nodes:
            return False

        # Log the service check
        POWERCONSUL.LOG.info('Clustered {0} [{1}]: active[{2}]/standby[{3}] nodes'.format(
            self.resource,
            self.name,
            ','.join(POWERCONSUL.CLUSTER.nodes.active),
            ','.join(POWERCONSUL.CLUSTER.nodes.standby)
        ))

        # Node is active
        if POWERCONSUL.CLUSTER.nodes.local in POWERCONSUL.CLUSTER.nodes.active:
            self.ensure(clustered=True)

        # Node is standby
        if POWERCONSUL.CLUSTER.nodes.local in POWERCONSUL.CLUSTER.nodes.standby:

            # Active nodes healthy/passing
            if POWERCONSUL.CLUSTER.activePassing(nodes=POWERCONSUL.CLUSTER.nodes.active):
                self.ensure(expects=False, clustered=True, active=False)

            # Active nodes critical
            self.ensure(expects=True, clustered=True, active=False)
