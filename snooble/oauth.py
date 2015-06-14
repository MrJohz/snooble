from . import utils

SCRIPT_TYPE = "script"
EXPLICIT_TYPE = "explicit"
IMPLICIT_TYPE = "implicit"
APPLICATION_IMPLICIT_TYPE = "application/implicit"
APPLICATION_EXPLICIT_TYPE = "application/explicit"


class OAuth(object):

    def __init__(self, type, scopes, **kwargs):
        self.type = type
        self.scopes = scopes

        if self.type == SCRIPT_TYPE:
            self.client_id = utils.fetch_parameter(kwargs, 'client_id')
            self.secret_id = utils.fetch_parameter(kwargs, 'secret_id')
            self.username = utils.fetch_parameter(kwargs, 'username')
            self.password = utils.fetch_parameter(kwargs, 'password')

        elif self.type == EXPLICIT_TYPE:
            self.client_id = utils.fetch_parameter(kwargs, 'client_id')
            self.secret_id = utils.fetch_parameter(kwargs, 'secret_id')
            self.redirect_uri = utils.fetch_parameter(kwargs, 'redirect_uri')
            self.mobile = kwargs.pop('mobile', False)
            self.duration = kwargs.pop('duration', 'temporary')

        elif self.type == APPLICATION_EXPLICIT_TYPE:
            self.client_id = utils.fetch_parameter(kwargs, 'client_id')
            self.secret_id = utils.fetch_parameter(kwargs, 'secret_id')

        elif self.type == IMPLICIT_TYPE:
            self.client_id = utils.fetch_parameter(kwargs, 'client_id')
            self.redirect_uri = utils.fetch_parameter(kwargs, 'redirect_uri')
            self.mobile = kwargs.pop('mobile', False)

        elif self.type == APPLICATION_IMPLICIT_TYPE:
            self.client_id = utils.fetch_parameter(kwargs, 'client_id')

        else:
            raise ValueError("Invalid oauth type {type}".format(type=self.type))
