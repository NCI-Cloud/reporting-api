#!/usr/bin/python

"""
Map URLs to Swagger operations and therefore to Python methods.
"""

import json
import logging

from swaggerapp.specification import SwaggerSpecification


# Pylint warns that the following class has too few public methods,
# even though __call__ is effectively a public method.
# The following comment disabled the seemingly-incorrect warning.
# pylint: disable=R0903

class SwaggerMiddleware(object):

    """
    A WSGI URL router middleware that automatically configures itself
    using a set of Swagger JSON API specifications.
    """

    def __init__(self, application, specs, cfg=None, **kw):
        self.specs = specs
        self.application = application

    def _decorate_environment(self, environ):
        """
        Given the request environment, using the loaded specification,
        decorate the request environment with additional information
        about the request found by examining the specification.

        If the request matches an operation defined in the specification,
        this information includes that operation and its parameters.
        """
        url = environ['SCRIPT_NAME'] + environ['PATH_INFO']
        if 'swagger' in environ:
            swagger = environ['swagger']
        else:
            swagger = environ['swagger'] = dict()
        if 'path' in swagger:
            pathdef = swagger['path']
        else:
            for spec in self.specs:
                [pathdef, path_parameters] = spec.find_path(url)
                if pathdef is not None:
                    swagger['spec'] = spec
                    swagger['path'] = pathdef
                    swagger['parameters'] = path_parameters
                    swagger['operation'] = spec.find_operation(
                        pathdef, environ['REQUEST_METHOD']
                    )
                    if swagger['operation'] is not None:
                        break
        if 'spec' not in swagger:
            swagger['spec'] = None
        if 'path' not in swagger:
            swagger['path'] = None
        if 'parameters' not in swagger:
            swagger['parameters'] = None
        if 'operation' not in swagger:
            swagger['operation'] = None

    def __call__(self, environ, start_response):
        logging.debug("PATH_INFO: " + environ['PATH_INFO'])
        logging.debug("SCRIPT_NAME: " + environ['SCRIPT_NAME'])
        logging.debug(self.specs)
        self._decorate_environment(environ)
        return self.application(environ, start_response)


def factory(config, **settings):
    """
    Function that returns a function that returns
    WSGI filters.
    """
    def filter(app):
        """
        Factory method that produces WSGI filters.
        """
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
    from reporting.api.versions import VersionsApp
    APP = VersionsApp()
    SPEC = SwaggerSpecification(
        json.loads(
            open('reporting/conf/swagger_versions.json').read()
        )
    )
    MIDDLEWARE = SwaggerMiddleware(APP, (SPEC))
    print MIDDLEWARE
