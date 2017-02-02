import json
from sys import stdout, exit
from subprocess import Popen, PIPE

# Power Consul modules
from powerconsul.common.args.options import OPTIONS
from powerconsul.common.handlers.base import PowerConsulHandler_Base
from powerconsul.common.checks.service import Check_Service
from powerconsul.common.checks.crontab import Check_Crontab
from powerconsul.common.checks.process import Check_Process

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
        },
        {
            "short": "n",
            "long": "nagiosargs",
            "help": "A string of arguments to pass to a Nagios script.",
            "action": "store"
        },
        {
            "short": "P",
            "long": "procstr",
            "help": "Look for a string in the process table to indicate an expected task during a critical check.",
            "action": "store"
        },
        {
            "short": "R",
            "long": "procre",
            "help": "Look for a regular expression in the process table to indicate an expected task during a critical check.",
            "action": "store"
        },
        {
            "short": "F",
            "long": "noopfile",
            "help": "If this file exists assume that all checks should pass (such as a deploy lockfile)",
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
        },
        "process": {
            "help": "Check a process running on the system."
        }
    }

    def __init__(self):
        super(PowerConsulHandler_Checks, self).__init__(self.id)

    def _check(self, check):
        """
        Wrapper method for running checks on a defined check object.
        """

        """ STANDALONE """
        if not POWERCONSUL.CLUSTER.active:
            check.ensure()

        """ CLUSTERED """

        # All resources active
        if not POWERCONSUL.CLUSTER.hasStandby:
            check.ensure(clustered=True)

        """ ACTIVE/STANDBY """
        check.byDatacenter()
        check.byNodes()

    def process(self):
        """
        Check for a running process.
        """
        self._check(Check_Process())

    def crontab(self):
        """
        Check the crontab for a user.
        """
        self._check(Check_Crontab())

    def service(self):
        """
        Check a service state.
        """
        self._check(Check_Service())
