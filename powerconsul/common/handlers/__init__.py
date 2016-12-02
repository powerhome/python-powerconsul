from powerconsul.common import import_class

class PowerConsulHandlers(object):
    """
    Class object for loading command handlers.
    """
    def _get_handler_args(self, handler):
        """
        Private method for returning handler argument attributes.
        """
        try:
            return {
                "help": self._handlers.get(handler).help,
                "options": self._handlers.get(handler).options,
                "commands": self._handlers.get(handler).commands
            }
        except Exception as e:
            POWERCONSUL.die('Failed to retrieve handler attributes: {0}'.format(str(e)))

    def all(self):
        """
        Return all available handlers.
        """
        return {
            "watch": import_class('PowerConsulHandler_Watchers', 'powerconsul.common.handlers.watchers', init=False),
            "trigger": import_class('PowerConsulHandler_Triggers', 'powerconsul.common.handlers.triggers', init=False),
            "check": import_class('PowerConsulHandler_Checks', 'powerconsul.common.handlers.checks', init=False),
            "config": import_class('PowerConsulHandler_Config', 'powerconsul.common.handlers.config', init=False)
        }

    def get_args(self, handler=None):
        """
        Construct and return argument attributes for a single or all handlers.
        """
        if handler:
            return self._get_handler_args(handler)

        # Arguments for all handlers
        args = {}
        for h in self._handlers.keys():
            args[h] = self._get_handler_args(h)
        return args

    def get(self, handler):
        """
        Retrieve and initialize a command handler.
        """
        return POWERCONSUL.ensure(self.all().get(handler, None),
            isnot = None,
            error = 'Attempted to load unsupported handler: {0}'.format(handler),
            code  = 1)
