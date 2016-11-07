# Power Consul Service Management

Python commands for watching services and triggering events for HA and self-healing infrastructure.

### Installation/Upgrade
This Python package is under development and can be installed/updated using Python/PIP with setuptools:

##### Install
You must have Python PIP available to get setuptools as well as the Git command line utility:
```
pip install setuptools
git clone https://github.com/powerhome/python-powerconsul
cd python-powerconsul
python setup.py install
```
##### Upgrade
Pull from upstream and reinstall to update code in-place:
```
git pull
python setup.py install
```

### Checks
The following are examples on how to set up different types of checks:
##### Service
Service checks can be used to ensure standalone, active/active, or active/standby groups of services.
```sh
# Always active (standalone)
powerconsul check service -s apache2
# Always active (part of cluster)
powerconsul check service -s apache2 -c
# Active node in active/standby cluster (by node names)
powerconsul check service -s apache2 -c -n demo18-nitro-webserver2 -N demo18-nitro-webserver1 -S nitroApacheService
# Active node in active/standby cluster (by datacenter)
powerconsul check service -s apache2 -c -d ch -D cv -S nitroApacheService
```
