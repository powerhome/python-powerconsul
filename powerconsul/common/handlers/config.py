import json

import powerconsul.common.logger as logger
from powerconsul.common.args.options import OPTIONS
from powerconsul.common.handlers.base import PowerConsulHandler_Base

class PowerConsulHandler_Config(PowerConsulHandler_Base):
    """
    Class object for managing Power Consul configuration.
    """
    id      = 'config'

    # Command description
    desc    = {
        "title": "Power Consul Configuration",
        "summary": "Manage local Power Consul configuration.",
        "usage": "powerconsul config [action] [options]"
    }

    # Supported options
    options = [
        {
            "short": "C",
            "long": "config",
            "help": "The configuration as a JSON string.",
            "action": "store"
        }
    ] + OPTIONS

    # Supported states
    commands = {
        "bootstrap": {
            "help": "Bootstrap the local configuration."
        }
    }

    def __init__(self):
        super(PowerConsulHandler_Config, self).__init__(self.id)

        # Setup the logger
        POWERCONSUL.LOG = logger.create('config', log_file='/var/log/powerconsul/config.log')

    def bootstrap(self):
        """
        Bootstrap the local configuration.
        """
        try:
            config = json.loads(POWERCONSUL.ARGS.get('config', required='Must supply a configuration JSON string to bootstrap!'))
        except Exception as e:
            POWERCONSUL.die('Failed to parse configuration string: {0}'.format(str(e)))

        # Write the local configuration
        POWERCONSUL.LOG.info('Bootstrapped local configuration: {0}'.format(json.dumps(config)), method='bootstrap')
        POWERCONSUL.CONFIG.writeLocal(config)
