from webob import Response
import webob.exc
from apiversion import APIVersion
from application import Application
from app.apiv1 import APIv1App

class VersionsApp(Application):

	version_classes = [ APIv1App ]

	def _api_version_detail(self, version):
		return {
			"id": version._version_identifier(),
			"links": [
				{
					"href": "/" + version._version_identifier(),
					"rel": "self"
				}
			]
		}

	def APIVersionList(self, args):
		return Response(status = 300, content_type = 'application/json', body = self._resultset_to_json([
			self._api_version_detail(version) for version in self.version_classes
		]))

	def APIVersion(self, version_identifier):
		versions = [ version for version in self.version_classes if version._version_identifier() == version_identifier ]
		if not versions:
			return webob.exc.HTTPNotFound()
		if len(versions) > 1:
			raise RuntimeError("Multiple API versions with identifier '%s'" % version_identifier)
		return Response(content_type = 'application/json', body = self._resultset_to_json({
			self._api_version_detail(versions[0])
		}))

def factory(global_config, **settings):
	return VersionsApp()
