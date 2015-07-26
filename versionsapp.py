import json
from apiversion import APIVersion
from application import Application
from apiv1app import APIv1App

class VersionsApp(Application):

	version_classes = [ APIv1App ]

	def respond(self):
		return [
			{
				"id": version.version_identifier(),
				"links": [
					{
						"href": "/" + version.version_identifier(),
						"rel": "self"
					}
				]
			} for version in self.version_classes
		]

def factory(global_config, **settings):
	return VersionsApp
