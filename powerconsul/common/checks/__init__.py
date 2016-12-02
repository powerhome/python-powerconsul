import json

import powerconsul.common.logger as logger

class Check_Base(object):
    """
    Base class for a checked resource.
    """
    def __init__(self, resource):
        self.resource       = resource
        self.name           = None

        # Parse the Consul service name and bootstrap cluster status
        POWERCONSUL.service = POWERCONSUL.ARGS.get('consulservice', required='Must supply a Consul servicename: powerconsul check <resource> -S <serviceName>')

        # Setup the logger
        POWERCONSUL.LOG = logger.create('check', service=POWERCONSUL.service, log_file='/var/log/powerconsul/check/{0}.{1}.log'.format(self.resource, POWERCONSUL.service))
        POWERCONSUL.LOG.info('=' * 20)

        # Bootstrap the cluster
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
                    applyChanges = True
                    serviceObj['Tags'].remove('nodns')

            # Disable DNS
            else:
                if not 'nodns' in serviceObj['Tags']:
                    applyChanges = True
                    serviceObj['Tags'].append('nodns')

            # Re-register the service
            if applyChanges:
                POWERCONSUL.LOG.info('enabled={0}'.format(('no' if ('nodns' in serviceObj['Tags']) else 'yes')), method='setDNS')

                # Make the API request
                POWERCONSUL.API.agent.service.register(POWERCONSUL.service,
                    service_id = serviceObj['ID'],
                    address    = serviceObj['Address'],
                    port       = serviceObj['Port'],
                    tags       = serviceObj['Tags'],
                    check      = json.loads(open('/etc/consul/service_{0}.json'.format(POWERCONSUL.service)).read())['service']['checks'][0]
                )

        # Failed to update DNS tag
        except Exception as e:
            POWERCONSUL.LOG.error('Failed to update DNS tag: {0}'.format(str(e)), method='setDNS')

    def byDatacenter(self):
        """
        Ensure a clustered resource state by datacenter.
        """
        if not POWERCONSUL.CLUSTER.datacenters.enabled:
            return None

        # Log the service check
        POWERCONSUL.LOG.info('active=[{0}], standby=[{1}], local={2}'.format(
            POWERCONSUL.CLUSTER.datacenters.active, POWERCONSUL.CLUSTER.datacenters.standby, POWERCONSUL.CLUSTER.datacenters.local
        ), method='ensure.byDatacenter')

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
        if not POWERCONSUL.CLUSTER.nodes.enabled:
            return None

        # Log the service check
        POWERCONSUL.LOG.info('active=[{0}], standby=[{1}], local={2}'.format(
            ','.join(POWERCONSUL.CLUSTER.nodes.active), ','.join(POWERCONSUL.CLUSTER.nodes.standby), POWERCONSUL.HOST
        ), method='ensure.byNodes')

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
