import os
import stat
import json
from uuid import uuid4
from subprocess import Popen, PIPE

class PowerConsul_Action(object):
    """
    Class object representing a trigger action.
    """
    def __init__(self, actionData):
        self._data    = actionData
        self._command = ['/usr/bin/env', 'true']

        # Temporary script
        self._script  = None

        # Bootstrap the action object
        self._bootstrap()

    def _bootstrap(self):
        """
        Bootstrap the action object.
        """
        if not self._data:
            return None

        # Trigger is a script
        if self._data.startswith('#!/bin/bash'):

            # Define a temporary script
            self._script = '/tmp/trigger_{0}.sh'.format(str(uuid4()))

            # Dump the action script
            with open(self._script, 'w') as f:
                f.write(self._data)
            os.chmod(self._script, os.stat(self._script).st_mode | stat.S_IEXEC)

            # Define the command
            self._command = ['/bin/bash', self._script]

        # Assume direct shell command
        else:
            self._command = self._data.split(' ')

    def _cleanup(self):
        """
        Post action cleanup.
        """
        if os.path.isfile(self._script):
            os.remove(self._script)

    def run(self):
        """
        Run the state action.
        """
        proc     = Popen(self._command, stdout=PIPE, stderr=PIPE)
        out, err = proc.communicate()

        # Command failed
        if proc.returncode != 0:
            POWERCONSUL.LOG.error('Failed to run action: {0}'.format(str(err).rstrip()))

        # Command success
        else:
            POWERCONSUL.LOG.info('Successfully ran action: {1}'.format(str(out).rstrip()))

        # Post action cleanup
        self._cleanup()

    @classmethod
    def parse(cls, state):
        """
        Parse an action stored in the KV database.
        """
        try:

            # Parse service JSON
            serviceJSON = json.loads(POWERCONSUL.ARGS.get('service',
                required='Must supply a service JSON object: powerconsul trigger <state> -s <serviceJSON>'
            ))

            # Set Consul service name
            POWERCONSUL.service = serviceJSON['ServiceName']

            # Return the action object
            return cls(POWERCONSUL.getKV('triggers/{0}/{1}/{2}'.format(
                POWERCONSUL.service, POWERCONSUL.CLUSTER.role, state
            )), serviceJSON)

        # Failed to parse service action/object
        except Exception as e:
            POWERCONSUL.die('Failed to parse service action: {0}'.format(str(e)))
