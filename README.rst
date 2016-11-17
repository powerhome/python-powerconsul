Power Consul Service Management
===============================

The ``python-powerconsul`` package is a command-line utility designed to
work with a server's Consul agent:

-  Service checks
-  Watching service health/state changes
-  Triggering actions based on service state changes

Installation/Upgrade
~~~~~~~~~~~~~~~~~~~~

You must have access to the
https://github.com/powerhome/python-powerconsul repository in order to
install directly from the repository.

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

Clustering
~~~~~~~~~~

For a check or trigger to be cluster aware, the following structure is
expected to exist in the Consul KV store:

.. code:: text

    cluster/<environment>/<consulService>

    EXAMPLE VALUES:
    environment: production
    consulService: myServiceCheckName

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
        "standby_nodes": ["node3", "nod4"]
    }

Nodes in the active list will be classified in the ``primary`` role.
Nodes in the secondary list will be classified in the ``secondary``
role.

Standalone
''''''''''

Any checks/triggers that do not find any data in the expected KV path
will assume they are in the ``standalone`` role and will always attempt
to be running/healthy.

Checks
~~~~~~

The following are examples on how to set up different types of checks:
##### Service Service checks can be used to ensure standalone, or
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
    powerconsul check crontab -n '-c 1:1 -C processName' -S <consulService>

Watchers
~~~~~~~~

Watcher handlers are relatively simply and should be installed for both
the critical and warnings states:

.. code:: sh

    powerconsul watch warning
    powerconsul watch critical

This will look for any health checks that change to a critical/warning
state for the local node, and will trigger events.

Triggers
~~~~~~~~

Triggers are called by watchers:

.. code:: sh

    powerconsul trigger critical
    powerconsul trigger warning

Triggers expect certain values to exist in the Consul KV store:

.. code:: text

    triggers/<environment>/<consulService>/<role>/<state>

    EXAMPLE VALUES:
    environment: production
    consulService: myServiceCheckName
    role: standalone/primary/secondary
    state: critical/warning

If a particular service goes into a critical/warning state, the trigger
will look to the KV store to determine what action it should run. The
following values are dynamic and will be substituted automatically in
either a shell command or script:

-  @ENV = The server environment, i.e.: production
-  @HOST = The hostname, i.e.: production-webserver1
-  @ROLE = The server role, i.e.: webserver

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
