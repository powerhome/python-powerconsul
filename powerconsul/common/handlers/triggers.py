import re
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

        # Service attributes
        self.serviceJSON = json.loads(POWERCONSUL.ARGS.get('service'))
        self.serviceName = self.serviceJSON['ServiceName']

    def _run_action(self, action):
        """
        Run the state action.
        """

        # Trigger method reference
        if action.startswith('@'):
            methodName = re.compile(r'^@([^ ]*)[ ].*$').sub(r'\g<1>', action)
            methodArgs = re.compile(r'^@[^ ]*[ ](.*$)').sub(r'\g<1>', action)
            methodObj  = POWERCONSUL.ACTIONS.get(methodName)

            # Run the action
            try:
                methodObj(**json.loads(methodArgs))
            except Exception as e:
                return POWERCONSUL.LOG.error('Failed to run @{0}({1}): {2}'.format(methodName, methodArgs, str(e)))
            POWERCONSUL.LOG.info('Successfully ran @{0}({1})'.format(methodName, methodArgs))

        # Assume a shell command
        else:

            # Assume action is a shell command
            proc = Popen(action.split(' '), stdout=PIPE, stderr=PIPE)
            out, err = proc.communicate()

            # Command failed
            if proc.returncode != 0:
                return POWERCONSUL.LOG.error('Failed to run [{0}]: {1}'.format(action, str(err).rstrip()))
            POWERCONSUL.LOG.info('Successfully ran [{0}]: {1}'.format(action, str(out).rstrip()))

    def _get_action(self, state):
        """
        Retrieve an action for a service state trigger.
        """

        # See if output is JSON
        try:
            POWERCONSUL.LOG.info('Parse service output: [{0}]'.format(str(self.serviceJSON['Output'].rstrip())))
            if isinstance(self.serviceJSON['Output'], dict):
                return self.serviceJSON['Output']['action']
            return json.loads(self.serviceJSON['Output'])['action']
        except:
            POWERCONSUL.LOG.info('No JSON in service output, attempting KV lookup...')

        # Get from Consul KV store as a fallback
        index, data = POWERCONSUL.API.kv.get('triggers/{0}/{1}'.format(self.serviceName, state))

        # No action found
        if not data:
            return '/usr/bin/env true'

        # Return action string
        return data['Value']

    def critical(self):
        """
        Trigger an action for a service in a critical state.
        """

        # Action to run
        action = self._get_action('critical')
        POWERCONSUL.LOG.info('state=critical, service={0}, action={1}'.format(self.serviceName, action))

        # Run the action
        self._run_action(action)

    def warning(self):
        """
        Trigger an action for a service in a warning state.
        """

        # Action to run
        action = self._get_action('warning')
        POWERCONSUL.LOG.info('state=warning, service={0}, action={1}'.format(self.serviceName, action))

        # Run the action
        self._run_action(action)
