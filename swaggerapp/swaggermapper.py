#!/usr/bin/python

"""
URL router middleware.
"""

import json
import os
from routes.middleware import RoutesMiddleware
from routes import Mapper
from swaggerapp.specification import SwaggerSpecification


class SwaggerMapper(Mapper):
    """
    A WSGI URL router middleware that automatically configures itself
    using a set of Swagger JSON API specifications.
    """

    def __init__(self, swagger_specs):
        super(SwaggerMapper, self).__init__()
        """
        To debug this Mapper:
        logging.basicConfig()
        logger = logging.getLogger('routes.middleware')
        logger.setLevel(logging.DEBUG)
        """
        for spec in swagger_specs:
            self._read_spec(spec)

    def _read_spec(self, swagger_spec):
        """
        FIXME: This breaks matching for apps whose Paste configuration
        has them served from a URL other than the root '/'.
        if 'basePath' in swagger_spec:
            base_path = swagger_spec['basePath']
        else:
            base_path = ''
        """
        base_path = ''
        for path, pathdef in swagger_spec['paths'].items():
            """
            NOTE: Use of mapper.collection rather than mapper.connect below
            would make the controller implicit, rather than using
            Swagger schema operationId attributes.
            However, doing so would impose additional structure on the API,
            limiting the generality of Swagger and this class.
            """
            methods = [
                method for method in SwaggerSpecification.methods
                if method != 'options' and method in pathdef
            ]
            for method in methods:
                methoddef = pathdef[method]
                if 'operationId' in methoddef:
                    handler_name = methoddef['operationId']
                    for suffix in ['', '/']:
                        super(SwaggerMapper, self).connect(
                            handler_name,
                            base_path + path + suffix,
                            method=handler_name,
                            conditions=dict(method=method.upper())
                        )
                else:
                    raise ValueError(
                        "No operationId attribute for method '%s' in path '%s'"
                        % (method, path)
                    )
            """
            TODO: Synthesise an OPTIONS response
            for suffix in [ '', '/' ]:
                super(SwaggerMapper, self).connect(
                    'OPTIONS_' +
                    '_'.join(base_path, path, suffix).replace('/', '_'),
                    base_path + path + suffix,
                    method='options',
                    conditions=dict(method='OPTIONS')
                )
            """
        self.redirect('', '/')

    def routematch(self, url=None, environ=None):
        """Work around a crash in routes.mapper if url is empty"""
        if url is '':
            result = self._match('', environ)
            return result[0], result[1]
        return super(SwaggerMapper, self).routematch(url, environ)


def factory(config, **settings):
    """
    Function that returns a WSGI filter factory function.
    """
    def filter(app):
        """
        WSGI filter factory function.
        """
        config.update(settings)
        swagger_files = config.get('swagger_json')
        if not swagger_files:
            raise ValueError('No swagger_json specified')
        specs = [
            json.loads(open(filename).read())
            for filename in swagger_files.split()
        ]
        mapper = SwaggerMapper(specs)
        return RoutesMiddleware(app, mapper)
    return filter

if __name__ == '__main__':
    REALFILE = os.path.realpath(__file__)
    REALDIR = os.path.dirname(REALFILE)
    PARDIR = os.path.realpath(os.path.join(REALDIR, os.pardir))
    CONFDIR = os.path.join(PARDIR, 'conf')
    SPECFILES = ['swagger_versions.json', 'swagger_apiv1.json']
    SPECS = [
        json.loads(open(os.path.join(CONFDIR, specfile)).read())
        for specfile in SPECFILES
    ]
    MAPPER = SwaggerMapper(SPECS)
    print MAPPER
