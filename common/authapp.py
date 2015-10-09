from common.application import Application

class KeystoneApplication(Application):

    """
    An Application which uses Keystone for authorisation using RBAC
    """

    def _check_auth(self, req):
        required_role = self.config.get('authorisation', 'required_role')
        if required_role is None:
            raise ValueError("No required role supplied")
        user_roles = req.env['HTTP_X_ROLES'].split(',')
        return required_role in user_roles
