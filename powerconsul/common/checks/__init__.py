import json
import re
from os import path
from subprocess import Popen, PIPE

import powerconsul.common.logger as logger

class Check_Base(object):
    """
    Base class for a checked resource.
    """
    def __init__(self, resource):
        self.resource       = resource
        self.name           = None

        # Process/regex string filter to indicate all is well
        self.procStr        = POWERCONSUL.ARGS.get('procstr')
        self.procRe         = POWERCONSUL.ARGS.get('procre')

        # Noop file
        self.noopFile       = POWERCONSUL.ARGS.get('noopfile')

        # Parse the Consul service name and bootstrap cluster status
        POWERCONSUL.service = POWERCONSUL.ARGS.get('consulservice', required='Must supply a Consul servicename: powerconsul check <resource> -S <serviceName>')

        # Setup the logger
        POWERCONSUL.LOG = logger.create('check', service=POWERCONSUL.service, log_file='/var/log/powerconsul/check/{0}.{1}.log'.format(self.resource, POWERCONSUL.service))
        POWERCONSUL.LOG.info('=' * 20)

        # Bootstrap the cluster
        POWERCONSUL.CLUSTER.bootstrap()

    def checkNoop(self):
        """
        Look for the existence of a noop file, to indicate all checks should pass.
        """
        if self.noopFile and path.isfile(self.noopFile):
            POWERCONSUL.LOG.info('Noop file discovered [{0}], setting checks to passing state'.format(self.noopFile))
            return True
        return False

    def checkPS(self):
        """
        Look for a user supplied string in the process table. If found, assume the check should pass.
        """
        if self.procStr or self.procRe:
            pstab = Popen(['ps', 'aux'], stdout=PIPE)
            out   = pstab.communicate()

            # Process regex
            regex = None if not self.procRe else re.compile(self.procRe)

            # Look for the process string in the process table
            for line in out[0].split('\n'):

                # Ignore powerconsul process table entries
                if 'powerconsul' in line:
                    continue

                # Process string
                if (self.procStr) and (self.procStr in line):
                    POWERCONSUL.LOG.info('Discovered process filter string: [{0}], set state -> passing'.format(self.procStr), method='checkPS')
                    return True

                # Process regular expressions
                if (regex) and (regex.match(line)):
                    POWERCONSUL.LOG.info('Discovered process filter regex: [{0}], set state -> passing'.format(self.procRe), method='checkPS')
                    return True
        return False

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
