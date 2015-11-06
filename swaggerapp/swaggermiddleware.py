#!/usr/bin/python

import json
import logging

from swaggerapp.specification import SwaggerSpecification


class SwaggerMiddleware(object):

    """
    A WSGI URL router middleware that automatically configures itself
    using a set of Swagger JSON API specifications.
    """

    def __init__(self, application, specs, cfg=None, **kw):
        self.specs = specs
        self.application = application

    def _decorate_environment(self, environ):
        url = environ['SCRIPT_NAME'] + environ['PATH_INFO']
        if 'swagger' in environ:
            swagger = environ['swagger']
        else:
            swagger = environ['swagger'] = dict()
        if 'path' in swagger:
            pathdef = swagger['path']
        else:
            for spec in self.specs:
                [pathdef, path_parameters] = spec._find_path(url)
                if pathdef is not None:
                    swagger['spec'] = spec
                    swagger['path'] = pathdef
                    swagger['parameters'] = path_parameters
                    swagger['operation'] = spec._find_operation(
                        pathdef, environ['REQUEST_METHOD']
                    )
                    if swagger['operation'] is not None:
                        break
        if not('spec' in swagger):
            swagger['spec'] = None
        if not('path' in swagger):
            swagger['path'] = None
        if not('parameters' in swagger):
            swagger['parameters'] = None
        if not('operation' in swagger):
            swagger['operation'] = None

    def __call__(self, environ, start_response):
        logging.debug("PATH_INFO: " + environ['PATH_INFO'])
        logging.debug("SCRIPT_NAME: " + environ['SCRIPT_NAME'])
        logging.debug(self.specs)
        self._decorate_environment(environ)
        return self.application(environ, start_response)


def factory(config, **settings):
    def filter(app):
        config.update(settings)
        swagger_files = config.get('swagger_json')
        if not swagger_files:
            raise ValueError('No swagger_json specified')
        specs = [
            SwaggerSpecification(
                json.loads(open(filename).read())
            ) for filename in swagger_files.split()
        ]
        return SwaggerMiddleware(app, specs)
    return filter

if __name__ == '__main__':
    app = HelloApp()
    middleware = SwaggerMiddleware(app)
    print middleware
