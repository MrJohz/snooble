import collections
import urllib

import requests

from . import oauth
from .ratelimit import RateLimiter


OAUTH_DOMAIN = 'https://oauth.reddit.com'
WWW_DOMAIN = 'https://www.reddit.com'

Domain = collections.namedtuple('Domain', ['auth', 'www'])


class Snooble(object):

    @property
    def domain(self):
        return Domain(auth=self.oauth_domain, www=self.www_domain)

    def __init__(self, useragent, oauth=None, bursty=True, ratelimit=(60, 60),
                 oauth_domain=OAUTH_DOMAIN, www_domain=WWW_DOMAIN):
        self.useragent = useragent
        self._session = requests.Session()
        self._session.headers.update({"User-Agent": useragent})

        if isinstance(ratelimit, RateLimiter):
            self._ratelimiter = ratelimit
        else:
            self._ratelimiter = RateLimiter(*ratelimit, bursty=bursty)

        self.oauth_domain, self.www_domain = oauth_domain, www_domain

        self._limited_session = self._ratelimiter.limitate(self._session, ['get'])

        if oauth is not None:
            self.oauth(oauth)
        else:
            self._authorised = False

    def oauth(self, auth=None, **kwargs):
        if auth is None:
            auth = oauth.OAuth(**kwargs)

        self._authorised = False

        if auth.kind == oauth.SCRIPT_KIND:
            client_auth = requests.auth.HTTPBasicAuth(auth.client_id, auth.secret_id)
            post_data = { "grant_type": "password",
                "username": auth.username, "password": auth.password }
            url = urllib.parse.urljoin(self.domain.www, '/api/v1/access_token')
            response = self._limited_session.get(url, auth=client_auth, data=post_data)
