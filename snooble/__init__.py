import requests

from .oauth import OAuth
from .ratelimit import RateLimiter


class Snooble(object):

    def __init__(self, useragent, oauth=None, bursty=True, ratelimit=(60, 60)):
        self.useragent = useragent
        self._session = requests.Session()
        self._session.headers.update({"User-Agent": useragent})

        if isinstance(ratelimit, RateLimiter):
            self._ratelimiter = ratelimit
        else:
            self._ratelimiter = RateLimiter(*ratelimit, bursty=bursty)

        self._limited_session = self._ratelimiter.limitate(self._session)

        if oauth is not None:
            self.oauth(oauth)

    def oauth(self, oauth=None, **kwargs):
        if oauth is None:
            self.oauth(OAuth(**kwargs))

        self._oauth_details = oauth
