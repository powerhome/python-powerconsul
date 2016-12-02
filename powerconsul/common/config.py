import json
from os.path import expanduser, isfile

# Power Consul modules
from powerconsul.common.collection import PowerConsul_Collection

# Local / Consul agent configuration
CONSUL_CONFIG = '/etc/consul/config.json'
LOCAL_CONFIG  = expanduser('~/.powerconsul.conf')

class PowerConsul_Config(object):
    """
    Configuration object for Power Consul interface.
    """
    def __init__(self):
        self.CONSUL     = self._getConsulConfig()
        self.LOCAL      = self._getLocalConfig()

    def get(self, configType, key, default=None):
        """
        Retrieve a configuration key value.
        """
        configs = {
            'local': self.LOCAL,
            'consul': self.CONSUL
        }
        return getattr(configs[configType], key, default)

    def _getConsulConfig(self):
        """
        Load and return the Consul agent configuration.
        """
        try:
            return PowerConsul_Collection.create(json.loads(open(CONSUL_CONFIG, 'r').read()))
        except Exception as e:
            POWERCONSUL.die('Failed to parse Consul agent configuration: {0}'.format(str(e)))

    def _getLocalConfig(self):
        """
        Load and return the local Power Consul configuration.
        """

        # Local configuration should exist
        if not isfile(LOCAL_CONFIG):
            POWERCONSUL.die('You must create a local configuration file using: powerconsul config bootstrap <options>')

        # Parse the local configuration
        try:
            return PowerConsul_Collection.create(json.loads(open(LOCAL_CONFIG).read()))
        except Exception as e:
            POWERCONSUL.die('Failed to parse local configuration: {0}'.format(str(e)))

    @classmethod
    def writeLocal(cls, config):
        """
        Write the local configuration.
        """
        try:
            with open(LOCAL_CONFIG, 'w') as f:
                f.write(json.dumps(config))
        except Exception as e:
            POWERCONSUL.die('Failed to write local configuration: {0}'.format(str(e)))

    @classmethod
    def parse(cls):
        """
        Parse the configuration objects.
        """
        POWERCONSUL.CONFIG = cls()
