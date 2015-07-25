from abc import abstractmethod
from application import Application

class APIVersion(Application):

	@abstractmethod
	def version_identifier(self): pass
