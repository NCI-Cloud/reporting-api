#!/usr/bin/python

"""
Encode values suitable for output.
"""

import sys
import json
from pprint import pprint
from datetime import datetime


class JSONStreamingEncoder(object):

    """
    This class wraps the Python 'json' module in code capable of handling
    potentially-large Python objects without holding the entire JSON output
    in memory.
    It also permits explicit choice of the type of top-level JSON value -
    either a JSON array or a JSON object is permitted by RFC 4627.
    RFC 7159 relaxed this to permit other top-level JSON types, but
    for compatibility with other JSON-processing software, those relaxations
    are not permitted by this encoder.
    """

    def __init__(self, value=None):
        """
        Construct a encoder instance, optionally passing in a Python value
        to be encoded.
        """
        self.terminator = ''
        self.value = value

    def __iter__(self):
        """
        Iterate over chunks of the JSON encoding of the Python value passed in
        at construction time (if any).
        """
        return self.to_json(self.value)

    def start_array(self):
        """
        Return the string that begins a JSON array.
        """
        self.terminator = ']' + self.terminator
        return '['

    def end_array(self):
        """
        Return the string that terminates a JSON array.
        """
        if self.terminator.startswith(']'):
            self.terminator = self.terminator[1:]
            return ']'
        else:
            raise ValueError(
                'Attempting to end an array when not in an array'
            )

    def start_object(self):
        """
        Return the string that begins a JSON object.
        """
        self.terminator = '}' + self.terminator
        return '{'

    def end_object(self):
        """
        Return the string that terminates a JSON object.
        """
        if self.terminator.startswith('}'):
            self.terminator = self.terminator[1:]
            return '}'
        else:
            raise ValueError(
                'Attempting to end an object when not in an object'
            )

    @staticmethod
    def _make_object_generator(value):
        """
        Given a Python value, return an iterator over tuples,
        so that each tuple can become a name: value entry
        in the containing JSON object.
        """
        if isinstance(value, dict):
            for key, entry in value.iteritems():
                yield (key, entry)
        elif isinstance(value, list):
            for tup in enumerate(value):
                yield tup
        else:
            i = 0
            for entry in value:
                if isinstance(entry, list) and len(entry) == 2:
                    yield entry
                else:
                    yield (i, entry)
                i += 1

    @staticmethod
    def _make_array_generator(value):
        """
        Given a Python value, return an iterator over elements,
        so that each element can become an entry
        in the containing JSON array.
        """
        if isinstance(value, dict):
            for entry in value.iteritems():
                yield entry
        else:
            for entry in value:
                yield entry

    def _to_array(self, value):
        """
        Generator function which converts the given Python value
        to a JSON array, converting it as necessary.
        """
        first = True
        for item in self._make_array_generator(value):
            if first:
                first = False
                yield self.start_array()
            else:
                yield ','
            for json_snippet in self.to_json(item):
                yield json_snippet
        if first:
            yield self.start_array()
        yield self.end_array()

    def _to_object(self, value):
        """
        Generator function which converts the given Python value
        to a JSON object, converting it as necessary.
        """
        first = True
        for key, entry in self._make_object_generator(value):
            if first:
                first = False
                yield self.start_object()
            else:
                yield ','
            for json_snippet in self.to_json(key):
                yield json_snippet
            yield ':'
            for json_snippet in self.to_json(entry):
                yield json_snippet
        if first:
            yield self.start_object()
        yield self.end_object()

    def to_json(self, value, array_not_object=None):
        """
        A generator which successively yields chunks of JSON-format data
        encoding the given value.
        If array_not_object is True, generate a JSON array.
        If array_not_object is False, generate a JSON object.
        Otherwise, output whichever JSON type is most similar to the type of
        the given value.
        """
        if array_not_object is None:
            if isinstance(value, list):
                array_not_object = True
            elif isinstance(value, dict):
                array_not_object = False
        if array_not_object is True:
            for json_snippet in self._to_array(value):
                yield json_snippet
        elif array_not_object is False:
            for json_snippet in self._to_object(value):
                yield json_snippet
        else:
            try:
                # FIXME: We must not output a string at top level
                yield '"' + value.isoformat() + '"'
                return
            except AttributeError:
                pass
            try:
                yield json.dumps(value)
                return
            except TypeError:
                pass
            for chunk in self._to_array(value):
                yield chunk


def test_streaming_encoder(value, array_not_object=None):
    """
    Pretty-print the given value and its JSON encoding.
    """
    enc = JSONStreamingEncoder()
    print '--------'
    print "Input:"
    pprint(value)
    if array_not_object is None:
        print "Either output type"
    elif array_not_object is True:
        print "Force array"
    elif array_not_object is False:
        print "Force object"
    sys.stdout.write('Output: ')
    for chunk in enc.to_json(value, array_not_object):
        sys.stdout.write(chunk)
    sys.stdout.write("\n")


TEST_DATETIME = datetime(1999, 12, 31, 23, 59, 59, 999999)


def gen():
    """
    An example generator function.
    """
    yield 'first_value'
    yield 'second_value'
    yield TEST_DATETIME
    yield dict(subkey='sub_entry')
    # If these are of length two, they will be treated as name/value pairs
    # when being forcibly converted to a JSON object, which looks strange.
    yield ['element1', 'element2', 'element3']
    yield ('element1', 'element2', 'element3')

TEST_DATA = (
    ['first_value', 'second_value', TEST_DATETIME, dict(subkey='sub_entry')],
    ('first_value', 'second_value', TEST_DATETIME, dict(subkey='sub_entry')),
    dict(
         firstkey='first_entry',
         secondkey='second_entry',
         happy_new_year=TEST_DATETIME,
         subarray=['element1', 'element2']
    ),
)


def test_encode(value):
    """
    Test JSON-encoding the given Python value,
    with and without forcing it to be a certain JSON type.
    """
    test_streaming_encoder(value)
    test_streaming_encoder(value, True)
    test_streaming_encoder(value, False)

if __name__ == '__main__':
    for data in TEST_DATA:
        test_encode(data)
    test_streaming_encoder(gen())
    test_streaming_encoder(gen(), True)
    test_streaming_encoder(gen(), False)
