import re
from os import environ
from sys import argv, exit
from json import loads as json_loads
from argparse import ArgumentParser, RawTextHelpFormatter

# PowerConsul Libraries
from powerconsul.common.handlers import PowerConsulHandlers
from powerconsul.common.args.options import OPTIONS

def get_base_commands():
    """
    Return base command attributes.
    """
    commands = {
        "help": "Get help for a specific command: powerconsul help <command>"
    }
    for handler, cls in PowerConsulHandlers().all().iteritems():
        commands[handler] = cls.desc['summary']
    return commands

class PowerConsulArgs_Base(object):
    """
    Argument attributes for the base PowerConsul interface.
    """

    # Description
    desc       = {
        "title": "Power Consul",
        "summary": "Command line tools for managing Power Consul HA services.",
        "usage": "\n> powerconsul [command] [subcommand] [options]\n> powerconsul help [target]"
    }

    # Target / options / commands
    use_target = True
    options    = []
    commands   = get_base_commands()

class PowerConsulArg_Commands(object):
    """
    Wrapper class for storing command attributes.
    """
    def __init__(self, cmds):
        self._cmds = cmds

    def keys(self):
        """
        Return a listing of handler command keys.
        """
        return self._cmds.keys()

    def help(self):
        """
        Return the handlers help prompt
        """
        cmds_str = ''
        for cmd, help in self._cmds.iteritems():
            if isinstance(help, str):
                cmds_str += "> {0}: {1}\n".format(cmd, help)
            else:
                cmds_str += "> {0}: {1}\n".format(cmd, help['help'])
        return ("Available Commands:\n{0}\n".format(cmds_str))

class PowerConsulArg_Option(object):
    """
    Wrapper class for storing option attributes.
    """
    def __init__(self, **opts):
        """
        :param    short: Option short key
        :type     short: str
        :param     long: Option long key
        :type      long: str
        :param     help: Option help prompt
        :type      help: str
        :param   action: Argparse action
        :type    action: str
        """

        # Argparse options
        self.short    = '-{0}'.format(opts['short'])
        self.long     = '--{0}'.format(opts['long'])
        self.help     = opts['help']
        self.action   = opts['action']

class PowerConsulArgsInterface(object):
    """
    Load client arguments from the manifest.
    """
    def __init__(self, opts, cmds):
        self._opts = opts
        self._cmds = cmds

        # Commands / options
        self.commands = PowerConsulArg_Commands(cmds)
        self.options  = []

        # Options
        for opt in self._opts:
            self.options.append(PowerConsulArg_Option(**opt))

class PowerConsulArgs(object):
    """
    Public class object for constructing arguments object for base
    and sub-commands.
    """
    def __init__(self, desc, opts, cmds, base):
        self.desc = desc
        self.opts = opts
        self.cmds = cmds
        self.base = base

         # Arguments interface / container
        self.interface = PowerConsulArgsInterface(opts=opts, cmds=cmds)
        self.container = {}

        # Parse command line arguments
        self._parse()

    def list(self):
        """
        Return a list of argument keys.
        """
        return self.container.keys()

    def dict(self):
        """
        Return a dictionary of argument key/values.
        """
        return self.container

    def set(self, k, v):
        """
        Set a new argument or change the value.
        """
        self.container[k] = v

    def get(self, k, default=None, use_json=False, required=False):
        """
        Retrieve an argument passed via the command line.
        """

        # Get the value from argparse
        _raw = self.container.get(k)
        _val = (_raw if _raw else default) if not isinstance(_raw, list) else (_raw[0] if _raw[0] else default)

        # No value and argument required
        if not _val and required:
            POWERCONSUL.die(required)

        # Return the value
        return _val if not use_json else json_loads(_val)

    def _desc(self):
         return "{0}\n\n{1}.\n".format(self.desc['title'], self.desc['summary'])

    def _parse(self):
        """
        Parse command line arguments.
        """

        # Create a new argument parsing object and populate the arguments
        self.parser = ArgumentParser(description=self._desc(), formatter_class=RawTextHelpFormatter, usage=self.desc['usage'])
        self.parser.add_argument('command', help=self.interface.commands.help())

        # Base command specific arguments
        if self.base:
            self.parser.add_argument('target', nargs='?', default=None, help='Target command for help')

        # Load client switches
        for arg in self.interface.options:
            self.parser.add_argument(arg.short, arg.long, help=arg.help, action=arg.action)

        # No parameters given
        if len(argv) == 1:
            self.help()
            exit(0)

        # Parse base command options
        argv.pop(0)
        self.container = vars(self.parser.parse_args(argv))

    def help(self):
        """
        Print the help prompt.
        """
        self.parser.print_help()

    @staticmethod
    def handlers():
        """
        Return a list of supported handlers.
        """
        return [h for h in POWERCONSUL.HANDLERS.all().keys()]

    @classmethod
    def construct(cls, desc=PowerConsulArgs_Base.desc, opts=PowerConsulArgs_Base.options, cmds=PowerConsulArgs_Base.commands, base=True):
        """
        Method for constructing and returning an arguments handler.

        :param desc: The description for the command
        :type  desc: dict
        :param opts: Any options the command takes
        :type  opts: list
        :param cmds: Additional subcommands
        :type  cmds: dict
        """
        POWERCONSUL.ARGS = cls(desc, opts, cmds, base)
