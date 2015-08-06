#!/usr/bin/python

import json
from webob import Request, Response
import webob.exc
import webob.dec

class SwaggerMiddleware(object):

	# The Swagger specification v2.0 mandates use of only these methods
	swagger_methods = [ 'get', 'put', 'post', 'delete', 'options', 'head', 'patch' ]

	def _path_matches(self, pattern, url):
		# print "Testing: '%s' '%s'" % (url, pattern)
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

	def _find_path(self, environ, spec):
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
				print "Rejected path:"
				print path
			"""
		return [ None, None ]

	def _find_operation(self, pathdef, environ):
		method = environ['REQUEST_METHOD'].lower()
		if method in pathdef:
			return pathdef[method]

	def _options_response(self, pathdef, parameters, environ, start_response):
		if pathdef:
			methods = [ method.upper() for method in self.swagger_methods if method in pathdef ]
		else:
			methods = []
		# Synthesise an OPTIONS method
		methods.append('OPTIONS')
		headers = []
		headers.append(('Allow', ','.join(methods)))
		start_response('200 OK', headers)
		if pathdef:
			return json.dumps(pathdef)
		return json.dumps(dict())

	def __init__(self, application, specs, cfg=None, **kw):
		self.specs = specs
		self.application = application

	def __call__(self, environ, start_response):
		# print "PATH_INFO: " + environ['PATH_INFO']
		# print "SCRIPT_NAME: " + environ['SCRIPT_NAME']
		# print self.specs
		for spec in self.specs:
			"""
			if ('SCRIPT_NAME' in environ) and ('basePath' in spec):
				if not environ['SCRIPT_NAME'].startswith(spec['basePath']):
					return webob.exc.HTTPNotFound()
			"""
			data = dict()
			[ pathdef, path_parameters ] = self._find_path(environ, spec)
			# Handle OPTIONS requests ourselves, since we know the methods allowed
			if "options" == environ['REQUEST_METHOD'].lower():
				return self._options_response(pathdef, path_parameters, environ, start_response)
			if pathdef:
				data['path'] = pathdef
				data['parameters'] = path_parameters
				oper = self._find_operation(pathdef, environ)
				if oper:
					data['operation'] = oper
				environ['swagger'] = data
				return self.application(environ, start_response)
		return self.application(environ, start_response)

def factory(config, **settings):
	def filter(app):
		config.update(settings)
		swagger_files = config.get('swagger_json', 'swagger.json');
		specs = [ json.loads(open(file).read()) for file in swagger_files.split() ]
		return SwaggerMiddleware(app, specs)
	return filter

if __name__ == '__main__':
	middleware = SwaggerMiddleware(HelloApp())
	print middleware
