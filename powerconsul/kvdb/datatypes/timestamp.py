import re
import six

class Timestamp_Data(object):
    """
    Class object for YYYY-MM-DD HH:MM:SS timestamp string.
    """
    def __init__(self, data):
        self.data   = data

        # Timestamp attributes
        self.year   = None
        self.month  = None
        self.day    = None
        self.hour   = None
        self.minute = None
        self.second = None

        # Parse init data
        self._parse()

    def __repr__(self):
        def _pad(val):
            if len(str(val)) == 1:
                return '0{0}'.format(val)
            return val
        return '{0}-{1}-{2} {3}:{4}:{5}'.format(
            self.year,
            _pad(self.month),
            _pad(self.day),
            _pad(self.hour),
            _pad(self.minute),
            _pad(self.second))

    def _parse(self):
        """
        Parse and validate the init timestamp data. Data can be either
        a string in the format: YYYY-MM-DD HH:MM:SS, or a tuple such as:
        (2017, 6, 21, 12, 1, 34).
        """
        _data = None

        # Timestamp from string
        if isinstance(self.data, six.string_types):
            regex = re.compile(r'^([0-9]{4})-([0-9]{1,2})-([0-9]{1,2})\s([0-9]{1,2}):([0-9]{1,2}):([0-9]{1,2})$')
            out   = re.search(regex, self.data)

            if not out:
                raise Exception('Failed to parse timestamp from string: {0}'.format(self.data))
            _data = out.groups()

        # Timestamp from tuple of ints
        if isinstance(self.data, tuple):
            if not len(self.data) == 6:
                raise Exception('Timestamp tuple must contain 6 elements, only found {0}'.format(len(self.data)))
            if not len([x for x in self.data if isinstance(x, int)]) == len(self.data):
                raise Exception('Timestamp must contain all integer values')
            _data = self.data

        # Map attribute data
        for i, val in enumerate(_data):
            setattr(self, ('year', 'month', 'day', 'hour', 'minute', 'second')[i], int(val))
