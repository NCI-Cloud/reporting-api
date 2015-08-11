import json
from webob import Request, Response
import abc
import webob.dec
import webob.exc
from common.specification import SwaggerSpecification

class Application(object):

	def _get_method(self, func_name):
		return getattr(self, func_name, None)

	@classmethod
	def _pyob_to_json(cls, pyval):
		def handler(value):
			if hasattr(value, 'isoformat'):
				return value.isoformat()
			elif hasattr(value, 'to_json'):
				return value.to_json()
			else:
				raise TypeError, 'Object of type %s with value of %s is not JSON serializable' % (type(value), repr(value))
		return json.dumps(pyval, default = handler)

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
	def _coerce_to_array(cls, value):
		if type(value) is list or type(value) is tuple:
			return value
		if type(value) is dict:
			return [ value.items() ]
		return [ value ]

	@classmethod
	def _coerce_to_dict(cls, value):
		if type(value) is list or type(value) is tuple:
			return dict((index, value[index]) for index in range(len(value)))
		if type(value) is dict:
			return value
		return dict(value = value)

	@classmethod
	def _expected_obj(cls, spec, operation, return_value):
		if operation is None:
			return return_value
		schema = cls._expected_schema(operation)
		typ = spec._resolve_refs(schema)
		if 'array' == typ:
			return cls._coerce_to_array(return_value)
		elif 'object' == typ:
			return cls._coerce_to_dict(return_value)
		raise ValueError("Cannot convert type '%s' into a valid JSON top-level type" % typ)

	@classmethod
	def _build_response(cls, req, return_value, headers = []):
		swagger = req.environ['swagger']
		if 'spec' not in swagger:
			raise ValueError('No spec in environment')
		spec = swagger['spec']
		if 'operation' in swagger:
			operation = swagger['operation']
		else:
			operation = None
		status = cls._expected_status(req, operation)
		return Response(
			status = status,
			content_type = 'application/json',
			body = cls._pyob_to_json(cls._expected_obj(spec, operation, return_value)),
			headers = headers
		)

	"""
	Respond to OPTIONS requests meaningfully,
	implementing HATEOAS using the information in the Swagger catalogs.
	"""
	@classmethod
	def _options_response(cls, req):
		swagger = req.environ['swagger']
		pathdef = swagger['path']
		if pathdef is None:
			result = None
			methods = []
		else:
			result = pathdef
			methods = [ method.upper() for method in SwaggerSpecification.methods if method != 'options' and method in pathdef ]
		# Synthesise an OPTIONS method
		methods.append('OPTIONS')
		headers = []
		headers.append(('Allow', ','.join(methods)))
		return cls._build_response(req, result, headers)

	@webob.dec.wsgify
	def __call__(self, req_dict):
		req = Request(req_dict.environ)
		if "options" == req.environ['REQUEST_METHOD'].lower():
			# Intercept this request to return an OPTIONS response
			return self._options_response(req)
		if 'wsgiorg.routing_args' in req.environ:
			routing_args = req.environ['wsgiorg.routing_args']
			method_params = routing_args[1]
			if method_params:
				method_name = method_params['method']
			else:
				return webob.exc.HTTPNotFound()
			swagger = None
		elif 'swagger' in req.environ:
			swagger = req.environ['swagger']
			# print swagger
			if 'operation' not in swagger:
				print "No operation"
				return webob.exc.HTTPNotFound()
			operation = swagger['operation']
			if operation is None:
				print "Null operation"
				return webob.exc.HTTPMethodNotAllowed()
			if 'operationId' not in operation:
				print "No operationId"
				return webob.exc.HTTPNotFound()
			method_name = operation['operationId']
			if 'parameters' in swagger:
				method_params = swagger['parameters']
			else:
				method_params = dict()
		else:
			print "Neither wsgiorg.routing_args nor swagger in environment"
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
		result = method(req, method_params)
		if isinstance(result, webob.exc.HTTPException):
			return result
		return self._build_response(req, result)
