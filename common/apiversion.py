from abc import abstractmethod
from application import Application

class APIVersion(Application):

	@abstractmethod
	def _version_identifier(cls): pass
