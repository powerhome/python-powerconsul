import json
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
            "help": "A username for supported triggers.".,
            "action": "store"
        },
        {
            "short":
        }
    ] + OPTIONS

    # Supported actions
    commands = {
        "critical": {
            "help": "Trigger an action for a service in a critical state."
        },
        "warning": {
            "help": "Trigger an action for a service in a warning state."
        },
        "crontab": {
            "help": "Enable or disable a user's crontab file."
        }
    }

    def __init__(self):
        super(PowerConsulHandler_Triggers, self).__init__(self.id)

        # Service attributes
        self.serviceJSON = None
        self.serviceName = None

    def _parse_service(self):
        self.serviceJSON = json.loads(POWERCONSUL.ARGS.get('service'))
        self.serviceName = self.serviceJSON['ServiceName']

    def _run_action(self, action):
        """
        Run the state action.
        """
        proc = Popen(action.split(' '), stdout=PIPE, stderr=PIPE)
        out, err = proc.communicate()

        # Command failed
        if proc.returncode != 0:
            return POWERCONSUL.LOG.error('Failed to run [{0}]: {1}'.format(action, str(err).rstrip()))
        POWERCONSUL.LOG.info('Successfully ran [{0}]: {1}'.format(action, str(out).rstrip()))

    def _get_action(self, service, state):
        """
        Retrieve an action for a service state trigger.
        """
        index, data = POWERCONSUL.API.kv.get('triggers/{0}/{1}'.format(service, state))

        # No action found
        if not data:
            return '/usr/bin/env true'

        # Return action string
        return data['Value']

    def critical(self):
        """
        Trigger an action for a service in a critical state.
        """
        self._parse_service()

        # Action to run
        action = self._get_action(self.serviceName, 'critical')
        POWERCONSUL.LOG.info('state=critical, service={0}, action={1}'.format(self.serviceName, action))

        # Run the action
        self._run_action(action)

    def warning(self):
        """
        Trigger an action for a service in a warning state.
        """
        self._parse_service()

        # Action to run
        action = self._get_action(self.serviceName, 'warning')
        POWERCONSUL.LOG.info('state=warning, service={0}, action={1}'.format(self.serviceName, action))

        # Run the action
        self._run_action(action)
