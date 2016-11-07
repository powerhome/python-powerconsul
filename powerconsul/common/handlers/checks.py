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
            "action": "store",
            "required": True
        },
        {
            "short": "S",
            "long": "consulservice",
            "help": "The name of the Consul service to check against.",
            "action": "store"
        },
        {
            "short": "c",
            "long": "clustered",
            "help": "Is this service part of a cluster or not (default=False)?",
            "action": "store_true"
        },
        {
            "short": "d",
            "long": "standbydc",
            "help": "The standby datacenter for this service.",
            "action": "store"
        },
        {
            "short": "D",
            "long": "activedc",
            "help": "The active datacenter for this service.",
            "action": "store"
        },
        {
            "short": "n",
            "long": "standbynodes",
            "help": "A list of standby node hostnames: i.e., node1,node2",
            "action": "store"
        },
        {
            "short": "N",
            "long": "activenodes",
            "help": "A list of active node hostnames: i.e., node3,node4",
            "action": "store"
        },
        {
            "short": "u",
            "long": "user",
            "help": "A local user account for supported checks.",
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
        if not crontab.clustered:
            crontab.ensure()

        """ CLUSTERED """

        # All services active
        if crontab.allActive:
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
        if not service.clustered:
            service.ensure()

        """ CLUSTERED """

        # All services active
        if service.allActive:
            service.ensure(clustered=True)

        """ ACTIVE/STANDBY """
        service.byDatacenter()
        service.byNodes()
