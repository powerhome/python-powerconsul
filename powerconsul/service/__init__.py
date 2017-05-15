from __future__ import print_function
import re
import json
from os import unlink, path
from sys import argv
from time import sleep
from subprocess import Popen, PIPE
from powerconsul.service.vars import CHROLE
from powerconsul.kvdb import PowerConsul_KVDB as KVDB
from powerconsul.service.base import PowerConsul_ServiceBase
from powerconsul.service.cluster import PowerConsul_ServiceCluster

class PowerConsul_Service(PowerConsul_ServiceBase):
    """
    Class object for representing a Consul service.
    """
    def __init__(self, name, consul_service, local_services, noop_lockfile):
        super(PowerConsul_Service, self).__init__()

        # Service name / local service names
        self.name    = name
        self.local   = [name] if not local_services else local_services

        # Service KV database
        self.kv      = KVDB(base_path='service/{0}'.format(consul_service))

        # Lock file to force a passing state for a check
        self.lock    = noop_lockfile

        # Parse the service command
        self.command = self._get_command()

        # Construct cluster data
        self.cluster = PowerConsul_ServiceCluster(consul_service)

    def _get_command(self):
        """
        Retrieve and validate the service command.
        """

        # Require an argument
        if not len(argv) > 1:
            self.usage()

        # Service commands
        commands = {
            'start': self.do_start,
            'stop': self.do_stop,
            'restart': self.do_restart,
            'status': self.do_status,
            'start-primary': self.do_start_primary,
            'demote': self.do_demote,
            'promote': self.do_promote
        }

        # Invalid command
        if not argv[1] in commands:
            self.usage()

        # Return the service command
        return commands[argv[1]]

    def _is_running(self, service):
        """
        Return (boolean, str) representing if the service is running or not.
        """
        proc     = Popen(['/usr/sbin/service', service, 'status'], stdout=PIPE, stderr=PIPE)
        out, err = proc.communicate()

        # Service is running
        for rstr in ['is running', 'start/running', 'currently running']:
            if rstr in out.rstrip():
                return True, out.rstrip()
        return False, out.rstrip()

    def _is_primary(self):
        """
        Return a boolean value indicating if this is a primary/active node
        for the service.
        """
        return True if self.host in self.cluster.active_nodes else False

    def _stop(self, service):
        """
        Wrapper for stopping a service.
        """
        if not self._is_running(service):
            print('service.{0}: already stopped...'.format(service))
        else:
            print('service.{0}: stopping...'.format(service), end='')

            # Attempt to start the service
            proc = Popen(['/usr/sbin/service', service, 'stop'], stdout=PIPE, stderr=PIPE)
            proc.communicate()

            # Service failed to start
            if proc.returncode != 0:
                print(self.colored('FAILED', 'red'))
            else:
                print(self.colored('SUCCESS', 'green'))

    def _start(self, service):
        """
        Wrapper for starting a service.
        """
        if self._is_running(service):
            print('service.{0}: already running...'.format(service))
        else:
            print('service.{0}: starting...'.format(service), end='')

            # Attempt to start the service
            proc = Popen(['/usr/sbin/service', service, 'start'], stdout=PIPE, stderr=PIPE)
            proc.communicate()

            # Service failed to start
            if proc.returncode != 0:
                print(self.colored('FAILED', 'red'))
            else:
                print(self.colored('SUCCESS', 'green'))

    def _status(self):
        """
        Show local service(s) status.
        """

        # Local service status message
        status_message = [
            '  {0}'.format(self.bold('local:'))
        ]

        # Generate local service status
        for service in self.local:
            running, stdout = self._is_running(service)
            status  = '{0} [ {1} ]'.format(self.colored('running...', 'green') if running else self.colored('stopped...', 'red'), stdout)

            # Append the local service status
            status_message.append('    service.{0}: {1}'.format(service, status))

        # Return the status message
        return '\n'.join(status_message)

    def _lock(self):
        """
        Generate a specified lockfile if defined before a restart.
        """
        if self.lock:
            with open(self.lock, 'w') as f:
                f.write('')

            # Grace period for any running checks to complete
            sleep(2)

    def _unlock(self):
        """
        Destroy a specified lockfile if defined before a restart.
        """
        if self.lock and path.isfile(self.lock):
            unlink(self.lock)

    def do_start(self, force=False):
        """
        Start the service.
        """

        # Node must be primary
        if not self._is_primary() and not force:
            print('\nCannot manually start service on a standby node! To make this node the new primary:')
            self.die('\n> service nitrophone start-primary\n')

        # Start all services
        for service in self.local:
            self._start(service)

    def do_stop(self, force=False):
        """
        Stop the service.
        """

        # Cannot stop on a primary node
        if self._is_primary() and not force:
            print('\nCannot manually stop service on a primary node! To make this node the new standby')
            print('issue the following command on the standby node:')
            self.die('\n> service nitrophone start-primary\n')

        # Stop all services
        for service in reversed(self.local):
            self._stop(service)

    def do_restart(self):
        """
        Restart the service.
        """

        # Server must be an active node
        if not self._is_primary():
            self.die('\nRestart commands can only be issued on primary/active nodes!\n')

        # Lock checks during restart
        self._lock()

        # Stop / start
        self.do_stop(force=True)
        self.do_start(force=True)

        # Unlock checks
        self._unlock()

    def do_status(self):
        """
        Show service status.
        """
        print(self.status_title('{0}.service:'.format(self.name)))
        print(self.cluster.status())
        print(self._status())
        print('')

    def do_start_primary(self):
        """
        Promote and start the current secondarys to primary nodes.
        """

        # Node is already primary
        if self._is_primary():
            self.die('\nNode is already primary/active!\n')

        # Begin promotion of secondary nodes
        self.cluster.promote_secondary()

        # Demote the current primary
        self.cluster.demote_primary()

        # Wait for demotion to complete
        self.cluster.demote_primary_wait()

        # Wait for secondaries to get promoted
        self.cluster.promote_secondary_wait()

        # Switch roles
        self.cluster.switch_roles()

        # Demotion/promotion completed
        self.cluster.demote_primary_complete()
        self.cluster.promote_secondary_complete()

    def do_promote(self):
        """
        Promote the secondary node after calling start-primary.
        """
        kvpath = '{0}/promote'.format(self.host)
        data   = self.kv.get(kvpath)

        # Start promotion
        if data == CHROLE.START:
            self._lock()
            self.kv.put(kvpath, CHROLE.WAIT)

        # Unlock after demotion completed
        if data == CHROLE.NULL:
            self.do_start(force=True)
            self._unlock()

    def do_demote(self):
        """
        Demote the current primary if starting up a secondary.
        """
        kvpath = '{0}/demote'.format(self.host)
        data   = self.kv.get(kvpath)

        # Start demotion
        if data == CHROLE.START:
            self._lock()
            self.do_stop(force=True)
            self.kv.put(kvpath, CHROLE.WAIT)

        # Unlock after demotion completed
        if data == CHROLE.NULL:
            self._unlock()

    def usage(self):
        """
        Print usage information.
        """
        self.die('Usage: service {0} {start|stop|restart|start-primary|status|demote}'.format(self.name))

    @classmethod
    def process(cls, name, consul_service, local_services=None, noop_lockfile=None):
        """
        Class method for handling service commands.
        """
        service = cls(name, consul_service, local_services, noop_lockfile)

        # Run service command
        service.command()
