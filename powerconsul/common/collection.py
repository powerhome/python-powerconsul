import re
import json
from collections import namedtuple
from types import InstanceType, ClassType

def merge_dict(a, b, path=None):
        """
        Merge two dictionaries together. Do not overwrite duplicate keys.

        :param a: The first dictionary
        :type a: dict
        :param b: The second dictionary
        :type b: dict
        :param path: Not really sure what this does, using re-purposed code here
        :type path: list
        """
        if path is None: path = []
        for key in b:
            if key in a:
                if isinstance(a[key], dict) and isinstance(b[key], dict):
                    merge_dict(a[key], b[key], path + [str(key)])
                elif a[key] == b[key]:
                    pass
                else:
                    raise Exception('Conflict at {0}'.format('.'.join(path + [str(key)])))
            else:
                a[key] = b[key]
        return a

class PowerConsul_Collection(object):
    """
    Construct an immutable collection from a dictionary.
    """
    def __init__(self, init_data=None):
        """
        Initialize a new collection object.

        :param init_data: An optional dictionary used to initialize the collection
        :type init_data: dict
        """
        self.class_name = self.__class__.__name__
        if init_data:
            if isinstance(init_data, dict):

                # Check if creating a collection from a Django QueryDict
                if re.match(r'^<QueryDict.*$', str(init_data)):
                    self.collection = self._convert_query_dict(init_data)
                else:
                    self.collection = init_data
            else:
                self.collection = {}
        else:
            self.collection = {}

    def _convert_query_dict(self, query_dict):
        """
        Helper method used to convert a Django QueryDict to a standard
        Python dictionary.

        :param query_dict: The Django QueryDict object to convert
        :type query_dict: QueryDict
        """
        raw_converted = dict(query_dict.iterlists())
        converted = {}
        for key, value in raw_converted.iteritems():
            converted[key] = value[0]
        return converted

    def map(self, map_dict={}):
        """
        Map a dictionary to an existing collection object.

        :param map_dict: The dictionary object to map
        :type map_dict: dict
        """
        if not map_dict:
            return None
        else:

            # Check if mapping a Django QueryDict
            if re.match(r'^<QueryDict.*$', str(map_dict)):
                self.collection = merge_dict(self._convert_query_dict(map_dict), self.collection)
            else:
                self.collection = merge_dict(map_dict, self.collection)

    def isclass(self, obj, cls):
        """
        Helper method to test if an object is either a new or old style class.

        :param obj: The object to test
        :type obj: *
        :rtype: boolean
        """

        # Test for an old style class
        if (type(obj) is InstanceType):
            return True

        # Test for a class object
        if (re.match(r'^<powerconsul\..[^>]*>$', str(obj))):
            return True

        # Test for a new style class
        if ((hasattr(obj, '__class__')) and (re.match(r'^<class \'powerconsul\..*\.{0}\'>$'.format(cls), repr(obj.__class__)))):
            return True
        return False

    def get(self):
        """
        Retrieve the constructed collection objects. Converts the internal
        dictionary collection to a named tuple.

        :rtype: namedtuple
        """
        def obj_mapper(d):
            """
            Map a dictionary to a named tuple object based on dictionary keys

            :param d: The dictionary to map
            :type d: dict
            :rtype: namedtuple
            """
            return namedtuple(self.class_name, d.keys())(*d.values())

        # Check if creating a collection of classes
        class_collection = False
        for key, obj in self.collection.iteritems():
            if self.isclass(self.collection[key], key):
                class_collection = True
                break

        # Map the data to an object and return
        if class_collection:
            return namedtuple(self.class_name, self.collection.keys())(*self.collection.values())
        else:
            data = json.dumps(self.collection)
            return json.loads(data, object_hook=obj_mapper)

    @classmethod
    def create(cls, data):
        """
        Create a new collection.

        :param data: The source dictionary
        :type  data: dict
        :rtype: namedtuple
        """
        return cls(data).get()
