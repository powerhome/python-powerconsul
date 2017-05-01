Power Consul Service Management
===============================

- `Clustering Services`_ with custom init scripts

The ``python-powerconsul`` package is a command-line utility designed to
work with a server's Consul agent:

-  Service/resource checks
-  Watching service health/state changes
-  Triggering actions based on service state changes

Consul and Puppet
~~~~~~~~~~~~~~~~~
For organizations that use Puppet https://github.com/solarkennedy/puppet-consul is an excellent solution for deploying both Consul masters and agents.

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

Active/Standby Nodes
''''''''''''''''''''

Service clustering works by defining a hash of active/standby nodes in the KV
path <clusterKey>/<consulService>.

.. code:: json

    {
        "active_nodes": ["node1","node2"],
        "standby_nodes": ["node3","node4"]
    }

Nodes in the active node(s) list will be classified in the ``primary``
role. Nodes in the secondary node(s) list will be classified in the
``secondary`` role.

Standalone
''''''''''

Any checks/triggers that do not find any data in the expected KV path
will assume they are in the ``standalone`` role and will always attempt
to be running/healthy.

Checks
~~~~~~

The following are examples on how to set up different types of checks:

Service Group
'''''''''''''

Service group checks are logical groupings of services under a single
service definition, using Power Consul clustered enabled init scripts.
For more information see `Clustering Services`_

.. code:: sh

    # <listOfServices> is a list of local service names, i.e.: apache2,mysql
    # <consulService> is the check name defined by the Consul agent, i.e.: apacheMySQLServices
    powerconsul check servicegroup -s <listOfServices> -S <consulService>

For more automated failover scenarios:

.. code:: sh

  # -U: This flag indicates that if the primary ever fails, and the secondary comes online,
  # update cluster roles to convert the secondary to the primary and require manual failback.
  #
  # -F /var/lock/somefile.lock: By providing this flag and the path to a lock file, this
  # allows manual failover commands from a single node which will rebalance and reassign roles
  # for the whole cluster.
  powerconsul check servicegroup -s <listOfServices> -S <consulService> -U -F /var/lock/apacheMysql.lock

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

Prepared Queries / DNS Tagging
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

This package has some built in functionality to manage prepared query tags for services in an active/standby configuration. As passing is inverted for standby servers (not running/healthy = passing), the ``only_passing`` tag for prepared queries is not sufficient. To work around this issue, Power Consul will update (as long as you enable tag overrides) passing/standby service tags with the string ``nodns`` which will allow you to have better control over a cluster of services. You can use additional tags (such as the environment, i.e. ``production``) to do further service filtering.

See (https://www.consul.io/docs/agent/http/query.html) for more information on prepared queries.

Example Service Definition
''''''''''''''''''''''''''
The following is an example service definition deployed via Puppet which will enable tag overrides:

.. code:: yaml

    consul::services:
      exampleApache2Service:
        enable_tag_override: true
        address: "somehostname.domain.com"
        checks:
          - script: "/usr/bin/env powerconsul check service -s apache2 -S exampleApache2Service"
            interval: 10s
        tags:
          - "apache"
          - "web"
          - "production"

Example Prepared Query
''''''''''''''''''''''
The following is an example prepared query which leverages tag overrides and the ``nodns`` tag. This will only return services in a passing state, and services without the ``nodns`` tag, which would be a standby service that is stopped, but shown as being in a passing state (as we expect). This example is also deployed via Puppet:

.. code:: yaml

    profiles::consul::prepared_queries:
      'production-web':
        'ensure': 'present'
        'service_name': 'exampleApache2Service'
        'service_failover_n': 1
        'service_only_passing': true
        'service_failover_dcs':
          - 'dc1'
          - 'dc2'
        'service_tags':
          - 'production'
          - '!nodns'
        'ttl': 10

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

.. _Clustering Services: CLUSTERED_SERVICES.rst
