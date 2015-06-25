import collections
import time
from urllib import parse as urlp

import requests

from . import oauth, errors, responses
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
                 www_domain=WWW_DOMAIN, auth_domain=AUTH_DOMAIN, auth=None,
                 encode_all=False):
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
        elif self._auth.kind not in oauth.ALL_KINDS:
            raise ValueError("Unrecognised auth kind {k}".format(k=self._auth.kind))

        create_auth_request = oauth.AUTHORIZATION_METHODS[self._auth.kind]
        response = create_auth_request(self, self._auth, self._limited_session, code)

        if response is None and self._auth.kind == oauth.IMPLICIT_KIND:
            # implicit kind does not send confirmation request, it has already been
            # given the correct token, just use that.
            self._auth.authorization = \
                oauth.Authorization(token_type='bearer', recieved=time.time(),
                                    token=code, length=expires)
        elif response.status_code != 200:
            m = "Authorization failed (are all your details correct?)"
            raise errors.RedditError(m, response=response)
        elif 'error' in response.json():
            m = "Authorization failed due to error: {error!r}"
            error = response.json()['error']
            raise errors.RedditError(m.format(error=error), response=response)
        else:
            r = response.json()
            self._auth.authorization = \
                oauth.Authorization(token_type=r['token_type'], recieved=time.time(),
                                    token=r['access_token'], length=r['expires_in'])

    def get(self, url, **kwargs):
        if not self.authorized:
            raise ValueError("Snooble.authorize must be called before making requests")

        else:
            headers = {"Authorization": " ".join((self._auth.authorization.token_type,
                                                  self._auth.authorization.token))}
            url = urlp.urljoin(self.domain.auth, url)
            response = self._limited_session.get(url, headers=headers, params=kwargs)
            return responses.create_response(response.json())
