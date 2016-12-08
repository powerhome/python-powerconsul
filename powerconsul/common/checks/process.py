from os import path
from subprocess import Popen, PIPE

from powerconsul.common.checks import Check_Base

class Check_Process(Check_Base):
    """
    Class object representing a process check.
    """
    def __init__(self):
        super(Check_Process, self).__init__('process')

        # Nagios check_procs script
        self.nagiosScript = '/usr/lib/nagios/plugins/check_procs'

        # Nagios script arguments
        self.nagiosArgs   = POWERCONSUL.ARGS.get('nagiosargs',
            required='Nagios arguments required: powerconsul check process -n \'<nagiosArgs>\''
        )

    def checkNagios(self):
        """
        Check if a process is healthy via Nagios checks.
        """

        # The Nagios script must exist
        if not path.isfile(self.nagiosScript):
            POWERCONSUL.LOG.critical('Unable to location Nagios process check script: {0}'.format(self.nagiosScript), method='checkNagios', die=True)

        # Execute the health check
        proc     = Popen([self.nagiosScript] + self.nagiosArgs.split(' '), stdout=PIPE, stderr=PIPE)
        out, err = proc.communicate()

        # Failed to run Nagios check (invalid syntax)
        if proc.returncode == 3:
            POWERCONSUL.LOG.critical('Failed to run Nagios check [{0}]: {1}'.format(self.nagiosScript, err.rstrip()), method='checkNagios', die=True)

        # Return the exit code and output
        return proc.returncode, out.rstrip()

    def ensure(self, expects=True, clustered=False, active=True):
        """
        Ensure a specific service state.
        """
        code, output = self.checkNagios()

        # Process should be running/healthy
        if expects == True:

            # Passing
            if code == 0:
                self.setDNS(True)
                POWERCONSUL.OUTPUT.passing({
                    'type': 'process',
                    'nagiosScript': self.nagiosScript,
                    'nagiosArgs': self.nagiosArgs,
                    'nagiosOutput': output,
                    'expects': expects,
                    'clustered': clustered
                })

            # Warning
            if code == 1:
                POWERCONSUL.OUTPUT.warning({
                    'type': 'process',
                    'nagiosScript': self.nagiosScript,
                    'nagiosArgs': self.nagiosArgs,
                    'nagiosOutput': output,
                    'expects': expects,
                    'clustered': clustered
                })

            # Critical
            if code == 2:
                POWERCONSUL.OUTPUT.critical({
                    'type': 'process',
                    'nagiosScript': self.nagiosScript,
                    'nagiosArgs': self.nagiosArgs,
                    'nagiosOutput': output,
                    'expects': expects,
                    'clustered': clustered
                })

        # Process should be stopped
        if expects == False:

            # Passing (Nagios check == critical)
            if code == 2:
                self.setDNS(False)
                POWERCONSUL.OUTPUT.passing({
                    'type': 'process',
                    'nagiosScript': self.nagiosScript,
                    'nagiosArgs': self.nagiosArgs,
                    'nagiosOutput': output,
                    'expects': expects,
                    'clustered': clustered
                })

            # Critical (Nagios check == warning/passing)
            if code in [0, 1]:
                POWERCONSUL.OUTPUT.critical({
                    'type': 'process',
                    'nagiosScript': self.nagiosScript,
                    'nagiosArgs': self.nagiosArgs,
                    'nagiosOutput': output,
                    'expects': expects,
                    'clustered': clustered
                })
