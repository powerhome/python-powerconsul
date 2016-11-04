# -*- coding: utf-8 -*-
__version__ = '0.1-1'

import json
from sys import argv, exit

# Power Consul modules
import powerconsul.common.logger as logger

class PowerConsul(object):
    """
    Public class for running Power Consul utilities.
    """
    @classmethod
    def _run_handler(cls, handler):
        """
        Private method for loading subcommand handler.
        """
        argv.pop(0)

        # Load the command handler
        command = POWERCONSUL.ensure(POWERCONSUL.HANDLERS.get(argv[0]),
            isnot = None,
            error = 'Cannot load unsupported command: {0}'.format(argv[0]),
            code  = 1)

        # Setup the logger
        POWERCONSUL.LOG = logger.create(command)

        # Run the target command
        return command().run()

    @classmethod
    def run(cls):
        """
        Public method for running Power Consul utilities.
        """

        # Must be run as root
        POWERCONSUL.ensure_root()

        # Supported handlers
        handlers = POWERCONSUL.ARGS.handlers()

        # Pass to handler
        if (len(argv) > 1) and (argv[1] in handlers):
            cls._run_handler(argv[1])

        # Base commands
        else:

            # Construct base argument parser
            POWERCONSUL.ARGS.construct()

            # If getting help for a command
            if POWERCONSUL.ARGS.get('command') == 'help':

                # Get the target handler
                target = POWERCONSUL.ensure(POWERCONSUL.ARGS.get('target'),
                    isnot = None,
                    error = 'Usage: powerconsul help [command]',
                    code  = 1)

                # Make sure the target is supported
                command = POWERCONSUL.ensure(POWERCONSUL.HANDLERS.get(target),
                    isnot = None,
                    error = 'Cannot load help for unsupported command: {0}'.format(target),
                    code  = 1)

                # Return the command help
                return command().help()

            # Unsupported command
            POWERCONSUL.ARGS.help()
            POWERCONSUL.die('\nUnsupported command: {0}\n'.format(POWERCONSUL.ARGS.get('command')))
