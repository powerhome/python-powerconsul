from os import rename, path, makedirs

CRONTABS = '/var/spool/cron/crontabs'
CRONTABS_DISABLED = '/var/spool/cron/crontabs.disabled'

class PowerConsul_Actions(object):
    """
    Command actions to be run by triggered events.
    """
    @classmethod
    def enableCrontab(cls, **kwargs):
        cronUser    = kwargs.get('user')
        cronPath    = '{0}/{1}'.format(CRONTABS_DISABLED, cronUser)
        cronEnabled = '{0}/{1}'.format(CRONTABS, cronUser)

        # Check if the crontab is in the disabled directory
        if not path.isfile(cronPath):
            raise Exception("Cannot enable crontab for user [{0}]: file not found: {1}".format(cronUser, cronPath))

        # Enable the crontab
        rename(cronPath, cronEnabled)
        POWERCONSUL.LOG.info('Enabled crontab for user: {0}'.format(cronUser))

    @classmethod
    def disableCrontab(cls, **kwargs):
        cronUser     = kwargs.get('user')
        cronPath     = '{0}/{1}'.format(CRONTABS, cronUser)
        cronDisabled = '{0}/{1}'.format(CRONTABS_DISABLED, cronUser)

        # Make sure the disabled directory exists
        if not path.isdir(CRONTABS_DISABLED):
            makedirs(CRONTABS_DISABLED)

        # Check if the crontab is in the disabled directory
        if not path.isfile(cronPath):
            raise Exception("Cannot disable crontab for user [{0}]: file not found: {1}".format(cronUser, cronPath))

        # Enable the crontab
        rename(cronPath, cronDisabled)
        POWERCONSUL.LOG.info('Disabled crontab for user: {0}'.format(cronUser))

    @classmethod
    def get(cls, method):
        if not hasattr(cls, method):
            raise Exception("Unsupported action: {0}".format(method))
        return getattr(cls, method)

    @classmethod
    def parseArgs(cls, argsStr):
        argsObj  = {}
        argsList = argsStr.split(',')
        for argElem in argsList:
            argAttrs = argElem.split('=')
            argsObj[argAttrs[0].lstrip().rstrip()] = argAttrs[1]
        return argsObj
