from . import utils
from .utils import cbc

from requests.auth import HTTPBasicAuth
from urllib.parse import urljoin

__all__ = [
    # constants
    'SCRIPT_KIND', 'EXPLICIT_KIND', 'IMPLICIT_KIND', 'APPLICATION_INSTALLED_KIND',
    'APPLICATION_EXPLICIT_KIND', 'ALL_SCOPES',
    # Classes
    'OAuth', 'Authorization'
]

SCRIPT_KIND = "script"
EXPLICIT_KIND = "explicit"
IMPLICIT_KIND = "implicit"
APPLICATION_INSTALLED_KIND = "application/installed"
APPLICATION_EXPLICIT_KIND = "application/explicit"

ALL_KINDS = (SCRIPT_KIND, EXPLICIT_KIND, IMPLICIT_KIND,
             APPLICATION_EXPLICIT_KIND, APPLICATION_INSTALLED_KIND)
ALL_SCOPES = ()

REVERSE_KINDS = {
    SCRIPT_KIND: "SCRIPT_KIND",
    EXPLICIT_KIND: "EXPLICIT_KIND",
    IMPLICIT_KIND: "IMPLICIT_KIND",
    APPLICATION_INSTALLED_KIND: "APPLICATION_INSTALLED_KIND",
    APPLICATION_EXPLICIT_KIND: "APPLICATION_EXPLICIT_KIND"
}

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
    """Class representing a set of OAuth credentials.  May be authorized.

    This class is used to represent a complete set of credentials to log in to Reddit's
    OAuth API using one of the script, explicit, implicit, or application authentication
    forms.  An object of this kind can be passed to the :class:`~snooble.Snooble`
    intializer, or via the :meth:`~snooble.Snooble.oauth` method.  An OAuth object may
    also be returned by the :meth:`~snooble.Snooble.oauth` method.

    .. seealso::
        :meth:`~snooble.oauth.OAuth.__init__`:
            All arguments passed in to this class will also be available as
            attributes to read and modify.
    """

    def __init__(self, kind, scopes, **kwargs):
        """Intialise the object with the correct keyword arguments.

        Arguments:
            kind (str): This should be one of the five kind strings.  These are all
                available as constants in this module - use these constants!  If this
                kind is wrong, initialisation will fail with a ValueError
            scopes (list[str]): A list of all of the requested scopes from the API.  For
                your convenience, the constant `ALL_SCOPES` is made available in this
                module, which will provide the correct scopes for all possible API
                requests.
            client_id (str): Always needed.  Client ID as provided on the apps
                preferences page.
            secret_id (str): Needed for script kind, explicit kind, and
                application/explicit kind.  As provided on the apps preferences page.
            username/password (str): Only needed for script kind.  Username and password
                of the user to log in to.
            redirect_uri (str): Needed for explicit and implicit kinds.  When the user
                has authenticated with Reddit, they will be sent to this uri.  *Must* be
                the same as provided on the apps preferences page.
            mobile (bool): If ``True``, for explicit and implicit kinds, this will cause
                any generated authentication links to use Reddit's mobile-friendly page.
                Defaults to ``False``.
            duration (str): One of ``'temporary'`` or ``'permanent'``.  Only applicable
                for explicit authentication kinds.  Defaults to ``'temporary'``.
            device_id (str): A unique string to identify a user, used to help Reddit
                track unique users and improve their analytics.  If the user does not
                want to be tracked, use ``'DO_NOT_TRACK_THIS_USER'``.  Defaults to
                ``'DO_NOT_TRACK_THIS_USER'``.
        """
        if kind not in ALL_KINDS:
            raise ValueError("Invalid oauth kind {kind}".format(kind=kind))

        self.kind = kind
        self.scopes = scopes

        self.mobile = kwargs.pop('mobile', False)
        self.duration = kwargs.pop('duration', 'temporary')
        self.device_id = kwargs.pop('device_id', 'DO_NOT_TRACK_THIS_USER')
        utils.assign_parameters(self, kwargs, KIND_PARAMETER_MAPPING[self.kind])

        self.authorization = None
        """The details of this account's authorization request, or ``None``.

        Will be ``None`` by default.  If an authorization request has been successfully
        completed, the :class:`~snooble.Snooble` class will set this to the
        corresponding :class:`~snooble.oauth.Authorization` object.
        """

    def __repr__(self):
        cls = self.__class__.__name__
        kind = REVERSE_KINDS.get(self.kind)
        args = ((k, v) for k, v in self.__dict__.items() if k != 'kind')
        args = ", ".join("{k}={v!r}".format(k=k, v=v) for k, v in args)
        return '{cls}({kind}, {args})'.format(cls=cls, kind=kind, args=args)

    @property
    def authorized(self):
        """True if this instance has an authorization property.

        Does not fully check the validity of the authorization property,
        only that it exists.
        """
        return self.authorization is not None


class Authorization(object):
    """A class containing the details of a successful authorization attempt.

    Contains the :attr:`~.token_type`, and the :attr:`~.token`.  It also stores the time
    the token was :attr:`~.recieved`, and the :attr:`~.length` that this token will last.
    Note that these last two attributes are not currently used by Snooble, but may be
    useful in future, or to users.
    """

    def __init__(self, token_type, token, recieved, length):
        self.token_type = token_type
        "*(str)* Should always be the string ``'bearer'``."
        self.token = token
        "*(str)* A Reddit session token."
        self.recieved = recieved
        "*(int)* When the token was recieved in seconds since the epoch.  (Always UTC)."
        self.length = length
        "*(int)* The length of time the token will last in seconds."

    def __repr__(self):
        cls = self.__class__.__name__
        args = ("{k}={v}".format(k=k, v=v) for k, v in self.__dict__.items())
        return "{cls}({args})".format(cls=cls, args=", ".join(args))

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
