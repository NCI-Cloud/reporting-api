from webob import Response
import webob.exc
from common.apiversion import APIVersion
from common.application import Application
from app.apiv1 import APIv1App

class VersionsApp(Application):

	def APIVersionList(self, args):
		return Response(status = 300, content_type = 'application/json', body = self._resultset_to_json([
			version._api_version_detail() for version in APIVersion.version_classes
		]))

	def APIVersionDetails(self, version_identifier):
		versions = [ version for version in APIVersion.version_classes if version._version_identifier() == version_identifier ]
		if not versions:
			return webob.exc.HTTPNotFound()
		if len(versions) > 1:
			raise RuntimeError("Multiple API versions with identifier '%s'" % version_identifier)
		return Response(content_type = 'application/json', body = self._resultset_to_json(
			versions[0]._api_version_detail()
		))

def factory(global_config, **settings):
	return VersionsApp()
