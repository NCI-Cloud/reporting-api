# An Application which uses Keystone for authentication and authorisation
class KeystoneApplication(object):
    def _check_auth(self, req):
        keystone_protocol = self.config.get('keystone_protocol')
        keystone_hostname = self.config.get('keystone_hostname')
        keystone_port = self.config.get('keystone_port')
        return True
