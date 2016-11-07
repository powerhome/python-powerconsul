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
        msgAttrs = [
            'service={0}'.format(self.name),
            'running={0}'.format('yes' if running else 'no'),
            'expects={0}'.format('running' if expects else 'stopped'),
            'clustered={0}'.format('yes' if clustered else 'no')
        ]

        # If running in a cluster, append datacenter attribute to message
        if clustered:
            msgAttrs.append('active{0}={1}'.format(self.filterStr, 'yes' if active else 'no'))

        # Service should be running
        if expects == True:
            if running:
                POWERCONSUL.SHOW.passing('SERVICE OK: {0}'.format(', '.join(msgAttrs)))
            POWERCONSUL.SHOW.critical('SERVICE CRITICAL: {0}'.format(', '.join(msgAttrs)))

        # Service should be stopped
        if expects == False:
            if not running:
                POWERCONSUL.SHOW.passing('SERVICE OK: {0}'.format(', '.join(msgAttrs)))
            POWERCONSUL.SHOW.critical('SERVICE CRITICAL: {0}'.format(', '.join(msgAttrs)))
