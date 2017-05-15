from subprocess import Popen, PIPE

from powerconsul.common.checks import Check_Base

class Check_ServiceGroup(Check_Base):
    """
    Class object representing a logical service group check.
    """
    def __init__(self):
        super(Check_ServiceGroup, self).__init__('service')

        # Service attributes
        self.services = POWERCONSUL.ARGS.get('service', required='Local service names required: powerconsul check servicegroup -s <name1>,<name2>').split(',')

    def running(self, expects):
        """
        Check if a service is running or not.
        """
        status   = []

        # Process table check
        if self.checkPS():
            return True

        # Noop file check
        if self.checkNoop():
            return expects

        # Check every service
        for service in self.services:
            proc     = Popen(['/usr/bin/env', 'service', service, 'status'], stdout=PIPE, stderr=PIPE)
            out, err = proc.communicate()

            # Unrecognized service
            if proc.returncode == 1:
                POWERCONSUL.LOG.critical('Failed to determine status for [{0}]: unrecognized service'.format(self.name), method='running', die=True)

            # Service is running
            is_running = False
            for rstr in ['is running', 'start/running', 'currently running']:
                if rstr in out.rstrip():
                    is_running = True
            POWERCONSUL.LOG.info('servicegroup.service "{0}" is {1}...'.format(service, ('running' if is_running else 'stopped')), method='running')
            status.append(is_running)

        # All services should be running
        if expects:
            return all(status)

        # All service should be stopped
        else:
            return True if (True in status) else False


    def ensure(self, expects=True, clustered=False, active=True):
        """
        Ensure a specific service state.
        """
        running  = self.running(expects)

        # Service should be running
        if expects == True:
            if running:
                self.setDNS(True)
                POWERCONSUL.OUTPUT.passing({
                    'type': 'servicegroup',
                    'services': self.services,
                    'expects': expects,
                    'clustered': clustered
                })
            POWERCONSUL.OUTPUT.critical({
                'type': 'servicegroup',
                'services': self.services,
                'expects': expects,
                'clustered': clustered
            })

        # Service should be stopped
        if expects == False:
            if not running:
                self.setDNS(False)
                POWERCONSUL.OUTPUT.passing({
                    'type': 'servicegroup',
                    'services': self.services,
                    'expects': expects,
                    'clustered': clustered
                })
            POWERCONSUL.OUTPUT.critical({
                'type': 'servicegroup',
                'services': self.services,
                'expects': expects,
                'clustered': clustered
            })
