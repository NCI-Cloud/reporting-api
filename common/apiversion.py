from abc import abstractmethod
import abc
from application import Application

class APIVersion(Application):

	version_classes = []

	@classmethod
	@abstractmethod
	def _version_identifier(cls): pass

	@classmethod
	def _get_links(cls):
		return []

	@classmethod
	def _api_version_detail(cls, req):
		links = cls._get_links()
		links.append(dict(
			href = "/" + cls._version_identifier(),
			rel = "self"
		))
		return dict(
			id = cls._version_identifier(),
			links = links
		)

	@classmethod
	def APIVersionDetails(cls, req, params):
		return ( cls._api_version_detail(req), None )
