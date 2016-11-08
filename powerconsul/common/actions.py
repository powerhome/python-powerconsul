from os import rename, path

class PowerConsul_Actions(object):
    """
    Command actions to be run by triggered events.
    """
    @classmethod
    def enableCrontab(cls, **kwargs):
        cronUser    = kwargs.get('user')
        cronPath    = '/var/spool/cron/crontabs.disabled/{0}'.format(cronUser)
        cronEnabled = '/var/spool/cron/crontabs/{0}'.format(cronUser)

        # Check if the crontab is in the disabled directory
        if not path.isfile(cronPath):
            raise Exception("Cannot enable crontab for user [{0}]: file not found: {1}".format(cronUser, cronPath))

        # Enable the crontab
        rename(cronPath, cronEnabled)
        POWERCONSUL.LOG.info('Enabled crontab for user: {0}'.format(cronUser))

    @classmethod
    def disableCrontab(cls, **kwargs):
        cronUser     = kwargs.get('user')
        cronPath     = '/var/spool/cron/crontabs/{0}'.format(cronUser)
        cronDisabled = '/var/spool/cron/crontabs.disabled/{0}'.format(cronUser)

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
