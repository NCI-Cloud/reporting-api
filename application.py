import json
from webob import Request, Response
import webob.dec
import webob.exc

class Application(object):

	@webob.dec.wsgify
	def __call__(self, req):
		return self.get_response()
