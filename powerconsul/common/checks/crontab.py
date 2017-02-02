from pwd import getpwuid
from grp import getgrgid
from os import path, stat
from subprocess import Popen, PIPE

# Power Consul modules
from powerconsul.common.checks import Check_Base

class Check_Crontab(Check_Base):
    """
    Class object representing a crontab check.
    """
    def __init__(self):
        super(Check_Crontab, self).__init__('crontab')

        # Crontab attributes
        self.name    = POWERCONSUL.ARGS.get('user', required='Local user name required: powerconsul check crontab -u <username>')
        self.pattern = POWERCONSUL.ARGS.get('pattern')
        self.path    = '/var/spool/cron/crontabs/{0}'.format(self.name)

        # Custom error string
        self.error   = ''

    def enabled(self):
        """
        Check if a crontab is enabled or not.
        """

        # Noop file
        if self.checkNoop():
            return True

        # Crontab does not exist
        if not path.isfile(self.path):
            self.error = 'Crontab file not found: {0}'.format(self.path)
            return False

        # Check ownership on crontab
        cron_stat  = stat(self.path)
        cron_owner = getpwuid(cron_stat.st_uid)[0]
        cron_group = getgrgid(cron_stat.st_gid)[0]

        # Should be <user>/crontab
        if not (cron_owner == self.name) or not (cron_group == 'crontab'):
            self.error = 'Incorrect permissions "{0}:{1}" for <{2}> crontab, expected "{3}:crontab"'.format(cron_owner, cron_group, self.name, self.name)
            return False

        # If searching for a pattern
        if self.pattern:
            foundPattern = False
            with open(self.path, 'r') as f:
                for line in f.readlines():
                    if self.pattern in line:
                        foundPattern = True
            if not foundPattern:
                self.error = 'Failed to find pattern [{0}] in crontab: {1}'.format(self.pattern, self.path)
                return False

        # Make sure it contains lines other then comments
        onlyComments = True
        with open(self.path, 'r') as f:
            for line in f.readlines():
                if not line.startswith('#'):
                    onlyComments = False

        # Crontab only contains comments
        if onlyComments:
            self.error = 'Crontab only contains comment lines: {0}'.format(self.path)
            return False

        # Crontab exists and is enabled
        return True

    def ensure(self, expects=True, clustered=False, active=True):
        """
        Ensure a specific crontab state.
        """
        enabled = self.enabled()

        # Crontab should be enabled
        if expects == True:
            if enabled:
                self.setDNS(True)
                POWERCONSUL.OUTPUT.passing({
                    'type': 'crontab',
                    'crontab': self.name,
                    'expects': expects,
                    'clustered': clustered,
                    'pattern': self.pattern
                })
            POWERCONSUL.OUTPUT.critical({
                'type': 'crontab',
                'crontab': self.name,
                'expects': expects,
                'clustered': clustered,
                'pattern': self.pattern,
                'error': self.error
            })

        # Crontab should be disabled
        if expects == False:
            if not enabled:
                self.setDNS(False)
                POWERCONSUL.OUTPUT.passing({
                    'type': 'crontab',
                    'crontab': self.name,
                    'expects': expects,
                    'clustered': clustered,
                    'pattern': self.pattern
                })
            POWERCONSUL.OUTPUT.critical({
                'type': 'crontab',
                'crontab': self.name,
                'expects': expects,
                'clustered': clustered,
                'pattern': self.pattern,
                'error': 'Crontab is enabled: {0}'.format(self.path)
            })
