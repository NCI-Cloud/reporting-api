import json
from webob import Response
from apiversion import APIVersion
from application import Application
from apiv1app import APIv1App

class VersionsApp(Application):

	version_classes = [ APIv1App ]

	def get_response(self):
		return Response(content_type = 'application/json', body = json.dumps([
			{
				"id": version.version_identifier(),
				"links": [
					{
						"href": "/" + version.version_identifier(),
						"rel": "self"
					}
				]
			} for version in self.version_classes
		]))

def factory(global_config, **settings):
	return VersionsApp()
