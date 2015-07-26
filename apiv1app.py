import json
from apiversion import APIVersion

class APIv1App(APIVersion):

	@classmethod
	def version_identifier(cls):
		return "v1";

	def respond(self):
		return { "todo": "API version 1" }

def factory(global_config, **settings):
	return APIv1App
