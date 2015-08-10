import json
from webob import Request, Response
import abc
import webob.dec
import webob.exc

class Application(object):

	def _get_method(self, func_name):
		return getattr(self, func_name, None)

	@classmethod
	def _resultset_to_json(self, resultset):
		def handler(obj):
			if hasattr(obj, 'isoformat'):
				return obj.isoformat()
			elif hasattr(obj, 'to_json'):
				return obj.to_json()
			else:
				raise TypeError, 'Object of type %s with value of %s is not JSON serializable' % (type(obj), repr(obj))
		return json.dumps(resultset, default = handler)

	@webob.dec.wsgify
	def __call__(self, req_dict):
		req = Request(req_dict.environ)
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
			if not ('operation' in swagger):
				print "No operation"
				return webob.exc.HTTPNotFound()
			operation = swagger['operation']
			if operation is None:
				print "Null operation"
				return webob.exc.HTTPMethodNotAllowed()
			if not ('operationId' in operation):
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
		return method(method_params)
