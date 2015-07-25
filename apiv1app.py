import json
from apiversion import APIVersion

class APIv1App(APIVersion):

	@staticmethod
	def version_identifier():
		return "v1";

	def respond(self):
		return { "todo": "API version 1" }

def factory(global_config, **settings):
	return APIv1App
