import requests

from .oauth import OAuth
from .ratelimit import RateLimiter, ratelimited


class Snooble(object):

    def __init__(self, useragent, ratelimit=(60, 60), oauth=None):
        self.useragent = useragent
        self._session = requests.Session()
        self._session.headers.update({"User-Agent": useragent})

        self._ratelimiter = RateLimiter(*ratelimit)

        if oauth is not None:
            self.oauth(oauth)

    def oauth(self, oauth=None, **kwargs):
        if oauth is None:
            self.oauth(OAuth(**kwargs))

        self._oauth_details = oauth
