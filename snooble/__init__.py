import collections
import urllib
import time

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

    def __init__(self, useragent, bursty=False, ratelimit=(60, 60),
                 auth_domain=AUTH_DOMAIN, www_domain=WWW_DOMAIN):
        self.useragent = useragent
        self.auth_domain, self.www_domain = auth_domain, www_domain

        self._limiter = ratelimit if isinstance(ratelimit, RateLimiter) else \
                        RateLimiter(*ratelimit, bursty=bursty)

        self._session = requests.Session()
        self._session.headers.update({"User-Agent": useragent})
        self._limited_session = self._limiter.limitate(self._session, ['get', 'post'])

        self._authorized = False
        self.authorization = None

    def oauth(self, auth=None, *args, **kwargs):
        if not isinstance(auth, oauth.OAuth):
            auth = oauth.OAuth(auth, *args, **kwargs)

        self._authorized = False

        if auth.kind == oauth.SCRIPT_KIND:
            client_auth = requests.auth.HTTPBasicAuth(auth.client_id, auth.secret_id)
            post_data = {"scope": ",".join(auth.scopes), "grant_type": "password",
                "username": auth.username, "password": auth.password}
            url = urllib.parse.urljoin(self.domain.www, 'api/v1/access_token')
            response = self._limited_session.post(url, auth=client_auth, data=post_data)

            if response.status_code != 200:
                if response.status_code == 401:
                    m = "Authorization failed (are all your details correct)"
                    raise errors.RedditError(m, response=response)
                else:
                    m = "Unknown authorization error"
                    raise errors.RedditError(m, response=response)

            r = response.json()

            self.authorization = \
                oauth.Authorization(token_type=r['token_type'], recieved=time.time(),
                                    token=r['access_token'], length=r['expires_in'])

            self._authorized = True

        elif auth.kind == oauth.EXPLICIT_KIND:
            pass

    def get(self, url):
        if not self._authorized:
            raise errors.SnoobleError("Snooble.auth must be called before making requests")
