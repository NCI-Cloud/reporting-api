#!/usr/bin/python

import json
from webob import Request, Response
import webob.exc
import webob.dec
from common.application import Application
from saml2.schema.soap import Operation

class SwaggerMiddleware(object):

	"""
	A WSGI URL router middleware that automatically configures itself
	using a set of Swagger JSON API specifications.
	"""

	# The Swagger specification v2.0 mandates use of only these methods
	swagger_methods = [ 'get', 'put', 'post', 'delete', 'options', 'head', 'patch' ]

	def _path_matches(self, pattern, url):
		# print "Testing URL '%s' against pattern '%s'" % (url, pattern)
		path_parameters = dict()
		pattern_components = pattern.split('/')
		url_components = url.split('/')
		patt_len = len(pattern_components)
		url_len = len(url_components)
		for i in range(0, min(patt_len, url_len)):
			patt_comp = pattern_components[i]
			url_comp = url_components[i]
			if patt_comp.startswith('{') and patt_comp.endswith('}') and url_comp:
				# Pattern component matched
				path_parameters[patt_comp[1:-1]] = url_comp
			elif patt_comp != url_comp:
				return [ False, [] ] # Literal component mismatch
		i += 1
		for comp in pattern_components[i:patt_len]:
			if comp:
				return [ False, [] ] # Trailing unmatched non-empty path pattern component
		for comp in url_components[i:url_len]:
			if comp:
				return [ False, [] ] # Trailing unmatched non-empty URL component
		# print "Match: '%s' '%s'" % (url, pattern)
		return [ True, path_parameters ]

	def _find_path_spec(self, environ, spec):
		if 'basePath' in spec:
			base_path = spec['basePath']
		else:
			base_path = ''
		for path, pathdef in spec['paths'].items():
			# print "BasePath: '%s'" % base_path
			url = environ['SCRIPT_NAME'] + environ['PATH_INFO']
			[ matched, parameters ] = self._path_matches(base_path + path, url)
			if matched:
				return [ pathdef, parameters ]
			"""
			else:
				print "Rejected URL '%s'" % url
			"""
		return [ None, None ]

	def _find_operation(self, pathdef, environ):
		method = environ['REQUEST_METHOD'].lower()
		if method in pathdef:
			return pathdef[method]
		elif method == 'options' and 'get' in pathdef:
			return pathdef['get']
		return None

	"""
	Respond to OPTIONS requests meaningfully,
	implementing HATEOAS using the information in the Swagger catalogs.
	"""
	def _options_response(self, environ, start_response):
		swagger = environ['swagger']
		pathdef = swagger['path']
		operation = swagger['operation']
		if pathdef is None:
			methods = []
		else:
			methods = [ method.upper() for method in self.swagger_methods if method != 'options' and method in pathdef ]
		# Synthesise an OPTIONS method
		methods.append('OPTIONS')
		headers = []
		headers.append(('Allow', ','.join(methods)))
		start_response('200 OK', headers)
		if operation is not None:
			result = operation
		elif pathdef is not None:
			result = pathdef
		else:
			result = dict()
		return Application._resultset_to_json(result)

	def __init__(self, application, specs, cfg=None, **kw):
		self.specs = specs
		self.application = application

	def _find_path(self, environ):
		if 'swagger' in environ:
			swagger = environ['swagger']
		else:
			swagger = environ['swagger'] = dict()
		if 'path' in swagger:
			pathdef = swagger['path']
		else:
			for spec in self.specs:
				[ pathdef, path_parameters ] = self._find_path_spec(environ, spec)
				if pathdef is not None:
					swagger['path'] = pathdef
					swagger['parameters'] = path_parameters
					swagger['operation'] = self._find_operation(pathdef, environ)
					if swagger['operation'] is not None:
						break
		if not('path' in swagger):
			swagger['path'] = None
		if not('parameters' in swagger):
			swagger['parameters'] = None
		if not('operation' in swagger):
			swagger['operation'] = None

	def __call__(self, environ, start_response):
		# print "PATH_INFO: " + environ['PATH_INFO']
		# print "SCRIPT_NAME: " + environ['SCRIPT_NAME']
		# print self.specs
		self._find_path(environ)
		if "options" == environ['REQUEST_METHOD'].lower():
			# Intercept this request to return an OPTIONS response
			return self._options_response(environ, start_response)
		return self.application(environ, start_response)

def factory(config, **settings):
	def filter(app):
		config.update(settings)
		swagger_files = config.get('swagger_json', 'swagger.json');
		specs = [ json.loads(open(filename).read()) for filename in swagger_files.split() ]
		return SwaggerMiddleware(app, specs)
	return filter

if __name__ == '__main__':
	app = HelloApp()
	middleware = SwaggerMiddleware(app)
	print middleware
