#!/usr/bin/python

import json
from pprint import pprint
from routes.middleware import RoutesMiddleware
from routes import Mapper

class SwaggerMapper(Mapper):
	"""
	A WSGI URL router middleware that automatically configures itself
	Using a Swagger specification.
	"""

	# The Swagger specification v2.0 mandates use of only these methods
	swagger_methods = [ 'get', 'put', 'post', 'delete', 'options', 'head', 'patch' ]

	def __init__(self, swagger_spec):
		super(SwaggerMapper, self).__init__();
		if 'basePath' in swagger_spec:
			base_path = swagger_spec['basePath']
		else:
			base_path = ''
		for path, pathdef in swagger_spec['paths'].items():
			"""
			NOTE: Use of mapper.collection rather than mapper.connect below
			would make the controller implicit, rather than extending
			the Swagger schema with x-handler attributes.
			However, doing so would impose additional structure on the API,
			limiting the generality of Swagger and this class.
			"""
			if 'x-handler' in pathdef:
				handler_name = pathdef['x-handler']
				methods = [ method.upper() for method in self.swagger_methods if method.lower() in pathdef ]
				super(SwaggerMapper, self).connect(handler_name, base_path + path, controller=handler_name, conditions=dict(method=methods))
			else:
				raise ValueError("No x-handler attribute for path '%s'" % path)

class SwaggerFilter(RoutesMiddleware):
	def __init__(self, app, mapper):
		self.app = app;
		super(SwaggerFilter, self).__init__(app, mapper)
	def __call__(self, environ, start_response):
		return self.app(environ, start_response)

def factory(config, **settings):
	config.update(settings);
	swagger_file = config.get("swagger_json", "swagger.json");
	spec = json.loads(open(swagger_file).read())
	mapper = SwaggerMapper(spec)
	def filter(app):
		return SwaggerFilter(app, mapper)
	return filter

if __name__ == '__main__':
	spec = json.loads(open('swagger.json').read())
	mapper = SwaggerMapper(spec)
	print mapper
