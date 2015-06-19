import collections
import time
from urllib import parse as urlp

import requests

from . import oauth, errors
from .ratelimit import RateLimiter


AUTH_DOMAIN = 'https://oauth.reddit.com/'
WWW_DOMAIN = 'https://www.reddit.com/'

Domain = collections.namedtuple('Domain', ['auth', 'www'])


class Snooble(object):

    @property
    def domain(self):
        return Domain(auth=self.auth_domain, www=self.www_domain)

    @domain.setter
    def domain(self, tup):
        self.www_domain, self.auth_domain = tup

    @property
    def authorized(self):
        return self._auth is not None and self._auth.authorized

    def __init__(self, useragent, bursty=False, ratelimit=(60, 60),
                 www_domain=WWW_DOMAIN, auth_domain=AUTH_DOMAIN, auth=None):
        self.useragent = useragent
        self.www_domain, self.auth_domain = www_domain, auth_domain

        if isinstance(ratelimit, RateLimiter):
            self._limiter = ratelimit
        else:
            self._limiter = RateLimiter(*ratelimit, bursty=bursty)

        self._session = requests.Session()
        self._session.headers.update({"User-Agent": useragent})
        self._limited_session = self._limiter.limitate(self._session, ['get', 'post'])
        self._auth = None
        if auth is not None:
            self.oauth(auth)

    def oauth(self, auth=None, *args, **kwargs):
        if auth is None and not len(args) and not len(kwargs):
            return self._auth
        elif not isinstance(auth, oauth.OAuth):
            auth = oauth.OAuth(auth, *args, **kwargs)

        old_auth, self._auth = self._auth, auth
        return old_auth

    def auth_url(self, state):
        if self._auth is None:
            raise ValueError("Cannot create auth url witout credentials")
        if self._auth.kind not in (oauth.EXPLICIT_KIND, oauth.IMPLICIT_KIND):
            raise ValueError("Selected auth kind does not use authorization URL")

        response_type = 'code' if self._auth.kind == oauth.EXPLICIT_KIND else 'token'

        options = {
            "client_id": self._auth.client_id,
            "response_type": response_type,
            "state": state,
            "redirect_uri": self._auth.redirect_uri,
            "scope": ",".join(self._auth.scopes)
        }

        if self._auth.kind == oauth.EXPLICIT_KIND:
            options['duration'] = self._auth.duration

        base = urlp.urljoin(self.domain.www, 'api/v1/authorize')
        if self._auth.mobile:
            base += ".compact"
        base += "?" + "&".join("{k}={v}".format(k=k, v=urlp.quote_plus(v))
                               for (k, v) in options.items())
        return base

    def authorize(self, code=None, expires=3600):
        if self._auth is None:
            raise ValueError("Attempting authorization without credentials")

        auth = self._auth

        if auth.kind == oauth.SCRIPT_KIND:
            client_auth = requests.auth.HTTPBasicAuth(auth.client_id, auth.secret_id)
            post_data = {"scope": ",".join(auth.scopes), "grant_type": "password",
                         "username": auth.username, "password": auth.password}
            url = urlp.urljoin(self.domain.www, 'api/v1/access_token')
            response = self._limited_session.post(url, auth=client_auth, data=post_data)

            if response.status_code != 200:
                m = "Authorization failed (are all your details correct?)"
                raise errors.RedditError(m, response=response)

            r = response.json()

            auth.authorization = \
                oauth.Authorization(token_type=r['token_type'], recieved=time.time(),
                                    token=r['access_token'], length=r['expires_in'])

            self._authorized = True

        elif auth.kind == oauth.EXPLICIT_KIND:
            client_auth = requests.auth.HTTPBasicAuth(auth.client_id, auth.secret_id)
            post_data = {"grant_type": "authorization_code",
                         "code": code, "redirect_uri": auth.redirect_uri}
            url = urlp.urljoin(self.domain.www, 'api/v1/access_token')
            response = self._limited_session.post(url, auth=client_auth, data=post_data)

            if response.status_code != 200:
                m = "Authorization failed (are all your details correct?)"
                raise errors.RedditError(m, response=response)

            r = response.json()

            auth.authorization = \
                oauth.Authorization(token_type=r['token_type'], recieved=time.time(),
                                    token=r['access_token'], length=r['expires_in'])

        elif auth.kind == oauth.IMPLICIT_KIND:
            auth.authorization = \
                oauth.Authorization(token_type='bearer', recieved=time.time(),
                                    token=code, length=expires)

        elif auth.kind == oauth.APPLICATION_EXPLICIT_KIND:
            client_auth = requests.auth.HTTPBasicAuth(auth.client_id, auth.secret_id)
            post_data = {"grant_type": "client_credentials"}
            url = urlp.urljoin(self.domain.www, 'api/v1/access_token')
            response = self._limited_session.post(url, auth=client_auth, data=post_data)

            if response.status_code != 200:
                m = "Authorization failed (are all your details correct?)"
                raise errors.RedditError(m, response=response)

            r = response.json()

            auth.authorization = \
                oauth.Authorization(token_type=r['token_type'], recieved=time.time(),
                                    token=r['access_token'], length=r['expires_in'])

        elif auth.kind == oauth.APPLICATION_INSTALLED_KIND:
            client_auth = requests.auth.HTTPBasicAuth(auth.client_id, "")
            post_data = {"grant_type": "https://oauth.reddit.com/grants/installed_client",
                         "device_id": auth.device_id}
            url = urlp.urljoin(self.domain.www, 'api/v1/access_token')
            response = self._limited_session.post(url, auth=client_auth, data=post_data)

            if response.status_code != 200:
                m = "Authorization failed (are all your details correct?)"
                raise errors.RedditError(m, response=response)

            r = response.json()

            auth.authorization = \
                oauth.Authorization(token_type=r['token_type'], recieved=time.time(),
                                    token=r['access_token'], length=r['expires_in'])

        else:
            raise ValueError("Unrecognised auth kind {kind}".format(kind=auth.kind))

    def get(self, url):
        if not self.authorized:
            raise ValueError("Snooble.auth must be called before making requests")
