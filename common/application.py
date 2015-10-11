from webob import Request, Response
import abc
import webob.dec
import webob.exc
from urlparse import parse_qs
from common.specification import SwaggerSpecification
from common.encoder import JSONStreamingEncoder

# TODO: Logging
class Application(object):

	def _get_method(self, func_name):
		return getattr(self, func_name, None)

	@classmethod
	def _expected_response(cls, operation):
		if 'responses' not in operation:
			raise ValueError('No responses')
		responses = operation['responses']
		if len(responses) != 1:
			raise ValueError('No or multiple responses')
		return responses

	@classmethod
	def _expected_status(cls, req, operation):
		if "options" == req.environ['REQUEST_METHOD'].lower():
			return '200 OK'
		resp = cls._expected_response(operation)
		return resp.keys()[0]

	@classmethod
	def _expected_body(cls, operation):
		return cls._expected_response(operation).values()[0]

	@classmethod
	def _expected_schema(cls, operation):
		body = cls._expected_body(operation)
		if 'schema' not in body:
			raise ValueError('No schema in response')
		return body['schema']

	@classmethod
	def _build_response(cls, req, return_value_iter, headers = None):
		"""
		Build an HTTP response to the given request, with response body
		containing the data output by the given iterator.
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
			expected_type = spec._resolve_refs(schema)
		else:
			schema = None
			expected_type = None
		status = cls._expected_status(req, operation)
		if not headers:
			headers = []
		headers.append(('Content-Type', 'application/json'))
		if return_value_iter is None:
			return_value_iter = iter()
		if expected_type is None:
			array_not_object = None
		elif 'array' == expected_type:
			array_not_object = True
		elif 'object' == expected_type:
			array_not_object = False
		else:
			raise ValueError("Cannot convert type '%s' into a valid JSON top-level type" % expected_type)
		encoder = JSONStreamingEncoder()
		json_iter = encoder.to_json(return_value_iter, array_not_object)
		return Response(
			status = status,
			app_iter = json_iter,
			headers = headers
		)

	"""
	Respond to OPTIONS requests meaningfully,
	implementing HATEOAS using the information in the Swagger catalogs.
	"""
	@classmethod
	def _options_response(cls, req):
		swagger = req.environ['swagger']
		spec = swagger['spec']
		path = swagger['path']
		if spec is None:
			result = None
			methods = []
		elif path is None:
			result = spec
			methods = [ method.upper() for method in SwaggerSpecification.methods if method != 'options' ]
		else:
			result = path
			methods = [ method.upper() for method in SwaggerSpecification.methods if method != 'options' and method in path ]
		# Synthesise an OPTIONS method
		methods.append('OPTIONS')
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
			# print swagger
			path = swagger['path']
			operation = swagger['operation']
			"""If no Swagger path matched, 404 Not Found"""
			if path is None:
				print "No path"
				# TODO: Include a link to the schema
				return webob.exc.HTTPNotFound()
			"""If Swagger path matched, but no operation matched the HTTP method, HTTP Method Not Allowed"""
			if operation is None:
				print "Null operation"
				print path
				# TODO: Include an Allow header listing acceptable request methods
				# TODO: Include a link to the schema
				return webob.exc.HTTPMethodNotAllowed()
			if 'operationId' not in operation:
				# TODO: Check this condition at API spec load time
				raise ValueError("No operationId in Swagger specification")
			method_name = operation['operationId']
			method_params = swagger['parameters']
		else:
			print "Neither wsgiorg.routing_args nor swagger in environment"
			# TODO: Include a link to the schema
			return webob.exc.HTTPNotFound()
			print req.environ
		if method_name.startswith('_'):
			# Attempt to call a private method
			return webob.exc.HTTPForbidden()
		method = self._get_method(method_name)
		if method is None:
			# Method specified in interface specification, but no matching Python method found
			print self.__class__.__name__ + " has no method '%s'" % method_name
			return webob.exc.HTTPNotImplemented()
		if ('QUERY_STRING' in req.environ) and req.environ['QUERY_STRING']:
			try:
				query_params = parse_qs(req.environ['QUERY_STRING'], True, True)
			except ValueError:
				return webob.exc.HTTPBadRequest()
		else:
			query_params = dict()
		query_params.update(method_params)
		result, headers = method(req, query_params)
		if isinstance(result, webob.exc.HTTPException):
			return result
		return self._build_response(req, result, headers)
