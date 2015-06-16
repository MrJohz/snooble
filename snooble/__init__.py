import collections
import urllib

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

        self._ratelimiter = ratelimit if isinstance(ratelimit, RateLimiter) else \
                            RateLimiter(*ratelimit, bursty=bursty)

        self._session = requests.Session()
        self._session.headers.update({"User-Agent": useragent})
        self._limited_session = self._ratelimiter.limitate(self._session, ['get'])

        self._authorized = False

    def oauth(self, auth=None, **kwargs):
        if auth is None:
            auth = oauth.OAuth(**kwargs)

        self._authorized = False

        if auth.kind == oauth.SCRIPT_KIND:
            client_auth = requests.auth.HTTPBasicAuth(auth.client_id, auth.secret_id)
            post_data = {"grant_type": "password",
                "username": auth.username, "password": auth.password}
            url = urllib.parse.urljoin(self.domain.www, 'api/v1/access_token')
            response = self._limited_session.get(url, auth=client_auth, data=post_data)

    def get(self, url):
        if not self._authorized:
            raise errors.SnoobleError("Snooble.auth must be called before making requests")
