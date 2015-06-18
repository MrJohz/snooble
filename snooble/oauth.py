from . import utils

SCRIPT_KIND = "script"
EXPLICIT_KIND = "explicit"
IMPLICIT_KIND = "implicit"
APPLICATION_INSTALLED_KIND = "application/installed"
APPLICATION_EXPLICIT_KIND = "application/explicit"


class OAuth(object):

    def __init__(self, kind, scopes, **kwargs):
        self.kind = kind
        self.scopes = scopes
        self.authorization = None

        if self.kind == SCRIPT_KIND:
            self.client_id = utils.fetch_parameter(kwargs, 'client_id')
            self.secret_id = utils.fetch_parameter(kwargs, 'secret_id')
            self.username = utils.fetch_parameter(kwargs, 'username')
            self.password = utils.fetch_parameter(kwargs, 'password')

        elif self.kind == EXPLICIT_KIND:
            self.client_id = utils.fetch_parameter(kwargs, 'client_id')
            self.secret_id = utils.fetch_parameter(kwargs, 'secret_id')
            self.redirect_uri = utils.fetch_parameter(kwargs, 'redirect_uri')
            self.mobile = kwargs.pop('mobile', False)
            self.duration = kwargs.pop('duration', 'temporary')

        elif self.kind == APPLICATION_EXPLICIT_KIND:
            self.client_id = utils.fetch_parameter(kwargs, 'client_id')
            self.secret_id = utils.fetch_parameter(kwargs, 'secret_id')

        elif self.kind == IMPLICIT_KIND:
            self.client_id = utils.fetch_parameter(kwargs, 'client_id')
            self.redirect_uri = utils.fetch_parameter(kwargs, 'redirect_uri')
            self.mobile = kwargs.pop('mobile', False)

        elif self.kind == APPLICATION_INSTALLED_KIND:
            self.client_id = utils.fetch_parameter(kwargs, 'client_id')

        else:
            raise ValueError("Invalid oauth kind {kind}".format(kind=self.kind))

    @property
    def authorized(self):
        return self.authorization is not None


class Authorization(object):

    __slots__ = ['token_type', 'token', 'recieved', 'length']

    def __init__(self, token_type, token, recieved, length):
        self.token_type = token_type
        self.token = token
        self.recieved = recieved
        self.length = length

    def __eq__(self, other):
        if type(self) == type(other):
            for elem in self.__slots__:
                if getattr(self, elem) != getattr(other, elem):
                    return False
            else:
                return True
        return False
