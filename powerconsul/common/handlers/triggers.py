from powerconsul.common.args.options import OPTIONS
from powerconsul.common.handlers.base import PowerConsulHandler_Base

class PowerConsulHandler_Triggers(PowerConsulHandler_Base):
    """
    Class object for managing Consul service state change triggers.
    """
    id      = 'trigger'

    # Command description
    desc    = {
        "title": "Power Consul Triggers",
        "summary": "Trigger events on service state changes.",
        "usage": "powerconsul trigger [action] [options]"
    }

    # Supported options
    options = [] + OPTIONS

    # Supported actions
    commands = {
        "start": {
            "help": "Start a service."
        },
        "stop": {
            "help": "Stop a service."
        }
    }

    def __init__(self):
        super(PowerConsulHandler_Triggers, self).__init__(self.id)

    def start(self):
        """
        Return a listing of datastores.
        """
        print 'START'

    def stop(self):
        """
        Return a listing of virtual machines.
        """
        print 'STOP'
