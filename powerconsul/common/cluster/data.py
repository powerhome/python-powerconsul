import re
import json

class PowerConsul_ClusterData(object):
    """
    Class object representing parsed cluster information from KV store.
    """
    def __init__(self):
        self._clusterKey = POWERCONSUL.CONFIG.get('local', 'clusterKey')
        self._data       = None

        # Is cluster data defined
        self.defined     = self._bootstrap()

    def get(self):
        """
        Getter method for returning cluster data.
        """
        return self._data

    def _bootstrap(self):
        """
        Bootstrap node cluster data.
        """
        if not self._clusterKey:
            POWERCONSUL.LOG.info('No cluster key configured, skipping clustering...', method='cluster.data._bootstrap')
            return False

        # Get key/value data
        kvpath = '{0}/{1}'.format(self._clusterKey, POWERCONSUL.service)
        kvdata = POWERCONSUL.getKV(kvpath)

        # No cluster data found
        if not kvdata:
            POWERCONSUL.LOG.info('No cluster data found: {0}'.format(kvpath), method='cluster.data._bootstrap')
            return None
        POWERCONSUL.LOG.info('Discovered cluster data: {0}'.format(kvpath), method='cluster.data._bootstrap')

        # Load cluster data
        self._data = POWERCONSUL.parseJSON(kvdata, error='Failed to parse cluster data')

        # If filtering hosts
        if 'filter' in self._data:
            hostFilter = None

            # Load filters
            for f,c in self._data['filter'].iteritems():
                if re.compile(f).match(POWERCONSUL.HOST):
                    hostFilter = f
                    self._data  = c

            # Host does not match any of the filters
            if not hostFilter:
                POWERCONSUL.LOG.critical('Host must match at least one cluster filter!', method='cluster.data._bootstrap', die=True)
            POWERCONSUL.LOG.info('Host filtering applied: {0}'.format(hostFilter), method='cluster.data._bootstrap')

        # No host filter
        else:
            POWERCONSUL.LOG.info('No host filtering applied.', method='cluster.data._bootstrap')

        # Log cluster data
        POWERCONSUL.LOG.info('data={0}'.format(json.dumps(self._data)), method='cluster.data._bootstrap')
        return True
