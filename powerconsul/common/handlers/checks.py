import json
from sys import stdout, exit
from subprocess import Popen, PIPE

# Power Consul modules
from powerconsul.common.args.options import OPTIONS
from powerconsul.common.handlers.base import PowerConsulHandler_Base
from powerconsul.common.checks.service import Check_Service
from powerconsul.common.checks.crontab import Check_Crontab

class PowerConsulHandler_Checks(PowerConsulHandler_Base):
    """
    Class object for managing custom Consul checks.
    """
    id      = 'check'

    # Command description
    desc    = {
        "title": "Power Consul Triggers",
        "summary": "Trigger events on service state changes.",
        "usage": "powerconsul trigger [action] [options]"
    }

    # Supported options
    options = [
        {
            "short": "s",
            "long": "service",
            "help": "The name of the local service to check the status of.",
            "action": "store"
        },
        {
            "short": "S",
            "long": "consulservice",
            "help": "The name of the Consul service to check against.",
            "action": "store"
        },
        {
            "short": "u",
            "long": "user",
            "help": "A local user account for supported checks.",
            "action": "store"
        },
        {
            "short": "p",
            "long": "pattern",
            "help": "A pattern to search for in the target resource.",
            "action": "store"
        }
    ] + OPTIONS

    # Supported actions
    commands = {
        "service": {
            "help": "Check a service running on the system."
        },
        "crontab": {
            "help": "Check a user's crontab on the system."
        }
    }

    def __init__(self):
        super(PowerConsulHandler_Checks, self).__init__(self.id)

    def crontab(self):
        """
        Check the crontab for a user.
        """
        crontab = Check_Crontab()

        """ STANDALONE """
        if not POWERCONSUL.CLUSTER.active:
            crontab.ensure()

        """ CLUSTERED """

        # All services active
        if not POWERCONSUL.CLUSTER.hasStandby:
            crontab.ensure(clustered=True)

        """ ACTIVE/STANDBY """
        crontab.byDatacenter()
        crontab.byNodes()

    def service(self):
        """
        Check a service state.
        """
        service = Check_Service()

        """ STANDALONE """
        if not POWERCONSUL.CLUSTER.active:
            service.ensure()

        """ CLUSTERED """

        # All services active
        if not POWERCONSUL.CLUSTER.hasStandby:
            service.ensure(clustered=True)

        """ ACTIVE/STANDBY """
        service.byDatacenter()
        service.byNodes()
