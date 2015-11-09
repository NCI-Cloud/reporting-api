"""
An Application which uses Keystone for authorisation using RBAC.
"""

import ConfigParser
import abc
from reporting_api.common.application import Application
from keystonemiddleware.auth_token import filter_factory as auth_filter_factory


# Pylint warns that the following class has too few public methods.
# It is not intended to have many (or even any) public methods,
# so this is not a problem, so the following comment silences the warning.
# Apparently, pylint assumes (falsely) that a class without public methods
# is being abused as a mere holder of data - but the below class is being
# used as a holder of code, as is common accepted practice in OOP.
# pylint: disable=R0903

class KeystoneApplication(Application):

    """
    An Application which uses Keystone for authorisation using RBAC.
    """

    __metaclass__ = abc.ABCMeta

    INI_SECTION = 'keystone_authtoken'

    def __init__(self, configuration):
        super(KeystoneApplication, self).__init__(configuration)
        self.required_role = self.config.get('authorisation', 'required_role')
        if self.required_role is None:
            raise ValueError("No required role supplied")

    def _check_auth(self, req):
        if not self.required_role:
            return True
        if 'HTTP_X_ROLES' in req.environ:
            user_roles = req.environ['HTTP_X_ROLES'].split(',')
            return self.required_role in user_roles
        return False


def keystone_auth_filter_factory(global_config, **local_config):
    """
    A factory function which produces Keystone authentication
    WSGI filters.
    """
    global_config.update(local_config)
    config_file_name = global_config.get('config_file')
    if not config_file_name:
        raise ValueError('No config_file directive')
    config_file = ConfigParser.SafeConfigParser()
    if not config_file.read(config_file_name):
        raise ValueError("Cannot read config file '%s'" % config_file_name)
    global_config.update(config_file.items(KeystoneApplication.INI_SECTION))
    return auth_filter_factory(global_config)
