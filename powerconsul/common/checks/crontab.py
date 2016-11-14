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
        self.name = POWERCONSUL.ARGS.get('user', required='Local user name required: powerconsul check crontab -u <username>')

        # Crontab paths
        self.path = {
            'enabled': '/var/spool/cron/crontabs/{0}'.format(self.name),
            'disabled': '/var/spool/cron/crontabs.disabled/{0}'.format(self.name)
        }

    def enabled(self):
        """
        Check if a crontab is enabled or not.
        """
        if path.isfile(self.path['enabled']):
            cron_stat  = stat(self.path['enabled'])

            # Check ownership on crontab
            cron_owner = getpwuid(cron_stat.st_uid)[0]
            cron_group = getgrgid(cron_stat.st_gid)[0]

            # Should be <user>/root
            if not (cron_owner == self.name) or not (cron_group == 'crontab'):
                POWERCONSUL.OUTPUT.warning('Incorrect permissions "{0}:{1}" for <{2}> crontab, expected "{3}:crontab"'.format(cron_owner, cron_group, self.name, self.name))
            return True

        # Crontab is disabled, but does not exist in '/var/spool/cron/crontabs.disabled'
        if not path.isfile(self.path['disabled']):
            POWERCONSUL.LOG.info('Crontab for [{0}] disabled, but does not exist in: /var/spool/cron/crontabs.disabled'.format(self.name))
        return False

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
                    'clustered': clustered
                })
            POWERCONSUL.OUTPUT.critical({
                'type': 'crontab',
                'crontab': self.name,
                'expects': expects,
                'clustered': clustered
            })

        # Crontab should be disabled
        if expects == False:
            if not enabled:
                self.setDNS(False)
                POWERCONSUL.OUTPUT.passing({
                    'type': 'crontab',
                    'crontab': self.name,
                    'expects': expects,
                    'clustered': clustered
                })
            POWERCONSUL.OUTPUT.critical({
                'type': 'crontab',
                'crontab': self.name,
                'expects': expects,
                'clustered': clustered
            })
