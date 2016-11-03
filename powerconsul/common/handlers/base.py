import json

class PowerConsulHandler_Base(object):
    """
    Base class for command handlers.
    """
    def __init__(self, handler):
        POWERCONSUL.ARGS.construct(
            desc = self.desc,
            opts = self.options,
            cmds = self.commands,
            base = False
        )

        # Handler / command
        self.handler     = handler
        self.command     = POWERCONSUL.ARGS.get('command')

    def run(self):
        """
        Public method for running the handler.
        """

        # Unsupported command
        if not self.command in self.commands:
            POWERCONSUL.ARGS.help()
            POWERCONSUL.die("\nUnsupported command: {0}\n".format(self.command))

        # Run the command
        getattr(self, self.command)()

    def help(self):
        """
        Return the help prompt for the command handler.
        """
        POWERCONSUL.ARGS.help()
