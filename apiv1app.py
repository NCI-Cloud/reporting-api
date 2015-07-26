import json
from webob import Response
from apiversion import APIVersion

class APIv1App(APIVersion):

	@classmethod
	def version_identifier(cls):
		return "v1";

	def get_response(self):
		return Response(content_type = 'application/json', body = json.dumps({ "todo": "API version 1" }))

def factory(global_config, **settings):
	return APIv1App()
