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

    def running(self):
        """
        Check if a service is running or not.
        """
        proc     = Popen(['/usr/bin/env', 'service', self.name, 'status'], stdout=PIPE, stderr=PIPE)
        out, err = proc.communicate()

        # Failed to get status
        if proc.returncode != 0:
            POWERCONSUL.die('Failed to determine status for [{0}]: {1}'.format(self.name, err.rstrip()))

        # Service is running
        for rstr in ['is running', 'start/running']:
            if rstr in out.rstrip():
                return True
        return False

    def ensure(self, expects=True, clustered=False, active=True):
        """
        Ensure a specific service state.
        """
        running  = self.running()

        # Service should be running
        if expects == True:
            if running:
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
