import json

# Power Consul modules
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
    options = [
        {
            "short": "s",
            "long": "service",
            "help": "The service check as a JSON string.",
            "action": "store",
            "required": True
        }
    ] + OPTIONS

    # Supported actions
    commands = {
        "critical": {
            "help": "Trigger an action for a service in a critical state."
        },
        "warning": {
            "help": "Trigger an action for a service in a warning state."
        }
    }

    def __init__(self):
        super(PowerConsulHandler_Triggers, self).__init__(self.id)

    def critical(self):
        """
        Trigger an action for a service in a critical state.
        """
        with open('/tmp/triggered_critical', 'w') as f:
            f.write(POWERCONSUL.ARGS.get('service'))

    def warning(self):
        """
        Trigger an action for a service in a warning state.
        """
        with open('/tmp/triggered_warning', 'w') as f:
            f.write(POWERCONSUL.ARGS.get('service'))
