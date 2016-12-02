Power Consul Service Management
===============================

The ``python-powerconsul`` package is a command-line utility designed to
work with a server's Consul agent:

-  Service/resource checks
-  Watching service health/state changes
-  Triggering actions based on service state changes

Limitations/Issues
~~~~~~~~~~~~~~~~~~
The following is a summary of known issues and limitations:

Tests/Documentation
'''''''''''''''''''
I have not gotten around to implementing unit tests yet. This should be done with Tox or something similar. Documentation is lacking, this should be done with good comments/docstrings and Sphinx.

Consul Agent
''''''''''''
This package assumes you have the Consul agent installed and running on your local system. Any command will fail if the agent is not installed and configured properly (https://www.consul.io/intro/getting-started/install.html).

Root Privileges
'''''''''''''''
Currently this must be installed and run as root in order to provide privileged access to system commands to implement the self-healing triggers. Ideally this package should be installed/configured/run in user space with sudo access to this specific command.

Cluster State
'''''''''''''
The cluster state is generated automatically from data stored in your Consul KV database. This will probably need a review and code cleanup, but for now it works as expected.

Installation/Upgrade
~~~~~~~~~~~~~~~~~~~~

Currently installation must be done against this repository:

Install
'''''''

You will need ``python-pip`` in order to install this package:

.. code:: sh

    # From master
    pip install git+ssh://github.com/powerhome/python-powerconsul.git

    # From a specific release
    pip install git+ssh://github.com/powerhome/python-powerconsul.git@<release_name>

    # From a specific branch
    pip install git+ssh://github.com/powerhome/python-powerconsul.git@<branch_name>

Upgrade
'''''''

Just pass the ``--upgrade`` flag to the PIP command:

.. code:: sh

    pip install --upgrade git+ssh://github.com/powerhome/python-powerconsul.git

Configuration
~~~~~~~~~~~~~

The Power Consul utility expects the presence of ``/root/.powerconsul.conf``. This can
be generated using ``powerconsul config bootstrap -C '<JSON String>'`` or deployed via
a configuration tool such as Puppet.

Example Configuration
'''''''''''''''''''''

.. code:: json

    {
      "serviceFilter": "^production-webserver[0-9]*$",
      "clusterKey": "cluster/production",
      "subVars": {
        "@ENV": "production",
        "@ROLE": "webserver",
        "@SERVER": "apache2"
      }
    }

serviceFilter
  This is used when filtering through Consul service checks to only include relevant hosts.
  By default when querying health status for a service, all services that share the same name
  (i.e., apacheService) will be returned. You can configure a regular expression here to limit
  the results to a specific subset of servers.
clusterKey
  This is the base key string used when looking up cluster information for a Consul service.
subVars
  An arbitrary dictionary of substitution keys and values which can be dynamically interpolated
  in trigger definitions.

Clustering
~~~~~~~~~~

For a check or trigger to be cluster aware, the following structure is
expected to exist in the Consul KV store:

.. code:: text

    <clusterKey>/<consulService>

By Datacenter
'''''''''''''

Nodes can be clustered into active/standby groups by their datacenters:

.. code:: json

    {
        "active_datacenters": ["hq"],
        "standby_datacenters": ["dr"]
    }

Nodes in the active datacenter(s) will be classified in the ``primary``
role. Nodes in the secondary datacenter(s) will be classified in the
``secondary`` role.

By Nodes
''''''''

Nodes can be clustered into active/standby groups by their hostnames:

.. code:: json

    {
        "active_nodes": ["node1", "node2"],
        "standby_nodes": ["node3", "node4"]
    }

Nodes in the active list will be classified in the ``primary`` role.
Nodes in the secondary list will be classified in the ``secondary``
role. This is the preferred method of clustering as doing it via datacenter has not been tested as extensively.

Cluster Filter
''''''''''''''

Depending on your configuration, you may want to do more fine-grained filtering. The
key values inside the filter block should be parseable regular expression strings. This
is useful if nodes share the same Consul service but should be grouped differently.

.. code:: json

    {
        "filter": {
            "^production-mysql-web[0-9]*$": {
                "active_nodes": ["production-mysql-web1"],
                "standby_nodes": ["production-mysql-web2"]
             },
            "^production-mysql-backend[0-9]*$": {
                "active_nodes": ["production-mysql-backend1"],
                "standby_nodes": ["production-mysql-backend2"]
             }
        }
    }

Standalone
''''''''''

Any checks/triggers that do not find any data in the expected KV path
will assume they are in the ``standalone`` role and will always attempt
to be running/healthy.

Checks
~~~~~~

The following are examples on how to set up different types of checks:

Service
'''''''

Service checks can be used to ensure standalone, or
active/standby groups of services. Both of the following arguments are
required:

.. code:: sh

    # <linuxService> is the local service name, i.e.: apache2
    # <consulService> is the check name defined by the Consul agent, i.e.: apacheWebService
    powerconsul check service -s <linuxService> -S <consulService>

Crontab
'''''''

The existence of a crontab for a specific user can be checked:

.. code:: sh

    # <username> is the crontab username, i.e.: myuser
    # <consulService> is the check name defined by the Consul agent, i.e.: myuserCrontab
    powerconsul check crontab -u <username> -S <consulService>
    # With a pattern search
    powerconsul check crontab -u <username> -S <consulService> -p "Something in the crontab"

Process
'''''''

This is a thin wrapper for the Nagios ``check_procs`` script (must be
available on the system):

.. code:: sh

    # <nagiosargs> are any arguments specific to the check_procs script
    # <consulService> is the check name defined by the Consul agent, i.e.: myuserCrontab
    powerconsul check process -n '-c 1:1 -C processName' -S <consulService>

See (https://www.consul.io/docs/agent/checks.html) for how to set up service checks with the Consul agent.

Watchers
~~~~~~~~

Watcher handlers are relatively simply and should be installed for both
the critical and warnings states:

.. code:: sh

    powerconsul watch warning
    powerconsul watch critical

This will look for any health checks that change to a critical/warning
state for the local node, and will trigger events. See (https://www.consul.io/docs/agent/watches.html#checks) for how to set this up.

Triggers
~~~~~~~~

Triggers are called by watchers:

.. code:: sh

    powerconsul trigger critical
    powerconsul trigger warning

Triggers expect certain values to exist in the Consul KV store:

.. code:: text

    triggers/<consulService>/<role>/<state>

role
  This can be either primary, secondary, or standalone
state
  This can be either critical or warning

If a particular service goes into a critical/warning state, the trigger
will look to the KV store to determine what action it should run. You may
use any of the keys in the subVars configuration directive for dynamic
substitution.

Shell Command
'''''''''''''

A shell command can be run if a service goes into a warning/critical
state:

.. code:: text

    /usr/bin/env service <linuxService> start

BASH Command
''''''''''''

A bash script can be run if a service goes into a warning/critical
state:

.. code:: text

    #!/bin/bash
    cd /to/some/place
    echo "Horray!"
    /usr/bin/env do --something

Logging
~~~~~~~~

Logs are broken down by action (check/watch/trigger) and further by state/service (triggers) or resource/service (checks):

.. code:: text

    user@hostname:~# cd /var/log/powerconsul
    user@hostname:/var/log/powerconsul# find . -type f -name *.log
    ./trigger/sshd.warning.log
    ./trigger/puppetAgent.critical.log
    ./trigger/ntpd.warning.log
    ./trigger/sssd.critical.log
    ./trigger/sssd.warning.log
    ./watch/warning.log
    ./watch/critical.log
    ./check/service.sshd.log
    ./check/service.ntpd.log
    ./check/service.sssd.log
    ./check/service.puppetAgent.log
