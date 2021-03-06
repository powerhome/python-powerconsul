import os
import stat
import json
from uuid import uuid4
from subprocess import Popen, PIPE

class PowerConsul_Action(object):
    """
    Class object representing a trigger action.
    """
    def __init__(self, actionData, state):
        self._data    = actionData
        self._command = ['/bin/echo', 'noop']
        self._type    = None
        self._state   = state

        # Temporary script
        self._script  = None

        # Bootstrap the action object
        self._bootstrap()

    def _subvars(self, cmdStr):
        """
        Look for any custom substitution variables.
        """
        for k,v in POWERCONSUL.CONFIG.get('local', 'subVars', default={}).__dict__.iteritems():
            cmdStr = cmdStr.replace('@{0}'.format(k), v)
        return cmdStr

    def _bootstrap(self):
        """
        Bootstrap the action object.
        """
        if not self._data:
            self._type   = 'default'
            return None

        # Trigger is a script
        if self._data.startswith('#!/bin/bash'):
            self._type   = 'script'

            # Define a temporary script
            self._script = '/tmp/trigger_{0}.sh'.format(str(uuid4()))

            # Dump the action script
            with open(self._script, 'w') as f:
                for line in self._data.split('\n'):
                    f.write(self._subvars(line))
                    f.write('\n')
            os.chmod(self._script, os.stat(self._script).st_mode | stat.S_IEXEC)

            # Define the command
            self._command = ['/bin/bash', self._script]

        # Assume direct shell command
        else:
            self._type    = 'command'
            self._command = self._subvars(self._data).split(' ')

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

        # Is this triggered configured for noop?
        if POWERCONSUL.service in POWERCONSUL.CONFIG.get('local', 'noopTriggers', default=[]):
            POWERCONSUL.LOG.info('Service trigger(s) configured as noop. Skipping...')
            return True

        try:
            proc     = Popen(self._command, stdout=PIPE, stderr=PIPE)
            out, err = proc.communicate()

            # Command failed
            if proc.returncode != 0:
                POWERCONSUL.LOG.error('type={0}, state={1}, error={2}'.format(self._type, self._state, str(err).rstrip()), method='action.run')

            # Command success
            else:
                POWERCONSUL.LOG.info('type={0}, state={1}, output={2}'.format(self._type, self._state, str(out).rstrip()), method='action.run')

            # Post action cleanup
            self._cleanup()

        # Failed to run action
        except Exception as e:
            POWERCONSUL.LOG.exception('state={0}, error={1}'.format(state, str(e)), method='action.run', die=True)

    @classmethod
    def checkNodes(cls):
        """
        Check if any primary nodes are passing.
        """
        if not POWERCONSUL.CLUSTER.nodes.enabled:
            return None

        # No active nodes passing
        if not POWERCONSUL.CLUSTER.activePassing(nodes=POWERCONSUL.CLUSTER.nodes.active):
            POWERCONSUL.LOG.info('No active/healthy nodes, set role: primary', method='action.checkNodes')
            POWERCONSUL.CLUSTER.role = POWERCONSUL.CLUSTER.roles.primary

    @classmethod
    def checkDatacenters(cls):
        """
        Check if any primary datacenters are passing.
        """
        if not POWERCONSUL.CLUSTER.datacenters.enabled:
            return None

        # No active datacenters passing
        if not POWERCONSUL.CLUSTER.activePassing(datacenters=[POWERCONSUL.CLUSTER.datacenters.active]):
            POWERCONSUL.LOG.info('No active/healthy datacenters, set role: primary', method='action.checkDatacenters')
            POWERCONSUL.CLUSTER.role = POWERCONSUL.CLUSTER.roles.primary

    @classmethod
    def parse(cls, state):
        """
        Parse an action stored in the KV database.
        """
        try:

            import powerconsul.common.logger as logger

            # Parse service JSON
            serviceJSON = json.loads(POWERCONSUL.ARGS.get('service',
                required='Must supply a service JSON object: powerconsul trigger <state> -s <serviceJSON>'
            ))

            # Set Consul service name
            POWERCONSUL.service = serviceJSON['ServiceName']

            # Setup the logger
            POWERCONSUL.LOG = logger.create('trigger', service=POWERCONSUL.service, log_file='/var/log/powerconsul/trigger/{0}.{1}.log'.format(POWERCONSUL.service, state))
            POWERCONSUL.LOG.info('=' * 20)

            # Bootstrap cluster state
            POWERCONSUL.CLUSTER.bootstrap()

            # If secondary, make sure primaries are passing
            if POWERCONSUL.CLUSTER.role == POWERCONSUL.CLUSTER.roles.secondary:
                cls.checkDatacenters()
                cls.checkNodes()

            # Return the action object
            return cls(POWERCONSUL.getKV('triggers/{0}/{1}/{2}'.format(
                POWERCONSUL.service, POWERCONSUL.CLUSTER.role, state
            )), state)

        # Failed to parse service action/object
        except Exception as e:
            POWERCONSUL.LOG.exception('state={0}, error={1}'.format(state, str(e)), method='action.parse', die=True)
