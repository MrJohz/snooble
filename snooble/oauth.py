from . import utils
from .utils import cbc

from requests.auth import HTTPBasicAuth
from urllib.parse import urljoin

SCRIPT_KIND = "script"
EXPLICIT_KIND = "explicit"
IMPLICIT_KIND = "implicit"
APPLICATION_INSTALLED_KIND = "application/installed"
APPLICATION_EXPLICIT_KIND = "application/explicit"

ALL_KINDS = (SCRIPT_KIND, EXPLICIT_KIND, IMPLICIT_KIND,
             APPLICATION_EXPLICIT_KIND, APPLICATION_INSTALLED_KIND)
ALL_SCOPES = ()

# Different kinds of authentication require different parameters.  This is a mapping of
# kind to required parameter keys for use in OAuth's __init__ method.
KIND_PARAMETER_MAPPING = {
    SCRIPT_KIND: ('client_id', 'secret_id', 'username', 'password'),
    EXPLICIT_KIND: ('client_id', 'secret_id', 'redirect_uri'),
    APPLICATION_EXPLICIT_KIND: ('client_id', 'secret_id'),
    IMPLICIT_KIND: ('client_id', 'redirect_uri'),
    APPLICATION_INSTALLED_KIND: ('client_id',)
}


class OAuth(object):

    def __init__(self, kind, scopes, **kwargs):
        if kind not in ALL_KINDS:
            raise ValueError("Invalid oauth kind {kind}".format(kind=kind))

        self.kind = kind
        self.scopes = scopes
        self.authorization = None

        self.mobile = kwargs.pop('mobile', False)
        self.duration = kwargs.pop('duration', 'temporary')
        self.device_id = kwargs.pop('device_id', 'DO_NOT_TRACK_THIS_USER')

        utils.assign_parameters(self, kwargs, KIND_PARAMETER_MAPPING[self.kind])

    @property
    def authorized(self):
        return self.authorization is not None


class Authorization(object):

    def __init__(self, token_type, token, recieved, length):
        self.token_type = token_type
        self.token = token
        self.recieved = recieved
        self.length = length

    def __eq__(self, other):
        if type(self) == type(other):
            return self.__dict__ == other.__dict__
        return False


class AUTHORIZATION_METHODS(cbc.CallbackClass):

    @cbc.CallbackClass.key(SCRIPT_KIND)
    def authorize_script(snoo, auth, session, code):
        client_auth = HTTPBasicAuth(auth.client_id, auth.secret_id)
        post_data = {"scope": ",".join(auth.scopes), "grant_type": "password",
                     "username": auth.username, "password": auth.password}
        url = urljoin(snoo.domain.www, 'api/v1/access_token')

        return session.post(url, auth=client_auth, data=post_data)

    @cbc.CallbackClass.key(EXPLICIT_KIND)
    def authorize_explicit(snoo, auth, session, code):
        client_auth = HTTPBasicAuth(auth.client_id, auth.secret_id)
        post_data = {"grant_type": "authorization_code", "code": code,
                     "redirect_uri": auth.redirect_uri}
        url = urljoin(snoo.domain.www, 'api/v1/access_token')

        return session.post(url, auth=client_auth, data=post_data)

    @cbc.CallbackClass.key(IMPLICIT_KIND)
    def authorize_implicit(snoo, auth, session, code):
        return None

    @cbc.CallbackClass.key(APPLICATION_EXPLICIT_KIND)
    def authorize_application_explicit(snoo, auth, session, code):
        client_auth = HTTPBasicAuth(auth.client_id, auth.secret_id)
        post_data = {"grant_type": "client_credentials"}
        url = urljoin(snoo.domain.www, 'api/v1/access_token')

        return session.post(url, auth=client_auth, data=post_data)

    @cbc.CallbackClass.key(APPLICATION_INSTALLED_KIND)
    def authorize_application_implicit(snoo, auth, session, code):
        client_auth = HTTPBasicAuth(auth.client_id, '')
        post_data = {"grant_type": "https://oauth.reddit.com/grants/installed_client",
                     "device_id": auth.device_id}
        url = urljoin(snoo.domain.www, 'api/v1/access_token')

        return session.post(url, auth=client_auth, data=post_data)
