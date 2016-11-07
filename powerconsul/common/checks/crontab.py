from os import path
from subprocess import Popen, PIPE

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
            'enabled': '/var/spool/cron/crontabs/{0}'.format(self.user),
            'disabled': '/var/spool/cron/crontabs.disabled/{0}'.format(self.user)
        }

    def enabled(self):
        """
        Check if a crontab is enabled or not.
        """
        if path.isfile(self.path.enabled):
            return True

    def ensure(self, expects=True, clustered=False, active=True):
        """
        Ensure a specific crontab state.
        """
        enabled  = self.enabled()
        msgAttrs = [
            'user={0}'.format(self.user),
            'enabled={0}'.format('yes' if enabled else 'no'),
            'expects={0}'.format('enabled' if expects else 'disabled'),
            'clustered={0}'.format('yes' if clustered else 'no')
        ]

        # If running in a cluster, append datacenter attribute to message
        if clustered:
            msgAttrs.append('active{0}={1}'.format(self.filterStr, 'yes' if active else 'no'))

        # Crontab should be enabled
        if expects == True:
            if running:
                POWERCONSUL.SHOW.passing('CRONTAB OK: {0}'.format(', '.join(msgAttrs)))
            POWERCONSUL.SHOW.critical('CRONTAB CRITICAL: {0}'.format(', '.join(msgAttrs)))

        # Crontab should be disabled
        if expects == False:
            if not running:
                POWERCONSUL.SHOW.passing('CRONTAB OK: {0}'.format(', '.join(msgAttrs)))
            POWERCONSUL.SHOW.critical('CRONTAB CRITICAL: {0}'.format(', '.join(msgAttrs)))
