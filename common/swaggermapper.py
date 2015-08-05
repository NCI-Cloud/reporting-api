#!/usr/bin/python

import json
from routes.middleware import RoutesMiddleware
from routes import Mapper

class SwaggerMapper(Mapper):
	"""
	A WSGI URL router middleware that automatically configures itself
	using a Swagger JSON API specification.
	"""

	# The Swagger specification v2.0 mandates use of only these methods
	swagger_methods = [ 'get', 'put', 'post', 'delete', 'options', 'head', 'patch' ]

	def __init__(self, swagger_spec):
		super(SwaggerMapper, self).__init__();
		"""
		To debug this Mapper:
		logging.basicConfig()
		logger = logging.getLogger('routes.middleware')
		logger.setLevel(logging.DEBUG)
		"""
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
			methods = [ method for method in self.swagger_methods if method in pathdef ]
			for method in methods:
				if 'operationId' in pathdef[method]:
					handler_name = pathdef[method]['operationId']
					for suffix in [ '', '/' ]:
						super(SwaggerMapper, self).connect(handler_name, base_path + path + suffix, method=handler_name, conditions=dict(method=method.upper()))
				else:
					raise ValueError("No operationId attribute for method '%s' in path '%s'" % (method, path))
		self.redirect('', '/');

	def routematch(self, url = None, environ = None):
		"""Work around a crash in routes.mapper if url is empty"""
		if url is '':
			result = self._match('', environ);
			return result[0], result[1]
		return super(SwaggerMapper, self).routematch(url, environ)

def factory(config, **settings):
	def filter(app):
		config.update(settings);
		swagger_file = config.get('swagger_json', 'swagger.json');
		spec = json.loads(open(swagger_file).read())
		mapper = SwaggerMapper(spec)
		return RoutesMiddleware(app, mapper)
	return filter

if __name__ == '__main__':
	spec = json.loads(open('swagger.json').read())
	mapper = SwaggerMapper(spec)
	print mapper
