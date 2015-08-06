import json
from webob import Request, Response
import webob.dec
import webob.exc

class Application(object):

	def _get_method(self, func_name):
		return getattr(self, func_name, None)

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
		if not('swagger' in req.environ):
			print "No swagger in environment"
			return webob.exc.HTTPNotFound()
		swagger = req.environ['swagger']
		# print swagger
		if not ('operation' in swagger):
			print "No operation"
			print swagger
			return webob.exc.HTTPNotFound()
		operation = swagger['operation']
		if not ('operationId' in operation):
			print "No operationId"
			return webob.exc.HTTPNotFound()
		method_name = operation['operationId']
		if method_name.startswith('_'):
			# Attempt to call a private method
			return webob.exc.HTTPForbidden()
		method = self._get_method(method_name)
		if method is None:
			# Method specified in interface specification, but no matching Python method found
			return webob.exc.HTTPNotImplemented()
		return method(swagger['parameters'])
