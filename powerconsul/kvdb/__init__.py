from __future__ import print_function
import json
from time import sleep
from consul import Consul
from termcolor import colored
from powerconsul.kvdb.datatypes import Timestamp_Data

class PowerConsul_KVDB(object):
    """
    Class object for a KV database connection. Using this
    interface for accessing KV data assumes you want the same
    data in all datacenters.
    """
    def __init__(self, get_local=True, put_local=True, base_path=None):
        self.api = Consul()
        self.dcs = self.api.catalog.datacenters()

        # Should we default to get/put data from local dc?
        self.get_local = get_local
        self.put_local = put_local

        # A base path to prepend to keys
        self.base_path = base_path

    def _parse_bool(self, string):
        """
        Attempt to parse a boolean string.
        """

        # True values
        if string in ['1', 'true', 'True']:
            return True

        # False values
        if string in ['0', 'false', 'False']:
            return False

        raise Exception('Could not parse boolean value from: {0}'.format(string))

    def _dump_data_value(self, data):
        """
        Dump data value to string before put operations.
        """

        # JSON?
        if isinstance(data, (dict, list)):
            return json.dumps(data)

        # All other
        return data

    def _load_data_value(self, data):
        """
        Process any returned data from a KV get operation.
        """

        # Boolean?
        try:
            return self._parse_bool(data)
        except: pass

        # Timestamp?
        try:
            return Timestamp_Data(string)
        except: pass

        # Float?
        try:
            return float(data)
        except: pass

        # Integer?
        try:
            return int(data)
        except: pass

        # JSON data?
        try:
            return json.loads(data)
        except: pass

        # Default to string
        return data

    def _map_key(self, key):
        """
        Format a KV path with any additional paths.
        """
        if self.base_path:
            return '{0}/{1}'.format(self.base_path, key)
        return key

    def _get_modify_index(self, key, dc=None):
        """
        Get the current modify index of the key.
        """
        if not dc:
            index, data = self.api.kv.get(key)
        else:
            index, data = self.api.kv.get(key, dc=dc)

        # No data found, create new entry
        if not data:
            return None
        return index

    def wait(self, key, value=None, sleep_time=1, message=None):
        """
        Wait for a KV to change or to become a specified value.
        """
        _key = self._map_key(key)
        if message:
            print(message, end='')

        init_value = self.get(_key, map=False)
        while True:
            if not value:
                if self.get(_key, map=False) != init_value:
                    break
            else:
                if self.get(_key, map=False) == value:
                    break
            sleep(sleep_time)
        if message:
            print(colored('SUCCESS', 'green'))

    def put(self, key, value):
        """
        Put KV data to the cluster. Use the Check-and-Set (cas) parameter to make this an
        atomic operation.

        :param    key: The KV key path
        :param  value: The new KV value
        """
        _data = self._dump_data_value(value)
        _key  = self._map_key(key)

        # Use local datacenter
        if self.put_local:

            # Get the last modify index
            mindex = self._get_modify_index(_key)

            # Perform a check and set operation
            if not mindex:
                return self.api.kv.put(_key, _data)
            else:
                return self.api.kv.put(_key, _data, cas=mindex)

        # Put to all datacenters
        for dc in self.dcs:

            # Get the last modify index
            mindex = self._get_modify_index(_key, dc=dc)

            # Perform a check and set operation
            if not mindex:
                self.api.kv.put(_key, _data, dc=dc)
            else:
                self.api.kv.put(_key, _data, dc=dc, cas=mindex)

    def get(self, key, map=True):
        """
        Retrieve and compare values from datacenters.
        """
        retval = []
        _key   = key if not map else self._map_key(key)

        # Use local datacenter
        if self.get_local:
            index, data = self.api.kv.get(_key)
            return self._load_data_value(data['Value'])

        # Get all datacenters
        for dc in self.dcs:
            index, data = self.api.kv.get(_key, dc=dc)
            retval.append(data['Value'])

        # Compare values
        if not all(retval):
            raise Exception('KV data mismatch: key={0}, dcs={1}'.format(key, ','.join(self.dcs)))
        return self._load_data_value(retval[0])
