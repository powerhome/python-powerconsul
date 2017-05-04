from subprocess import Popen, PIPE

from powerconsul.common.checks import Check_Base

class Check_Service(Check_Base):
    """
    Class object representing a service check.
    """
    def __init__(self):
        super(Check_Service, self).__init__('service')

        # Service attributes
        self.name = POWERCONSUL.ARGS.get('service', required='Local service name required: powerconsul check service -s <name>')

    def running(self, expects=True):
        """
        Check if a service is running or not.
        """
        proc     = Popen(['/usr/bin/env', 'service', self.name, 'status'], stdout=PIPE, stderr=PIPE)
        out, err = proc.communicate()

        # Process table check
        if self.checkPS():
            return True

        # Noop file check
        if self.checkNoop():
            return expects

        # Unrecognized service
        if proc.returncode == 1:
            POWERCONSUL.LOG.critical('Failed to determine status for [{0}]: unrecognized service'.format(self.name), method='running', die=True)

        # Service is running
        for rstr in ['is running', 'start/running', 'currently running']:
            if rstr in out.rstrip():
                return True
        return False

    def ensure(self, expects=True, clustered=False, active=True):
        """
        Ensure a specific service state.
        """
        running  = self.running(expects=expects)

        # Service should be running
        if expects == True:
            if running:
                self.setDNS(True)
                POWERCONSUL.OUTPUT.passing({
                    'type': 'service',
                    'service': self.name,
                    'expects': expects,
                    'clustered': clustered
                })
            POWERCONSUL.OUTPUT.critical({
                'type': 'service',
                'service': self.name,
                'expects': expects,
                'clustered': clustered
            })

        # Service should be stopped
        if expects == False:
            if not running:
                self.setDNS(False)
                POWERCONSUL.OUTPUT.passing({
                    'type': 'service',
                    'service': self.name,
                    'expects': expects,
                    'clustered': clustered
                })
            POWERCONSUL.OUTPUT.critical({
                'type': 'service',
                'service': self.name,
                'expects': expects,
                'clustered': clustered
            })
