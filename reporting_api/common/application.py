"""
A WSGI application configured by an INI file,
which responds to requests according to a Swagger API specification.
"""

from webob import Request, Response
import abc
import webob.dec
import webob.exc
from urlparse import parse_qs
from swaggerapp.specification import SwaggerSpecification
from swaggerapp.encoder import JSONStreamingEncoder
import logging


# Pylint warns that the following class has too few public methods.
# It is not intended to have many (or even any) public methods,
# so this is not a problem, so the following comment silences the warning.
# Apparently, pylint assumes (falsely) that a class without public methods
# is being abused as a mere holder of data - but the below class is being
# used as a holder of code, as is common accepted practice in OOP.
# pylint: disable=R0903

class Application(object):

    """
    Abstract base class for a WSGI application configured by an INI file
    which responds to requests according to a Swagger API specification.
    """

    __metaclass__ = abc.ABCMeta

    def __init__(self, configuration):
        super(Application, self).__init__()
        self.config = configuration

    def _get_method(self, func_name):
        """
        Find and return the method with the given name on this object,
        or return None if no such method exists.
        """
        return getattr(self, func_name, None)

    @classmethod
    def _expected_response(cls, operation):
        """
        Given a Swagger operation, return the sole response.
        If the specification allows no responses, we cannot succeed,
        because HTTP requires a response to every request.
        If the specification allows multiple responses,
        we have no way to choose which will be returned,
        so we must also fail.
        """
        if 'responses' not in operation:
            raise ValueError('No responses')
        responses = operation['responses']
        if len(responses) != 1:
            raise ValueError('No or multiple responses')
        return responses

    @classmethod
    def _expected_status(cls, req, operation):
        """
        Given a Swagger operation, return the expected status.
        This is the HTTP status that will be served in response
        to a request mapping to this operation.
        """
        if "options" == req.environ['REQUEST_METHOD'].lower():
            return '200 OK'
        resp = cls._expected_response(operation)
        return resp.keys()[0]

    @classmethod
    def _expected_body(cls, operation):
        """
        Given a Swagger operation, return the expected body.
        This is the HTTP response body that will be served
        in response to a request mapping to this operation.
        """
        return cls._expected_response(operation).values()[0]

    @classmethod
    def _expected_schema(cls, operation):
        """
        Given a Swagger operation, return the schema of the expected body.
        This specifies the structure of the HTTP response body that will
        be served in response to a request mapping to this operation.
        """
        body = cls._expected_body(operation)
        if 'schema' not in body:
            raise ValueError('No schema in response')
        return body['schema']

    @classmethod
    def _headers(cls):
        """
        Return a list of ('Header-Name', 'Header-Value') tuples,
        which should be added as HTTP headers to every response.
        """
        return []

    @classmethod
    def _build_response(cls, req, return_value_iter, headers=None):
        """
        Build an HTTP response to the given request, with response body
        containing the data output by the given iterator.
        Tailor the response to the datatypes specified by Swagger, if any.
        """
        if isinstance(return_value_iter, webob.exc.WSGIHTTPException):
            return return_value_iter
        swagger = req.environ['swagger']
        spec = swagger['spec']
        if 'operation' in swagger:
            operation = swagger['operation']
        else:
            operation = None
        if operation:
            schema = cls._expected_schema(operation)
            expected_type = spec.resolve_refs(schema)
        else:
            schema = None
            expected_type = None
        status = cls._expected_status(req, operation)
        if not headers:
            headers = []
        """
        TODO: XML response support, depending on content negotiation.
        """
        headers.append(('Content-Type', 'application/json'))
        for tup in cls._headers():
            headers.append(tup)
        if return_value_iter is None:
            return_value_iter = iter()
        if expected_type is None:
            # Not sure what type to return
            array_not_object = None
        elif 'array' == expected_type:
            # The specification says we're to return an array
            array_not_object = True
        elif 'object' == expected_type:
            # The specification says we're to supply an object
            array_not_object = False
        else:
            # A JSON response must be either an object or an array
            raise ValueError(
                "Cannot convert type '%s' into a valid JSON top-level type"
                % expected_type
            )
        encoder = JSONStreamingEncoder()
        json_iter = encoder.to_json(return_value_iter, array_not_object)
        return Response(
            status=status,
            app_iter=json_iter,
            headers=headers
        )

    @classmethod
    def _allowed_methods(cls, spec, path):
        """
        Which HTTP methods are allowed by the specification?
        An OPTIONS method is permitted whether or not the specification
        says so, since we synthesise those.
        """
        if spec is None:
            methods = []
        elif path is None:
            methods = [
                method.upper() for method in SwaggerSpecification.methods
                if method != 'options'
            ]
        else:
            methods = [
                method.upper() for method in SwaggerSpecification.methods
                if method != 'options' and method in path
            ]
        # Synthesise an OPTIONS method
        methods.append('OPTIONS')
        return methods

    @classmethod
    def _options_response(cls, req):
        """
        Respond to OPTIONS requests meaningfully,
        implementing HATEOAS using the information in the Swagger catalogs.
        """
        swagger = req.environ['swagger']
        spec = swagger['spec']
        path = swagger['path']
        methods = cls._allowed_methods(spec, path)
        if spec is None:
            result = None
        elif path is None:
            result = spec
        else:
            result = path
        headers = []
        headers.append(('Allow', ','.join(methods)))
        return cls._build_response(req, result, headers)

    def _check_auth(self, req):
        """
        Hook for subclasses to override to implement authentication
        and/or authorisation. Allows everything by default.
        """
        return True

    @webob.dec.wsgify
    def __call__(self, req_dict):
        """
        Match the given request in the Swagger specification.
        Requires WSGI environment information from either SwaggerMapper
        or SwaggerMiddleware.

        Respond with one of several things:
        - For an OPTIONS request, respond with part/all of the spec
        - For an unauthorised request, an HTTP error
        - For a request that doesn't map to an operationId in the schema,
          or maps to something not defined in Python, or maps to a private
          method whose name begins with an underscore, an HTTP error
        - The result of calling self.operation_<operationId>, which is expected to
          return a ( body, headers ) tuple.
        """
        req = Request(req_dict.environ)
        if "options" == req.environ['REQUEST_METHOD'].lower():
            # Intercept this request to return an OPTIONS response
            return self._options_response(req)
        # Require valid authentication/authorisation from this point onward
        if not self._check_auth(req):
            # Authentication or authorisation failed
            return webob.exc.HTTPUnauthorized()
        if 'wsgiorg.routing_args' in req.environ:
            routing_args = req.environ['wsgiorg.routing_args']
            method_params = routing_args[1]
            if method_params:
                method_name = method_params['method']
            else:
                # TODO: Include a link to the schema
                return webob.exc.HTTPNotFound()
        elif 'swagger' in req.environ:
            swagger = req.environ['swagger']
            logging.debug(swagger)
            path = swagger['path']
            operation = swagger['operation']
            # If no Swagger path matched, 404 Not Found
            if path is None:
                logging.warning("No path matched requested URL")
                # TODO: Include a link to the schema
                return webob.exc.HTTPNotFound()
            # If Swagger path matched, but no operation matched the HTTP
            # method, HTTP Method Not Allowed
            if operation is None:
                logging.warning(
                    "No matching operation in path in API specification"
                )
                logging.debug(path)
                # Include an Allow header listing acceptable request methods
                headers = []
                methods = self._allowed_methods(swagger, path)
                headers.append(('Allow', ','.join(methods)))
                # TODO: Include a link to the schema
                return webob.exc.HTTPMethodNotAllowed(headers=headers)
            if 'operationId' not in operation:
                # This condition is also checked at API spec load time
                raise ValueError("No operationId in Swagger specification")
            method_name = 'operation_' + operation['operationId']
            method_params = swagger['parameters']
        else:
            logging.error(
                "Neither wsgiorg.routing_args nor swagger in environment"
            )
            logging.debug(req.environ)
            # TODO: Include a link to the schema
            return webob.exc.HTTPNotFound()
        if method_name.startswith('_'):
            # Attempt to call a private method
            return webob.exc.HTTPForbidden()
        method = self._get_method(method_name)
        if method is None:
            # Method specified in interface specification,
            # but no matching Python method found
            logging.warning(
                self.__class__.__name__ +
                " has no method '" +
                method_name + "'"
            )
            return webob.exc.HTTPNotImplemented()
        if ('QUERY_STRING' in req.environ) and req.environ['QUERY_STRING']:
            try:
                query_params = parse_qs(
                    req.environ['QUERY_STRING'], True, True
                )
            except ValueError:
                return webob.exc.HTTPBadRequest(
                    "Failed to parse URL query parameters"
                )
        else:
            query_params = dict()
        query_params.update(method_params)
        result, headers = method(req, query_params)
        if isinstance(result, webob.exc.HTTPException):
            return result
        return self._build_response(req, result, headers)
