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

        # Service attributes
        self.serviceJSON = json.loads(POWERCONSUL.ARGS.get('service'))
        self.serviceName = self.serviceJSON['ServiceName']

    def _get_action(self, service, state):
        """
        Retrieve an action for a service state trigger.
        """
        index, data = POWERCONSUL.API.kv.get('triggers/{0}/{1}'.format(service, state))

        # No action found
        if not data:
            return '/bin/true'

        # Return action string
        return data['Value']

    def critical(self):
        """
        Trigger an action for a service in a critical state.
        """

        # Action to run
        action = self._get_action(self.serviceName, 'critical')
        POWERCONSUL.LOG.info('state=critical, service={1}, action={2}'.format(self.serviceName, action))

    def warning(self):
        """
        Trigger an action for a service in a warning state.
        """

        # Action to run
        action = self._get_action(self.serviceName, 'warning')
        POWERCONSUL.LOG.info('state=warning, service={1}, action={2}'.format(self.serviceName, action))
