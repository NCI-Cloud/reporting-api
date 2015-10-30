#!/usr/bin/python

import sys
import json

class JSONEvent(object):
    def __init__(self, event):
        self.event = event

JSONEvent.START_ARRAY  = 1
JSONEvent.END_ARRAY    = 2
JSONEvent.START_OBJECT = 3
JSONEvent.END_OBJECT   = 4

class JSONStreamingEncoder(object):

    def __init__(self):
        self.terminator = ''

    def __iter__(self):
        return self

    def start_array(self):
        self.terminator = ']' + self.terminator
        return '['

    def end_array(self):
        if self.terminator.startswith(']'):
            self.terminator = self.terminator[1:]
            return ']'
        else:
            raise ValueError('Attempting to end an array when not in an array')

    def start_object(self):
        self.terminator = '}' + self.terminator
        return '{'

    def end_object(self):
        if self.terminator.startswith('}'):
            self.terminator = self.terminator[1:]
            return '}'
        else:
            raise ValueError('Attempting to end an object when not in an object')

    def to_array(self, value):
        first = True
        for item in value:
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

    def to_object(self, value):
        first = True
        for key in value:
            if first:
                first = False
                yield self.start_object()
            else:
                yield ','
            for json_snippet in self.to_json(key):
                yield json_snippet
            yield ':'
            for json_snippet in self.to_json(value[key]):
                yield json_snippet
        if first:
            yield self.start_object()
        yield self.end_object()

    def to_json(self, value, array_not_object = None):
        if hasattr(value, 'isoformat'):
            yield '"' + value.isoformat() + '"'
            return
        if array_not_object == True or isinstance(value, list):
            for json_snippet in self.to_array(value):
                yield json_snippet
            return
        if array_not_object == False or isinstance(value, dict):
            for json_snippet in self.to_object(value):
                yield json_snippet
            return
        try:
            yield json.dumps(value)
            return
        except TypeError:
            pass
        try:
            it = iter(value)
        except TypeError:
            it = None
        if it is not None:
            if array_not_object == False or self.terminator.startswith('}'):
                for json_snippet in self.to_object(it):
                    yield json_snippet
                return
            else:
                for json_snippet in self.to_array(it):
                    yield json_snippet
                return
        yield json.dumps(value)
        return

    def old_next(self):
        try:
            value = self.input.next()
        except StopIteration:
            if self.terminator:
                term = self.terminator
                self.terminator = ''
                return term
            raise
        if isinstance(value, JSONEvent):
            if value.event == JSONEvent.START_ARRAY:
                return self.start_array()
            elif value.event == JSONEvent.START_OBJECT:
                return self.start_object()
            raise ValueError('Unrecognised JSONEvent')
        if self.terminator:
            ret_json = ''
        else:
            ret_json = self.start_array()
        for json_snippet in self.to_json(value):
            ret_json = ret_json + json_snippet
        return ret_json

def test_streaming_encoder(value):
    enc = JSONStreamingEncoder()
    for chunk in enc.to_json(value):
        sys.stdout.write(chunk)

def test_encode_array():
    arr = [ 'firstval', 'secondval' ]
    test_streaming_encoder(arr)

def test_encode_dict():
    dic = dict( firstkey = 'firstval', secondkey = 'secondval' )
    test_streaming_encoder(dic)

def test_encode_generator():
    def gen():
        yield 'firstval'
        yield 'secondval'
    test_streaming_encoder(gen())

if __name__ == '__main__':
    test_encode_array()
    test_encode_dict()
    test_encode_generator()
