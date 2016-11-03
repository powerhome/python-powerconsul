from powerconsul.common.args.options import OPTIONS
from powerconsul.common.handlers.base import PowerConsulHandler_Base

class PowerConsulHandler_Watchers(PowerConsulHandler_Base):
    """
    Class object for managing Consul service state watchers.
    """
    id      = 'watch'

    # Command description
    desc    = {
        "title": "Power Consul Watchers",
        "summary": "Watch Consul health checks",
        "usage": "powerconsul watch [state] [options]"
    }

    # Supported options
    options = [] + OPTIONS

    # Supported states
    commands = {
        "critical": {
            "help": "Watch for services in a critical state."
        },
        "warning": {
            "help": "Watch for services in a warning state."
        }
    }

    def __init__(self):
        super(PowerConsulHandler_Watchers, self).__init__(self.id)

    def critical(self):
        """
        Return a listing of datastores.
        """
        print 'CRITICAL'

    def warning(self):
        """
        Return a listing of virtual machines.
        """
        print 'WARNING'
