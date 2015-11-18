#!/usr/bin/python

"""
Encode values suitable for output.
"""

import json
from datetime import datetime
from unittest import main as test_main, TestCase


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
                yield (str(key), entry)
        elif isinstance(value, list):
            for tup in enumerate(value):
                yield [str(tup[0])] + list(tup[1:])
        else:
            i = 0
            for entry in value:
                if isinstance(entry, list) and len(entry) == 2:
                    yield (str(entry[0]), entry[1])
                else:
                    yield (str(i), entry)
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
                yield entry[0]
                yield entry[1]
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


"""
Pairs of input data and expected output data for unit testing.
"""
TEST_INPUT_DATETIME = datetime(1999, 12, 31, 23, 59, 59, 999999)
TEST_OUTPUT_DATETIME = '"1999-12-31T23:59:59.999999"'
TEST_INPUT_SUBARRAY = [
    'element1',
    'element2'
]
TEST_OUTPUT_SUBARRAY = (
    '['
    '"element1",'
    '"element2"'
    ']'
)
TEST_INPUT_SUBDICT = dict(
    sub_key1='sub_entry1',
    sub_key2='sub_entry2'
)
TEST_OUTPUT_SUBDICT = (
    '{'
    '"sub_key2":"sub_entry2",'
    '"sub_key1":"sub_entry1"'
    '}'
)
TEST_INPUT_LIST = [
    'first_value', 'second_value', TEST_INPUT_DATETIME, TEST_INPUT_SUBDICT
]
TEST_OUTPUT_LIST_ARRAY = (
    '['
    '"first_value",'
    '"second_value",'
) + TEST_OUTPUT_DATETIME + ',' + TEST_OUTPUT_SUBDICT + (
    ']'
)
TEST_OUTPUT_LIST_OBJECT = (
    '{'
    '"0":"first_value",'
    '"1":"second_value",'
    '"2":'
) + TEST_OUTPUT_DATETIME + ',' + (
    '"3":'
) + TEST_OUTPUT_SUBDICT + (
    '}'
)
TEST_INPUT_DICT = dict(
    first_key='first_entry',
    second_key='second_entry',
    happy_new_year=TEST_INPUT_DATETIME,
    subarray=TEST_INPUT_SUBARRAY
)
TEST_OUTPUT_DICT_ARRAY = (
    '['
    '"subarray",'
) + TEST_OUTPUT_SUBARRAY + ',' + (
    '"second_key",'
    '"second_entry",'
    '"happy_new_year",'
) + TEST_OUTPUT_DATETIME + ',' + (
    '"first_key",'
    '"first_entry"'
    ']'
)
TEST_OUTPUT_DICT_OBJECT = (
    '{'
    '"subarray":'
) + TEST_OUTPUT_SUBARRAY + ',' + (
    '"second_key":"second_entry",'
    '"happy_new_year":'
) + TEST_OUTPUT_DATETIME + ',' + (
    '"first_key":"first_entry"'
    '}'
)


def gen():
    """
    An example generator function.
    """
    yield 'first_value'
    yield 'second_value'
    yield TEST_INPUT_DATETIME
    yield TEST_INPUT_SUBDICT
    # If these are of length two, they will be treated as name/value pairs
    # when being forcibly converted to a JSON object, which looks strange.
    yield TEST_INPUT_SUBARRAY
TEST_OUTPUT_GEN_ARRAY = (
    '['
    '"first_value",'
    '"second_value",'
) + TEST_OUTPUT_DATETIME + ',' \
    + TEST_OUTPUT_SUBDICT + ',' \
    + TEST_OUTPUT_SUBARRAY + (
    ']'
)


# Silence a warning about there being too many public methods.
# It is not a problem to have too many unit tests.
# pylint: disable=R0904
class JSONTestCase(TestCase):

    """
    Unit tests for the streaming JSON encoder.
    """

    def setUp(self):
        self.enc = JSONStreamingEncoder()

    # Silence warnings about the camelCase method names below.
    # PyUnit requires such camelCase names.
    # pylint: disable=C0103

    def testListToAuto(self):
        """
        Test converting a Python list into a JSON value.
        Python lists automatically become JSON arrays.
        """
        test_input = TEST_INPUT_LIST
        test_output_iter = self.enc.to_json(test_input)
        test_output = ''.join(test_output_iter)
        self.assertEqual(test_output, TEST_OUTPUT_LIST_ARRAY)

    def testListToArray(self):
        """
        Test converting a Python list into a JSON array.
        """
        test_input = TEST_INPUT_LIST
        test_output_iter = self.enc.to_json(test_input, True)
        test_output = ''.join(test_output_iter)
        self.assertEqual(test_output, TEST_OUTPUT_LIST_ARRAY)

    def testListToObject(self):
        """
        Test converting a Python list into a JSON object.
        """
        test_input = TEST_INPUT_LIST
        test_output_iter = self.enc.to_json(test_input, False)
        test_output = ''.join(test_output_iter)
        self.assertEqual(test_output, TEST_OUTPUT_LIST_OBJECT)

    def testDictToAuto(self):
        """
        Test converting a Python dictionary into a JSON value.
        Python dictionaries automatically become JSON objects.
        """
        test_input = TEST_INPUT_DICT
        test_output_iter = self.enc.to_json(test_input)
        test_output = ''.join(test_output_iter)
        self.assertEqual(test_output, TEST_OUTPUT_DICT_OBJECT)

    def testDictToArray(self):
        """
        Test converting a Python dictionary into a JSON array.
        """
        test_input = TEST_INPUT_DICT
        test_output_iter = self.enc.to_json(test_input, True)
        test_output = ''.join(test_output_iter)
        self.assertEqual(test_output, TEST_OUTPUT_DICT_ARRAY)

    def testDictToObject(self):
        """
        Test converting a Python dictionary into a JSON object.
        """
        test_input = TEST_INPUT_DICT
        test_output_iter = self.enc.to_json(test_input, False)
        test_output = ''.join(test_output_iter)
        self.assertEqual(test_output, TEST_OUTPUT_DICT_OBJECT)

    def testGenToAuto(self):
        """
        Test converting a Python generator into a JSON value.
        Python generators automatically become JSON arrays.
        """
        test_input = gen()
        test_output_iter = self.enc.to_json(test_input)
        test_output = ''.join(test_output_iter)
        self.assertEqual(test_output, TEST_OUTPUT_GEN_ARRAY)

    def testGenToArray(self):
        """
        Test converting a Python generator into a JSON array.
        """
        test_input = gen()
        test_output_iter = self.enc.to_json(test_input)
        test_output = ''.join(test_output_iter)
        self.assertEqual(test_output, TEST_OUTPUT_GEN_ARRAY)


if __name__ == '__main__':
    test_main()
