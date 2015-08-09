from abc import abstractmethod
import abc
from application import Application
from webob import Response
import webob.exc
import webob.dec

class APIVersion(Application):

	version_classes = []

	@abstractmethod
	def _version_identifier(cls): pass

	@classmethod
	def _api_version_detail(cls):
		return dict(
			id = cls._version_identifier(),
			links = [
				dict(
					href = "/" + cls._version_identifier(),
					rel = "self"
				)
			]
		)

	@classmethod
	def APIVersionDetails(cls, params):
		return Response(content_type = 'application/json', body = cls._resultset_to_json(
			cls._api_version_detail()
		))

	@classmethod
	def APIVersionList(cls, args):
		return Response(status = 300, content_type = 'application/json', body = cls._resultset_to_json(
			[ version._api_version_detail() for version in APIVersion.version_classes ]
		))
