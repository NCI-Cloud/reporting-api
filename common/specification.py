#!/usr/bin/python

import json

class SwaggerSpecification(object):

    # The Swagger specification v2.0 mandates use of only these methods
    methods = [ 'get', 'put', 'post', 'delete', 'options', 'head', 'patch' ]

    def __init__(self, spec):
        self.spec = spec

    def _resolve_ref(self, ref):
        spec = self.spec
        if not ref.startswith('#/'):
            raise ValueError("Cannot handle catalog ref '%s'" % ref)
        ref = ref[2:]
        components = ref.split('/')
        for comp in components:
            if comp not in spec:
                raise ValueError("No definition component '%s' in spec '%s'" % (comp, spec))
            spec = spec[comp]
        return spec

    def _resolve_refs(self, schema):
        while '$ref' in schema:
            schema = self._resolve_ref(schema['$ref'])
        if 'type' in schema:
            return schema['type']
        raise ValueError('No type in schema')

    @classmethod
    def _path_matches(cls, pattern, url):
        # print "Testing URL '%s' against pattern '%s'" % (url, pattern)
        path_parameters = dict()
        pattern_components = pattern.split('/')
        url_components = url.split('/')
        patt_len = len(pattern_components)
        url_len = len(url_components)
        for i in range(0, min(patt_len, url_len)):
            patt_comp = pattern_components[i]
            url_comp = url_components[i]
            if patt_comp.startswith('{') and patt_comp.endswith('}') and url_comp:
                # Pattern component matched
                path_parameters[patt_comp[1:-1]] = url_comp
            elif patt_comp != url_comp:
                return [ False, [] ] # Literal component mismatch
        i += 1
        for comp in pattern_components[i:patt_len]:
            if comp:
                return [ False, [] ] # Trailing unmatched non-empty path pattern component
        for comp in url_components[i:url_len]:
            if comp:
                return [ False, [] ] # Trailing unmatched non-empty URL component
        # print "Match: '%s' '%s'" % (url, pattern)
        return [ True, path_parameters ]

    def _base_path(self):
        if 'basePath' in self.spec:
            return self.spec['basePath']
        return ''

    def _paths(self):
        return self.spec['paths'].items()

    def _find_path(self, url):
        base_path = self._base_path()
        for path, pathdef in self._paths():
            # print "BasePath: '%s'" % base_path
            [ matched, parameters ] = self._path_matches(base_path + path, url)
            if matched:
                return [ pathdef, parameters ]
            """
            else:
                print "Rejected URL '%s'" % url
            """
        return [ None, None ]

    @classmethod
    def _find_operation(cls, pathdef, request_method):
        request_method = request_method.lower()
        if request_method in pathdef:
            return pathdef[request_method]
        return None

if __name__ == '__main__':
    swagger_files = 'conf/swagger_apiv1.json'
    specs = [
        SwaggerSpecification(
            json.loads(open(filename).read())
        ) for filename in swagger_files.split()
    ]
    print specs
