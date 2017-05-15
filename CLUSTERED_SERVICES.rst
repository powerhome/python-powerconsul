Power Consul Service Clustering
===============================

The ``python-powerconsul`` package includes libraries which allow you to
create a cluster aware service init script. This allows service commands,
such as stop/start/restart/status to be aware of the state of the whole
cluster, not just the local machine.

Service Scripts
~~~~~~~~~~~~~~~~~
In order to leverage the functionality provided by service libraries, you
must be using a custom init script, which can either be deploy manually or
with a configuration tool such as Puppet.

.. code:: python

    #!/usr/bin/env python
    from powerconsul.service import PowerConsul_Service

    # This would be installed to: /etc/init.d/myservice

    ### BEGIN INIT INFO
    # Provides:          myservice
    # Required-Start:    $remote_fs $syslog
    # Required-Stop:     $remote_fs $syslog
    # Default-Start:     2 3 4 5
    # Default-Stop:      0 1 6
    # Short-Description: My clustered service.
    # Description:       My clustered service (apache2 and mysql).
    ### END INIT INFO

    if __name__ == '__main__':
      """
      Process the service wrapper command.
      """
      PowerConsul_Service.process(
          name           = 'myservice',
          consul_service = 'myserviceConsulName',
          local_services = ['apache2', 'mysql'],
          noop_lockfile  = '/var/lock/myservice.lock'
      )

These are the parameters passed to ``PowerConsul_Service.process``. **Bold** arguments are required, *italic* options are optional:

  - **name**: The local service wrapper name
  - **consul_service**: The name of the registered Consul service
  - *local_services*: A list of service(s) managed by this wrapper. Even if this is a single service, it must still be a list.
  - *noop_lockfile*: An optional lockfile that if it exists, forces all checks to pass. This is used when restarting or switching the primary node(s) to prevent service flapping.

Service Cluster Data
~~~~~~~~~~~~~~~~~~~~
In order for clustered service scritps to work, you must have cluster KV data
in each datacenter, i.e. ``<clusterKey>/<consulService>``.

KV Path: cluster/production/myserviceConsulName

.. code:: json

    {
      "active_nodes": ["node1"],
      "standby_nodes": ["node2"]
    }

This data is pulled automatically via service checks and service scripts to
begin determining the state of the cluster.

Node Promotion/Demotion Flags
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
The service manager uses two unique KV paths for every node/service combination. These values should be initialized with a string value of ``NULL``, and will be updated automatically when using the ``start-primary`` command to switch primary servers. Each node has a KV watch configuration to look for changes in these values and trigger actions when promoting or demoting in the cluster. For example:

KV Paths
''''''''

.. code:: text

    Demotion:  service/myConsulService/node1/demote
    Promotion: service/myConsulService/node1/promote

KV Values
'''''''''

.. code:: text

    NULL  - No promotion/demotion action triggers need to be taken
    START - Node is beginning the promotion/demotion process
    WAIT  - Node has completed the promotion/demotion process and is waiting for all
            other nodes to complete. This value will automatically be reset to NULL
            once this is finished.

KV Demotion/Promotion Watchers
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
The following are example Consul configurations for the KV watchers:

Demotion Watcher
''''''''''''''''
**config**: /etc/consul/watch_myServiceDemote.json

.. code:: json

    {
      "watches": [{
        "handler": "/usr/bin/env service nitrophone demote",
        "key": "service/nitroPhoneServicesInbound/production-talkbox-inbound/demote",
        "type": "key"
      }]
    }

Promotion Watcher
'''''''''''''''''
**config**: /etc/consul/watch_myServicePromote.json

.. code:: json

    {
      "watches": [{
        "handler": "/usr/bin/env service nitrophone promote",
        "key": "service/nitroPhoneServicesInbound/production-talkbox-inbound/promote",
        "type": "key"
      }]
    }

Service Commands
~~~~~~~~~~~~~~~~
The following commands are supported via the custom init script libraries:

.. code:: sh

    service myservice start
    service myservice stop
    service myservice status
    service myservice restart
    service myservice start-primary

Service: start
''''''''''''''

Attempt to start all local services. This command is run internally
by called the ``do_start`` method with any required parameters.

Service: stop
'''''''''''''

Attempt to stop all local services. This command is run internally
by called the ``do_stop`` method with any required parameters.

Service: status
'''''''''''''''

This command can be run from CLI to generate a status message show the status
of cluster nodes, and local services.

The following shows the status on node1 (the primary node):

.. code:: text

    user@node1:~# service myservice status

    myservice.service:
      cluster:
        nodes.active: node1.passing
        nodes.standby: node2.passing
      local:
        service.apache2: running... [  <stdout from: service apache2 status> ]
        service.mysql: running... [ <stdout from: service mysql status> ]

    user@node1:~#

The following shows the status on node2 (the standby node):

.. code:: text

    user@node2:~# service myservice status

    myservice.service:
      cluster:
        nodes.active: node1.passing
        nodes.standby: node2.passing
      local:
        service.apache2: stopped... [  <stdout from: service apache2 status> ]
        service.mysql: stopped... [ <stdout from: service mysql status> ]

    user@node2:~#

Service: restart
''''''''''''''''

This command can only be run on a primary/active server, and will generate lock files
during the restart to prevent service flapping if a secondary detects the primary
services are stopped during the restart period.

Service: start-primary
''''''''''''''''''''''

This can only be run on a secondary/standby node to convert all standby nodes to
the new primary. This can be in preparation for a datacenter failover, or after a
datacenter failover to restore back to the primary datacenter.

.. code:: text

    user@node2:~# service myservice status

    myservice.service:
      cluster:
        nodes.active: node1.passing
        nodes.standby: node2.passing
      local:
        service.apache2: stopped... [  <stdout from: service apache2 status> ]
        service.mysql: stopped... [ <stdout from: service mysql status> ]

    user@node2:~# service myservice start-primary
    Starting promotion for node node2...SUCCESS
    Starting demotion for node node1...SUCCESS
    Demoting primary node node1...SUCCESS
    Promoting secondary node node2...SUCCESS
    Switching cluster primary/secondary node roles...SUCCESS
    Clearing demotion trigger for node node1...SUCCESS
    Clearing promotion trigger for node node2...SUCCESS
    root@demo19-talkbox2:~# service myservice status

    myservice.service:
      cluster:
        nodes.active: node2.passing
        nodes.standby: node1.passing
      local:
        service.apache2: running... [  <stdout from: service apache2 status> ]
        service.mysql: running... [ <stdout from: service mysql status> ]

    user@node2:~#
