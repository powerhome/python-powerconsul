class PowerConsul_Actions(object):
    """
    Command actions to be run by triggered events.
    """
    @classmethod
    def enableCrontab(cls, **kwargs):
        cronUser = kwargs.get('user')

    @classmethod
    def disableCrontab(cls, **kwargs):
        cronUser = kwargs.get('user')

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
