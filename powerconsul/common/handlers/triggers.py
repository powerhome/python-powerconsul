import re
import os
import stat
import json
from uuid import uuid4
from subprocess import Popen, PIPE

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
        },
        {
            "short": "u",
            "long": "user",
            "help": "A username for supported triggers.",
            "action": "store"
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
        action = POWERCONSUL.ACTION.parse('critical')
        action.run()

    def warning(self):
        """
        Trigger an action for a service in a warning state.
        """
        action = POWERCONSUL.ACTION.parse('warning')
        action.run()
